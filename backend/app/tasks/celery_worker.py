import os
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery = Celery(
    __name__,
    broker=redis_url,
    backend=redis_url
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

        # We will use our mock payload format and callback url
        callback_url = f"{webhook_base}/execution/internal/partner-results"
        
        payload = {
            "source_code": request_record.source_code,
            "language_id": 71, # Python
            "stdin": request_record.standard_input,
            "callback_url": callback_url,
            "execution_id": execution_request_id,
            "correlation_id": request_record.correlation_id,
        }
        
        # Dispatch to partner
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{judge0_url}/submissions?base64_encoded=false", json=payload)
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

