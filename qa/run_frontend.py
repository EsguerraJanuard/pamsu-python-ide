"""Start the local QA frontend on http://localhost:5174. Stop it with Ctrl+C.

It talks only to the local QA backend (http://127.0.0.1:8010), never to the
live site. Usage, from the repository folder:
    backend\\venv\\Scripts\\python.exe qa\\run_frontend.py
"""

import os
import subprocess
import sys

import qa_env

if not (qa_env.FRONTEND_DIR / "node_modules").exists():
    print("The frontend packages are not installed yet. Run this first:")
    print("  cd frontend")
    print("  npm ci")
    sys.exit(1)

env = dict(os.environ)
# Environment values win over frontend/.env files, so this copy can never
# point at the production API.
env["VITE_API_BASE_URL"] = qa_env.BACKEND_URL
env["VITE_DEFAULT_REQUEST_TIMEOUT_MS"] = "15000"

print(f"QA frontend starting on {qa_env.FRONTEND_URL} (Ctrl+C to stop)")
try:
    subprocess.run(
        f"npm run dev -- --port {qa_env.FRONTEND_PORT} --strictPort",
        cwd=qa_env.FRONTEND_DIR,
        env=env,
        shell=True,
        check=False,
    )
except KeyboardInterrupt:
    pass
