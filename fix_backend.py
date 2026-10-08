import os
import re

def ensure_logger(content):
    if "import logging" not in content:
        # Find first import to inject after
        content = re.sub(r'^(import .*|from .* import .*)$', r'import logging\n\1', content, count=1, flags=re.MULTILINE)
    
    if "logger = logging.getLogger" not in content:
        # Inject after imports
        imports_end = [m.end() for m in re.finditer(r'^(import .*|from .* import .*)$', content, flags=re.MULTILINE)]
        if imports_end:
            insert_pos = imports_end[-1]
            content = content[:insert_pos] + '\n\nlogger = logging.getLogger(__name__)\n' + content[insert_pos:]
        else:
            content = "import logging\nlogger = logging.getLogger(__name__)\n\n" + content
    return content

# 1. Fix prints to logger.error
files_with_prints = [
    "backend/app/routers/ws_execution.py",
    "backend/app/routers/submissions.py",
    "backend/app/tasks/celery_worker.py"
]

for fpath in files_with_prints:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        content = ensure_logger(content)
        content = re.sub(r'print\((f?".*?")\)', r'logger.error(\1)', content)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

# 2. Fix swallowed exceptions
files_with_swallowed = [
    "backend/app/services/reporting_service.py",
    "backend/app/services/classroom_service.py",
    "backend/app/services/task_service.py",
    "backend/app/services/otp_service.py",
    "backend/app/services/jaccard.py"
]

for fpath in files_with_swallowed:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = ensure_logger(content)
        
        # Replace `except Exception:\n    pass`
        content = re.sub(
            r'except\s*(?:Exception)?\s*:\s*\n(\s*)pass\b', 
            r'except Exception as e:\n\1logger.warning(f"Caught silent exception: {e}", exc_info=True)', 
            content
        )
        
        # Replace `except:\n    pass`
        content = re.sub(
            r'except\s*:\s*\n(\s*)pass\b', 
            r'except Exception as e:\n\1logger.warning(f"Caught silent exception: {e}", exc_info=True)', 
            content
        )
        
        # Replace `except Exception as e:\n    pass`
        content = re.sub(
            r'except\s*Exception\s*as\s*[a-zA-Z_]\w*\s*:\s*\n(\s*)pass\b', 
            r'except Exception as e:\n\1logger.warning(f"Caught silent exception: {e}", exc_info=True)', 
            content
        )

        # Replace `except Exception:\n    return`
        content = re.sub(
            r'except\s*(?:Exception)?\s*:\s*\n(\s*)return\b', 
            r'except Exception as e:\n\1logger.warning(f"Caught silent exception: {e}", exc_info=True)\n\1return', 
            content
        )
        
        # Replace `except:\n    return`
        content = re.sub(
            r'except\s*:\s*\n(\s*)return\b', 
            r'except Exception as e:\n\1logger.warning(f"Caught silent exception: {e}", exc_info=True)\n\1return', 
            content
        )

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

# 3. Fix llm_adapters.py
llm_path = "backend/app/integrations/llm_adapters.py"
if os.path.exists(llm_path):
    with open(llm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove the hardcoded fallback
    content = content.replace(
        'self.api_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")', 
        'self.api_url = os.getenv("LLM_API_URL")\n        if not self.api_url:\n            raise ValueError("LLM_API_URL is missing.")'
    )
    with open(llm_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Backend fixes complete.")
