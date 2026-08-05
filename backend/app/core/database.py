from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    Session,
    declarative_base,
    sessionmaker,
)

from app.core.config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.database_url.get_secret_value()

engine_options: dict[str, Any] = {
    "pool_pre_ping": True,
}

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {
        "check_same_thread": False,
    }

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **engine_options,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Provide one SQLAlchemy database session per FastAPI request.

    The session is always closed after the request finishes, including
    requests that end because of an exception.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# CONFIGURATION BOUNDARY:
# Database configuration is loaded only through the validated immutable
# application settings object. This module does not parse environment
# variables independently.

# SECRET HANDLING BOUNDARY:
# The database URL is unwrapped only when constructing the SQLAlchemy
# engine. It must never be logged, returned in an API response, or exposed
# through health and readiness endpoints.

# SESSION BOUNDARY:
# Each FastAPI request receives an independent SQLAlchemy session that is
# always closed after use. Commit and rollback responsibilities remain with
# the service or workflow performing the database operation.

# TEST COMPATIBILITY:
# SQLite connections disable same-thread enforcement for isolated tests.
# Production PostgreSQL connections retain pool pre-ping validation.
