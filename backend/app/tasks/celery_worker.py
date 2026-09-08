import os
import ssl
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
# Remove any leftover query params if they were added in Render
if "?" in redis_url:
    redis_url = redis_url.split("?")[0]

ssl_conf = {'ssl_cert_reqs': ssl.CERT_NONE} if redis_url.startswith('rediss://') else None

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
)

@celery.task(bind=True, max_retries=3)
def dispatch_to_partner(self, execution_request_id: str) -> None:
    import httpx
    from app.core.database import SessionLocal
    from app.models.domain_models import ExecutionRequest
    from sqlalchemy.exc import SQLAlchemyError
    
    judge0_url = os.getenv("JUDGE0_API_URL", "http://mock_judge0:8001")
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
            print(f"ExecutionRequest {execution_request_id} not found.")
            return

        import base64

        # We use a query-param adapter URL since Judge0 just PUTs a simple JSON payload
        callback_url = f"{webhook_base}/execution/internal/judge0-callback?execution_id={execution_request_id}&correlation_id={request_record.correlation_id}"
        
        # Base64 encode the student source code and standard input
        source_code_b64 = base64.b64encode(request_record.source_code.encode("utf-8")).decode("utf-8")
        stdin_b64 = base64.b64encode(request_record.standard_input.encode("utf-8")).decode("utf-8") if request_record.standard_input else None

        payload = {
            "source_code": source_code_b64,
            "language_id": 71, # Python
            "stdin": stdin_b64,
            "callback_url": callback_url,
        }
        
        # Dispatch to partner with base64_encoded=true
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{judge0_url}/submissions?base64_encoded=true", json=payload)
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
        print(f"Failed to dispatch to partner: {e}")
        # Retry task if partner is down
        raise self.retry(exc=e, countdown=5)
    finally:
        db.close()

