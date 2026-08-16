from fastapi import FastAPI, BackgroundTasks
import httpx
import uuid
from pydantic import BaseModel, ConfigDict
import asyncio

app = FastAPI()

class SubmissionRequest(BaseModel):
    source_code: str
    language_id: int
    stdin: str | None = None
    callback_url: str | None = None
    
    # Custom fields for our mock to pass back
    execution_id: str
    correlation_id: str
    
    model_config = ConfigDict(extra="ignore")

class SubmissionResponse(BaseModel):
    token: str

async def send_webhook(callback_url: str, execution_id: str, correlation_id: str, token: str):
    await asyncio.sleep(1)  # Simulate execution time
    
    # Simulate a successful execution output
    from datetime import datetime, timezone, timedelta
    payload = {
        "execution_id": execution_id,
        "correlation_id": correlation_id,
        "update_id": str(uuid.uuid4()),
        "sequence_number": 1,
        "worker_task_id": token,
        "status": "completed",
        "stdout": "Hello World!\n",
        "stderr": "",
        "exit_code": 0,
        "execution_time_ms": 150,
        "completed_at": (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat(),
        "limit_reason": None,
        "error_code": None,
        "error_message": None
    }
    
    import os
    # Use the static partner token defined in .env
    token_value = os.getenv("PAMSU_PARTNER_EXECUTION_TOKEN", "mortI2OQi9qiniHcd3a4_7uU5nagHy15A_nod7_AE5R3S75uIqAT9FnksX4PLe1W")
    headers = {
        "X-Partner-Token": token_value
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(callback_url, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"Failed to send webhook to {callback_url}: {response.status_code} {response.text}")
            else:
                print(f"Successfully sent webhook for {execution_id}")
        except Exception as e:
            print(f"Failed to send webhook: {e}")

@app.post("/submissions", response_model=SubmissionResponse)
async def create_submission(request: SubmissionRequest, background_tasks: BackgroundTasks):
    token = str(uuid.uuid4())
    
    if request.callback_url:
        background_tasks.add_task(
            send_webhook, 
            request.callback_url, 
            request.execution_id, 
            request.correlation_id,
            token
        )
        
    return {"token": token}
