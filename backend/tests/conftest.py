import os

# Tests must never reach a real database, mail relay, Redis or Celery broker.
# app.core.config calls load_dotenv(), which would otherwise read the
# developer's .env (real DATABASE_URL and SMTP credentials); load_dotenv does
# not override variables that are already set, so these win.
# PostgreSQL-only suites (migrations, concurrency) create and drop their own
# temporary database on the server named by PAMSU_TEST_DATABASE_URL; without
# it they are skipped.
os.environ["DATABASE_URL"] = os.environ.get("PAMSU_TEST_DATABASE_URL") or "sqlite://"
os.environ["PAMSU_ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-only-jwt-secret-key-0123456789abcdef"
os.environ["OTP_SECRET_KEY"] = "test-only-otp-secret-key-0123456789abcdef"
# Port 1 refuses connections immediately: Redis-backed features take their
# documented "Redis unavailable" paths without waiting on timeouts.
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
for variable in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "GEMINI_API_KEY", "JUDGE0_API_KEY"):
    os.environ[variable] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import domain_models  # noqa: F401


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@event.listens_for(test_engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def block_real_smtp(monkeypatch):
    # backend/.env may hold real SMTP credentials; tests must never send mail.
    from app.services import email_service

    monkeypatch.setattr(
        email_service,
        "get_smtp_config",
        lambda: {
            "host": "",
            "port": 0,
            "user": "",
            "password": "",
            "sender_name": "PSU Python IDE",
            "sender_email": "noreply@pampangastateu.edu.ph",
        },
    )


@pytest.fixture(autouse=True)
def reset_redis_memory_fallback():
    # Redis is unreachable in tests (REDIS_URL above), so rate limits, token
    # revocation and AI Tutor hints use the in-memory fallback; start each
    # test empty.
    from app.core import rate_limit, token_revocation
    from app.services import practice_hint_store

    stores = (rate_limit.memory_counters, token_revocation.revoked_in_memory, practice_hint_store.memory_store)

    for store in stores:
        store.clear()
    yield
    for store in stores:
        store.clear()


@pytest.fixture(autouse=True)
def celery_calls(monkeypatch):
    """Record Celery enqueues instead of contacting a broker."""

    from app.tasks import celery_worker

    calls: list[tuple[str, tuple]] = []

    for task_name in ("dispatch_to_partner", "evaluate_submission_background_task"):
        task = getattr(celery_worker, task_name)
        monkeypatch.setattr(
            task,
            "delay",
            lambda *args, _name=task_name: calls.append((_name, args)),
        )

    return calls


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
