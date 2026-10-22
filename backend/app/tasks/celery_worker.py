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

def judge0_connection() -> tuple[str, dict[str, str]]:
    """Judge0 base URL and auth headers (RapidAPI or a self-hosted token)."""

    judge0_url = os.getenv("JUDGE0_API_URL", "http://mock_judge0:8001")
    if judge0_url and not judge0_url.startswith("http"):
        judge0_url = f"https://{judge0_url}"
    judge0_key = os.getenv("JUDGE0_API_KEY")
    judge0_host = os.getenv("JUDGE0_HOST")

    headers: dict[str, str] = {}
    if judge0_key:
        headers["X-RapidAPI-Key"] = judge0_key
        headers["X-Auth-Token"] = judge0_key
    if judge0_host:
        headers["X-RapidAPI-Host"] = judge0_host
    return judge0_url.rstrip("/"), headers


def judge0_dispatch_outcome(error: Exception) -> str:
    """
    What to do after a failed Judge0 submission, without paying twice:

    - "retry": Judge0 certainly did not queue it (no connection, or it
      answered 429/5xx), so sending again is safe;
    - "fail": Judge0 refused the submission itself (another 4xx), and
      sending it again would be refused the same way;
    - "wait": the request may have reached Judge0 (the answer timed out or
      broke off). Sending it again could run, and bill, the code twice, so
      the attempt stays pending: the callback completes it, or the 120 s
      expiry closes it (app.services.practice_evaluation_service).
    """

    import httpx

    if isinstance(error, (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)):
        return "retry"
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        return "retry" if status == 429 or status >= 500 else "fail"
    if isinstance(error, httpx.TransportError):
        return "wait"
    # Not a network error (e.g. the database read): nothing was sent.
    return "retry"


@celery.task(bind=True, max_retries=2)
def dispatch_practice_attempt(self, attempt_id: int) -> None:
    """
    Send a pending solo-practice attempt to Judge0. Judge0 calls back to
    /practice/internal/judge0-callback with the result; nothing here waits
    for the run. Retries only when Judge0 certainly did not queue the code
    (judge0_dispatch_outcome); after the last failed try the attempt is
    closed as failed, so the page stops waiting.
    """

    import httpx
    from app.core.database import SessionLocal
    from app.services import practice_evaluation_service as practice

    db = SessionLocal()
    try:
        payload = practice.prepare_dispatch(db, attempt_id)
        # Committed reads only: end the transaction before the network call.
        db.rollback()
        if payload is None:
            return

        judge0_url, headers = judge0_connection()
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.post(f"{judge0_url}/submissions?base64_encoded=true", json=payload, headers=headers)
            response.raise_for_status()
    except Exception as error:
        db.rollback()
        outcome = judge0_dispatch_outcome(error)
        logger.error(
            "Failed to dispatch practice attempt %s to Judge0 (attempt %s): %s; %s.",
            attempt_id,
            self.request.retries + 1,
            type(error).__name__,
            outcome,
        )
        if outcome == "wait":
            return
        if outcome == "fail":
            practice.mark_attempt_failed(db, attempt_id=attempt_id, message=practice.RUNNER_ERROR_MESSAGE)
            return
        if self.request.retries >= self.max_retries:
            practice.mark_attempt_failed(db, attempt_id=attempt_id, message=practice.RUNNER_UNAVAILABLE_MESSAGE)
            return
        # Practice is interactive: retry quickly, and only twice.
        raise self.retry(exc=error, countdown=3)
    finally:
        db.close()


@celery.task(bind=True, max_retries=3)
def dispatch_to_partner(self, execution_request_id: str) -> None:
    import httpx
    from app.core.database import SessionLocal
    from app.models.domain_models import ExecutionRequest

    judge0_url, headers = judge0_connection()
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
        # A retry after Judge0 already answered (its callback finished the
        # request) must not send the code, and pay for it, again.
        if request_record.status != "queued":
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
        with httpx.Client(timeout=httpx.Timeout(10.0, read=10.0)) as client:
            response = client.post(f"{judge0_url}/submissions?base64_encoded=true", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # The worker_task_id will be the token returned by the partner.
            # Judge0's callback can arrive before this runs (a short program
            # on a quiet Judge0); it already recorded the result and the
            # token, so only a request that is still queued becomes "running".
            token = data.get("token")
            if token:
                db.query(ExecutionRequest).filter(
                    ExecutionRequest.execution_id == execution_request_id,
                    ExecutionRequest.status == "queued",
                ).update(
                    {ExecutionRequest.worker_task_id: token, ExecutionRequest.status: "running"},
                    synchronize_session=False,
                )
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
                # Only a request nothing has answered yet: a callback that
                # arrived meanwhile keeps its result.
                db.query(ExecutionRequest).filter(
                    ExecutionRequest.execution_id == execution_request_id,
                    ExecutionRequest.status.in_(("queued", "running")),
                    ExecutionRequest.completed_at.is_(None),
                ).update(
                    {
                        ExecutionRequest.status: "failed",
                        # Shown to the student: no provider URL or error detail.
                        ExecutionRequest.stderr: "System error: the code execution service could not be reached. Please try again.",
                    },
                    synchronize_session=False,
                )
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
