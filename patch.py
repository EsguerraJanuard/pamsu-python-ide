import re
with open('backend/app/main.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('app = FastAPI(', 'from app.integrations.llm_adapters import get_local_llm_adapter\napp = FastAPI(')
c = c.replace('configure_request_logging(app)', 'configure_request_logging(app)\napp.state.llm_adapter = get_local_llm_adapter()')

with open('backend/app/main.py', 'w', encoding='utf-8') as f:
    f.write(c)