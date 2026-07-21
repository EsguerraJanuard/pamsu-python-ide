from logging.config import fileConfig
import os
from pathlib import Path
from typing import Any

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.pool import NullPool

from app.core.database import Base

# Import the complete domain-model module so every SQLAlchemy table is
# registered in Base.metadata before Alembic performs autogeneration.
from app.models import domain_models  # noqa: F401


# ------------------------------------------------------------------
# Paths and environment
# ------------------------------------------------------------------

ALEMBIC_DIRECTORY = Path(__file__).resolve().parent
BACKEND_DIRECTORY = ALEMBIC_DIRECTORY.parent
ENV_FILE = BACKEND_DIRECTORY / ".env"

SUPPORTED_DATABASE_DIALECTS = {
    "postgresql",
    "sqlite",
}

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


# ------------------------------------------------------------------
# Alembic configuration
# ------------------------------------------------------------------

config = context.config

if config.config_file_name is not None:
    fileConfig(
        config.config_file_name,
        disable_existing_loggers=False,
    )

target_metadata = Base.metadata


class AlembicConfigurationError(RuntimeError):
    """Raised when migration configuration is missing or unsafe."""


def get_database_url() -> str:
    database_url = (os.getenv("DATABASE_URL") or "").strip()

    if not database_url:
        raise AlembicConfigurationError(
            "DATABASE_URL is not configured. "
            "Add it to backend/.env before running Alembic."
        )

    try:
        parsed_url = make_url(database_url)
    except Exception as error:
        raise AlembicConfigurationError(
            "DATABASE_URL is not a valid SQLAlchemy database URL."
        ) from error

    database_dialect = parsed_url.get_backend_name()

    if database_dialect not in SUPPORTED_DATABASE_DIALECTS:
        raise AlembicConfigurationError(
            "Alembic migrations support only PostgreSQL "
            "and SQLite development databases."
        )

    if database_dialect == "postgresql" and not parsed_url.database:
        raise AlembicConfigurationError(
            "The PostgreSQL DATABASE_URL must include a database name."
        )

    return database_url


def get_database_dialect(
    database_url: str,
) -> str:
    return make_url(database_url).get_backend_name()


def build_context_options(
    *,
    database_dialect: str,
) -> dict[str, Any]:
    return {
        "target_metadata": target_metadata,
        "compare_type": True,
        "compare_server_default": True,
        "include_schemas": False,
        "render_as_batch": (database_dialect == "sqlite"),
        "version_table": "alembic_version",
        "transaction_per_migration": True,
    }


def configure_online_context(
    connection: Connection,
) -> None:
    context.configure(
        connection=connection,
        **build_context_options(
            database_dialect=(connection.dialect.name),
        ),
    )


# ------------------------------------------------------------------
# Offline migrations
# ------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Generate SQL migration output without opening a database connection.

    DATABASE_URL is still required so Alembic knows which SQL dialect
    should be used while rendering migration statements.
    """

    database_url = get_database_url()
    database_dialect = get_database_dialect(database_url)

    context.configure(
        url=database_url,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        **build_context_options(
            database_dialect=database_dialect,
        ),
    )

    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------------
# Online migrations
# ------------------------------------------------------------------


def run_migrations_online() -> None:
    """
    Run migrations against the configured database.

    A connection may be injected through config.attributes during tests.
    Otherwise, Alembic creates a temporary NullPool engine using the
    DATABASE_URL loaded from the environment.
    """

    injected_connection = config.attributes.get("connection")

    if injected_connection is not None:
        configure_online_context(injected_connection)

        with context.begin_transaction():
            context.run_migrations()

        return

    database_url = get_database_url()

    connectable = create_engine(
        database_url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )

    try:
        with connectable.connect() as connection:
            configure_online_context(connection)

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


# CONFIGURATION BOUNDARY:
# Database credentials are loaded from DATABASE_URL at runtime and are never
# stored in alembic.ini, migration scripts, logs, or committed repository files.

# METADATA BOUNDARY:
# Alembic autogeneration compares the database only with Base.metadata after
# all domain models have been imported.

# STARTUP BOUNDARY:
# Alembic migrations run only through explicit migration commands. Importing
# or starting FastAPI never upgrades the database automatically.
