"""Settings for running PAMS(U) IDE on a tester's own computer.

The local copy never reads backend/.env, keeps all of its data in
qa/.qa-data/qa.db (a throwaway SQLite file), and blanks every outside
service (email, Redis, Judge0, AI), so testing cannot reach the production
database, a real mailbox or a paid API.
"""

import json
import os
import secrets
import sys
from pathlib import Path

QA_DIR = Path(__file__).resolve().parent
REPO_DIR = QA_DIR.parent
BACKEND_DIR = REPO_DIR / "backend"
FRONTEND_DIR = REPO_DIR / "frontend"

DATA_DIR = QA_DIR / ".qa-data"
DB_PATH = DATA_DIR / "qa.db"
ACCOUNTS_FILE = DATA_DIR / "accounts.txt"
# Kept between runs so sign-ins survive a backend restart.
SECRETS_FILE = DATA_DIR / "server-secrets.json"

BACKEND_PORT = 8010
FRONTEND_PORT = 5174
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"


def _server_secrets() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    if SECRETS_FILE.exists():
        return json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    values = {
        "JWT_SECRET_KEY": secrets.token_urlsafe(48),
        "OTP_SECRET_KEY": secrets.token_urlsafe(48),
    }
    SECRETS_FILE.write_text(json.dumps(values), encoding="utf-8")
    return values


def apply() -> None:
    """Point the backend at the throwaway database and switch off outside services."""
    os.environ.update(
        {
            "PYTHON_DOTENV_DISABLED": "1",
            "PAMSU_ENVIRONMENT": "development",
            "DATABASE_URL": "sqlite:///" + DB_PATH.as_posix(),
            # Port 1 refuses connections at once: features that need Redis
            # take their documented "Redis unavailable" paths.
            "REDIS_URL": "redis://127.0.0.1:1/0",
            "REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS": "0.2",
            "PAMSU_CORS_ALLOWED_ORIGINS": f"http://localhost:{FRONTEND_PORT},http://127.0.0.1:{FRONTEND_PORT}",
            "PAMSU_ALLOWED_HOSTS": "localhost,127.0.0.1",
            **_server_secrets(),
        }
    )
    for name in (
        "SMTP_HOST", "SMTP_USER", "SMTP_PASS", "SMTP_SENDER_EMAIL",
        "GEMINI_API_KEY", "LLM_API_KEY", "LLM_API_URL",
        "JUDGE0_API_URL", "JUDGE0_API_KEY", "JUDGE0_HOST",
        "WEBHOOK_BASE_URL", "PAMSU_PARTNER_EXECUTION_TOKEN",
    ):
        os.environ[name] = ""
    os.chdir(BACKEND_DIR)
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
