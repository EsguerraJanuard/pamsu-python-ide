"""Start the local QA backend on http://127.0.0.1:8010. Stop it with Ctrl+C.

Usage, from the repository folder:
    backend\\venv\\Scripts\\python.exe qa\\run_backend.py
"""

import sys

import qa_env

if not qa_env.DB_PATH.exists():
    print("No QA database yet. Run this first:")
    print("  backend\\venv\\Scripts\\python.exe qa\\qa_setup.py")
    sys.exit(1)

qa_env.apply()

import uvicorn  # noqa: E402

print(f"QA backend starting on {qa_env.BACKEND_URL} (Ctrl+C to stop)")
uvicorn.run("app.main:app", host="127.0.0.1", port=qa_env.BACKEND_PORT, log_level="info")
