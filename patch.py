import re
with open('backend/app/routers/ws_execution.py', 'r', encoding='utf-8') as f:
    c = f.read()

t1 = '''@router.websocket("/execute")
async def websocket_endpoint(websocket: WebSocket):'''

r1 = '''from app.core.redis_async import async_redis_client
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
'''

c = c.replace(t1, r1)

with open('backend/app/routers/ws_execution.py', 'w', encoding='utf-8') as f:
    f.write(c)