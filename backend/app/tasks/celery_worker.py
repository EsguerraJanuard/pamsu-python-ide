import logging
import os

from celery import Celery

from app.core.redis_tls import redis_tls_options

logger = logging.getLogger(__name__)

# Same default as app.core.redis_client / redis_async. docker-compose and
# render.yaml always set REDIS_URL explicitly; the old "redis" hostname
# default only resolved inside docker-compose, so local API processes
# published to a host that does not exist.
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Remove any leftover query params if they were added in Render
if "?" in redis_url:
    redis_url = redis_url.split("?")[0]

# Verified TLS for rediss:// (see app.core.redis_tls).
ssl_conf = redis_tls_options(redis_url)

celery = Celery(
    __name__,
    broker=redis_url,
    backend=redis_url,
    broker_use_ssl=ssl_conf,
    redis_backend_use_ssl=ssl_conf
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # No caller reads task results (no AsyncResult.get()). Tracking them made
    # every .delay() subscribe to the Redis result backend, which retries 20
    # times when Redis is down and blocked the HTTP request for ~70 s.
    task_ignore_result=True,
    # Bound how long the API waits to enqueue when the broker is unreachable,
    # so routes fail fast instead of hanging.
    broker_connection_timeout=2.0,
    redis_socket_connect_timeout=2.0,
    task_publish_retry_policy={
        "max_retries": 1,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.2,
    },
)

@celery.task(bind=True, max_retries=3)
def dispatch_to_partner(self, execution_request_id: str) -> None:
    import httpx
    from app.core.database import SessionLocal
    from app.models.domain_models import ExecutionRequest
    
    judge0_url = os.getenv("JUDGE0_API_URL", "http://mock_judge0:8001")
    if judge0_url and not judge0_url.startswith("http"):
        judge0_url = f"https://{judge0_url}"
    judge0_key = os.getenv("JUDGE0_API_KEY")
    judge0_host = os.getenv("JUDGE0_HOST")
    webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://backend:8000")
    
    db = SessionLocal()
    try:
        # Retrieve the execution request
        request_record = (
            db.query(ExecutionRequest)
            .filter(ExecutionRequest.execution_id == execution_request_id)
            .first()
        )
        
        if not request_record:
            logger.error(f"ExecutionRequest {execution_request_id} not found.")
            return

        import base64

        # We use a query-param adapter URL since Judge0 just PUTs a simple JSON payload
        callback_url = f"{webhook_base}/execution/internal/judge0-callback?execution_id={execution_request_id}&correlation_id={request_record.correlation_id}"
        
        # Base64 encode the student source code and standard input
        source_code_b64 = base64.b64encode(request_record.source_code.encode("utf-8")).decode("utf-8")
        stdin_b64 = base64.b64encode(request_record.standard_input.encode("utf-8")).decode("utf-8") if request_record.standard_input else None

        payload = {
            "source_code": source_code_b64,
            "language_id": 71,  # Python
            "stdin": stdin_b64,
            "callback_url": callback_url,
            "cpu_time_limit": 5.0,           # Enforce 5-second max CPU time
            "memory_limit": 256000,          # Enforce 256MB memory cap (KB format)
            "wall_time_limit": 10.0,         # Enforce 10-second max wall time
            "max_processes_and_or_threads": 64, 
            "enable_network": False          # Strictly isolate classroom code
        }
        
        # Dispatch to partner with base64_encoded=true
        
        headers = {}
        if judge0_key:
            headers["X-RapidAPI-Key"] = judge0_key
            headers["X-Auth-Token"] = judge0_key
        if judge0_host:
            headers["X-RapidAPI-Host"] = judge0_host

        with httpx.Client(timeout=httpx.Timeout(10.0, read=10.0)) as client:
            response = client.post(f"{judge0_url}/submissions?base64_encoded=true", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # The worker_task_id will be the token returned by the partner
            token = data.get("token")
            if token:
                request_record.worker_task_id = token
                request_record.status = "running"
                db.commit()

    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to dispatch execution %s to Judge0 (attempt %s): %s",
            execution_request_id,
            self.request.retries + 1,
            type(e).__name__,
        )
        if self.request.retries >= self.max_retries:
            try:
                db.begin()
                req = db.query(ExecutionRequest).filter(ExecutionRequest.execution_id == execution_request_id).first()
                if req:
                    req.status = "failed"
                    # Shown to the student: no provider URL or error detail.
                    req.stderr = "System error: the code execution service could not be reached. Please try again."
                    db.commit()
            except Exception:
                db.rollback()
            raise
        # Retry task if partner is down and retries remain
        raise self.retry(exc=e, countdown=5)
    finally:
        db.close()


@celery.task(bind=True, max_retries=3)
def evaluate_submission_background_task(self, sub_id: int) -> None:
    import logging

    from app.core.database import SessionLocal
    from app.services.evaluation_service import evaluate_submission_by_id
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        evaluate_submission_by_id(db=db, sub_id=sub_id, instructor_id=None)
    except Exception as e:
        logger.error("Background evaluation failed for submission %s: %s", sub_id, type(e).__name__)
        raise self.retry(exc=e, countdown=5)
    finally:
        db.close()
