import asyncio
import tempfile
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(
    prefix="/ws",
    tags=["WebSockets"],
)

from app.core.redis_async import async_redis_client
import time

@router.websocket("/execute")
async def websocket_endpoint(websocket: WebSocket):
    # Retrieve user_id from headers/cookies or assume anonymous IP
    # For a robust implementation, you should parse the token here
    client_id = websocket.client.host if websocket.client else "unknown"
    
    # Simple Redis Rate Limiter: max 3 requests per minute per client
    rate_limit_key = f"ws_rate_limit:{client_id}"
    try:
        current_requests = await async_redis_client.get(rate_limit_key)
        if current_requests and int(current_requests) >= 3:
            await websocket.accept()
            await websocket.send_text("Rate limit exceeded. Please wait a minute before running code again.")
            await websocket.close(code=1008)
            return
            
        await async_redis_client.incr(rate_limit_key)
        await async_redis_client.expire(rate_limit_key, 60)
    except Exception as e:
        print(f"Redis rate limiter error: {e}")

    await websocket.accept()
    
    try:
        # Wait for the initial payload (the source code)
        data = await websocket.receive_text()
    except WebSocketDisconnect:
        return
        
    # Code is directly encoded into the Docker command
        
    process = None
    try:
        # Spawn the process in a sandboxed Docker container
        import base64
        encoded_code = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        runner_cmd = f"import base64; exec(base64.b64decode('{encoded_code}').decode('utf-8'))"
        
        process = await asyncio.create_subprocess_exec(
            "docker", "run", "-i", "--rm",
            "--network", "none",
            "--cpus", "0.5",
            "--memory", "128m",
            "python:3.13-slim",
            "python", "-u", "-c", runner_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        async def read_stdout():
            try:
                while True:
                    # Read byte by byte or by chunks
                    chunk = await process.stdout.read(1024)
                    if not chunk:
                        break
                    # Send output to the frontend terminal
                    await websocket.send_text(chunk.decode('utf-8', errors='replace'))
            except Exception as e:
                print(f"Stdout read error: {e}")
                
        async def write_stdin():
            try:
                while True:
                    message = await websocket.receive_text()
                    if message and process.stdin:
                        process.stdin.write(message.encode('utf-8'))
                        await process.stdin.drain()
            except WebSocketDisconnect:
                pass
            except Exception as e:
                print(f"Stdin write error: {e}")

        # Run both tasks concurrently
        stdout_task = asyncio.create_task(read_stdout())
        stdin_task = asyncio.create_task(write_stdin())
        
        # Wait for the process to finish
        await process.wait()
        
        # Wait a tiny bit for stdout to flush
        await asyncio.wait_for(stdout_task, timeout=1.0)
        
        # Cancel the stdin task since the process is done and we don't need input
        stdin_task.cancel()
        
        # Send a terminal closing message
        await websocket.send_text("\r\n\r\n[Process exited with code " + str(process.returncode) + "]")
        
        # Close connection cleanly
        await websocket.close(code=1000)
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket execution error: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        # Cleanup process and temp file
        if process and process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
