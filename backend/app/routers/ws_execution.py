import asyncio
import tempfile
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(
    prefix="/ws",
    tags=["WebSockets"],
)

@router.websocket("/execute")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Wait for the initial payload (the source code)
        data = await websocket.receive_text()
    except WebSocketDisconnect:
        return
        
    # Save code to a temp file
    fd, temp_script_path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(data)
        
    process = None
    try:
        # Spawn the process
        process = await asyncio.create_subprocess_exec(
            "python", "-u", temp_script_path,
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
        try:
            os.remove(temp_script_path)
        except FileNotFoundError:
            pass