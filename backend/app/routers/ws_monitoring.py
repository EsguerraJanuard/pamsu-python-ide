import json
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.redis_async import async_redis_client
from app.core.security import SECRET_KEY, ALGORITHM, get_current_user
from app.models.domain_models import User

router = APIRouter()

from fastapi.concurrency import run_in_threadpool

async def get_user_from_token(token: str, db: Session) -> Optional[User]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        subject = payload.get("sub")
        if not subject:
            return None
        user_id = int(subject)
        
        def fetch_user():
            return db.query(User).filter(User.user_id == user_id).first()
            
        return await run_in_threadpool(fetch_user)
    except (JWTError, ValueError):
        return None

@router.websocket("/student")
async def student_telemetry_ws(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for student sandboxes to stream telemetry 
    (tab switches, pastes) to Redis Pub/Sub.
    """
    await websocket.accept()
    user = await get_user_from_token(token, db)
    
    if not user or user.role != "student":
        await websocket.close(code=1008, reason="Unauthorized")
        return

    try:
        await async_redis_client.sadd("presence:online_students", user.user_id)
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                # Append user info for instructor dashboard
                payload["student_id"] = user.user_id
                payload["student_name"] = user.full_name
                
                # Publish to a global monitoring channel
                await async_redis_client.publish(
                    "monitoring:global", 
                    json.dumps(payload)
                )
                
                # If there's a task_id, publish to a task-specific channel too
                if "task_id" in payload:
                    await async_redis_client.publish(
                        f"monitoring:task:{payload['task_id']}", 
                        json.dumps(payload)
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        # Student closed tab or disconnected
        pass
    except Exception as e:
        print(f"WS Student Error: {e}")
        await websocket.close(code=1011)
    finally:
        await async_redis_client.srem("presence:online_students", user.user_id)

@router.websocket("/instructor")
async def instructor_monitoring_ws(
    websocket: WebSocket,
    token: str = Query(...),
    task_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for Instructor Dashboard to listen to telemetry.
    """
    await websocket.accept()
    user = await get_user_from_token(token, db)
    
    if not user or user.role != "instructor":
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # Determine which channel to subscribe to
    channel = f"monitoring:task:{task_id}" if task_id else "monitoring:global"
    
    pubsub = async_redis_client.pubsub()
    await pubsub.subscribe(channel)
    
    try:
        async def pubsub_reader():
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    await websocket.send_text(message["data"])
                await asyncio.sleep(0.01)  # Yield control to prevent tight looping

        async def websocket_reader():
            while True:
                await websocket.receive()

        pubsub_task = asyncio.create_task(pubsub_reader())
        ws_task = asyncio.create_task(websocket_reader())

        done, pending = await asyncio.wait(
            [pubsub_task, ws_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Instructor Error: {e}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
