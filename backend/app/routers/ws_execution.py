import asyncio
import tempfile
import os
import sys
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.redis_async import async_redis_client
from app.models.domain_models import User

router = APIRouter(
    prefix="/ws",
    tags=["WebSockets"],
)

settings = get_settings()

@router.websocket("/execute")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    # Authenticate WebSocket connection
    auth_token = token
    if not auth_token:
        # Check authorization header or sec-websocket-protocol
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            auth_token = auth_header.split(" ", 1)[1].strip()

    authenticated_user_id = None
    if auth_token:
        try:
            payload = jwt.decode(
                auth_token,
                settings.jwt_secret_key.get_secret_value(),
                algorithms=[settings.jwt_algorithm],
            )
            sub = payload.get("sub")
            if sub:
                authenticated_user_id = int(sub)
        except (JWTError, ValueError):
            pass

    # Verify user exists and is active in database
    if not authenticated_user_id:
        await websocket.accept()
        await websocket.send_text("\r\n[Authentication required: Please log in to run code]\r\n")
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == authenticated_user_id).first()
        if not user or not user.is_active:
            await websocket.accept()
            await websocket.send_text("\r\n[Authorization failed: Inactive or invalid user account]\r\n")
            await websocket.close(code=1008)
            return
    finally:
        db.close()

    # Rate Limiting: 30 executions per minute per user ID
    rate_limit_key = f"ws_rate_limit:user:{authenticated_user_id}"
    try:
        current_requests = await async_redis_client.get(rate_limit_key)
        if current_requests and int(current_requests) >= 30:
            await websocket.accept()
            await websocket.send_text("\r\n[Rate limit exceeded: Please wait before executing again]\r\n")
            await websocket.close(code=1008)
            return

        new_count = await async_redis_client.incr(rate_limit_key)
        if new_count == 1:
            await async_redis_client.expire(rate_limit_key, 60)
    except Exception as e:
        pass

    await websocket.accept()

    try:
        data = await websocket.receive_text()
    except WebSocketDisconnect:
        return

    # Sanitize environment variables: strip database credentials and API secrets
    safe_env = {
        "PATH": os.environ.get("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
        "PYTHONUNBUFFERED": "1",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }

    process = None
    try:
        encoded_code = base64.b64encode(data.encode("utf-8")).decode("utf-8")
        runner_cmd = f"import base64; exec(base64.b64decode('{encoded_code}').decode('utf-8'))"

        with tempfile.TemporaryDirectory() as sandbox_dir:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-u",
                "-c",
                runner_cmd,
                cwd=sandbox_dir,
                env=safe_env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            async def read_stdout():
                try:
                    while True:
                        chunk = await process.stdout.read(1024)
                        if not chunk:
                            break
                        await websocket.send_text(chunk.decode("utf-8", errors="replace"))
                except Exception:
                    pass

            async def write_stdin():
                try:
                    while True:
                        message = await websocket.receive_text()
                        if message and process.stdin:
                            process.stdin.write(message.encode("utf-8"))
                            await process.stdin.drain()
                except WebSocketDisconnect:
                    pass
                except Exception:
                    pass

            stdout_task = asyncio.create_task(read_stdout())
            stdin_task = asyncio.create_task(write_stdin())

            try:
                await asyncio.wait_for(process.wait(), timeout=15.0)
            except asyncio.TimeoutError:
                process.terminate()
                await websocket.send_text("\r\n\r\n[Process terminated: Time limit exceeded (15s)]")

            await asyncio.wait_for(stdout_task, timeout=1.0)
            stdin_task.cancel()

            await websocket.send_text(f"\r\n\r\n[Process exited with code {process.returncode}]")
            await websocket.close(code=1000)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        if process and process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
