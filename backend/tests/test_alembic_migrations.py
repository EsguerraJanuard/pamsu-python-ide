from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import psycopg2
import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from dotenv import dotenv_values
from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.engine import make_url


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
ALEMBIC_INI_PATH = BACKEND_DIRECTORY / "alembic.ini"
ALEMBIC_DIRECTORY = BACKEND_DIRECTORY / "alembic"
ENV_FILE = BACKEND_DIRECTORY / ".env"

BASELINE_REVISION = "18d3ef8f020d"

EXPECTED_APPLICATION_TABLES = {
    "academic_events",
    "ast_analyses",
    "ast_findings",
    "audit_records",
    "behavioral_logs",
    "classrooms",
    "coding_sessions",
    "enrollments",
    "execution_requests",
    "instructor_allowlist",
    "instructor_grades",
    "notifications",
    "otp_challenges",
    "partner_execution_updates",
    "pending_registrations",
    "similarity_results",
    "submissions",
    "task_test_cases",
    "tasks",
    "users",
}


def get_configured_database_url() -> URL:
    environment_value = (os.getenv("DATABASE_URL") or "").strip()

    dotenv_value = (dotenv_values(ENV_FILE).get("DATABASE_URL") or "").strip()

    database_url = environment_value or dotenv_value

    if not database_url:
        pytest.fail("DATABASE_URL is required for Alembic migration tests.")

    try:
        return make_url(database_url)
    except Exception as error:
        pytest.fail(
            f"DATABASE_URL is not a valid SQLAlchemy URL: {type(error).__name__}"
        )


def build_alembic_config() -> Config:
    config = Config(
        str(ALEMBIC_INI_PATH),
    )

    config.set_main_option(
        "script_location",
        str(ALEMBIC_DIRECTORY),
    )

    return config


def build_psycopg2_connection_kwargs(
    database_url: URL,
) -> dict[str, object]:
    connection_kwargs: dict[str, object] = {}

    if database_url.database:
        connection_kwargs["dbname"] = database_url.database

    if database_url.username:
        connection_kwargs["user"] = database_url.username

    if database_url.password:
        connection_kwargs["password"] = database_url.password

    if database_url.host:
        connection_kwargs["host"] = database_url.host

    if database_url.port:
        connection_kwargs["port"] = database_url.port

    return connection_kwargs


def create_temporary_database(
    *,
    administrator_url: URL,
    database_name: str,
) -> None:
    connection = psycopg2.connect(**build_psycopg2_connection_kwargs(administrator_url))

    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
            )
    finally:
        connection.close()


def drop_temporary_database(
    *,
    administrator_url: URL,
    database_name: str,
) -> None:
    connection = psycopg2.connect(**build_psycopg2_connection_kwargs(administrator_url))

    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s
                  AND pid <> pg_backend_pid()
                """,
                (database_name,),
            )

            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(database_name)
                )
            )
    finally:
        connection.close()


def read_database_tables(
    database_url: URL,
) -> set[str]:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def read_database_revision(
    database_url: URL,
) -> str | None:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    try:
        tables = set(inspect(engine).get_table_names())

        if "alembic_version" not in tables:
            return None

        with engine.connect() as connection:
            return connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
    finally:
        engine.dispose()


@pytest.fixture
def temporary_postgresql_database(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[URL]:
    administrator_url = get_configured_database_url()

    if administrator_url.get_backend_name() != "postgresql":
        pytest.skip("Alembic integration smoke tests require PostgreSQL.")

    if not administrator_url.database:
        pytest.fail("The configured PostgreSQL URL must include a database name.")

    database_name = f"pamsu_ide_alembic_pytest_{uuid4().hex[:12]}"

    create_temporary_database(
        administrator_url=administrator_url,
        database_name=database_name,
    )

    temporary_url = administrator_url.set(
        database=database_name,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        temporary_url.render_as_string(
            hide_password=False,
        ),
    )

    try:
        yield temporary_url
    finally:
        drop_temporary_database(
            administrator_url=administrator_url,
            database_name=database_name,
        )


def test_alembic_ini_does_not_store_database_url():
    config = Config(
        str(ALEMBIC_INI_PATH),
    )

    stored_database_url = (config.get_main_option("sqlalchemy.url") or "").strip()

    assert stored_database_url == ""


def test_alembic_revision_graph_has_baseline_and_one_head():
    config = build_alembic_config()
    script = ScriptDirectory.from_config(config)

    baseline_revision = script.get_revision(BASELINE_REVISION)

    assert baseline_revision is not None
    assert baseline_revision.down_revision is None
    assert len(script.get_heads()) == 1


def test_alembic_upgrade_downgrade_and_reupgrade(
    temporary_postgresql_database: URL,
):
    config = build_alembic_config()
    script = ScriptDirectory.from_config(config)

    current_head = script.get_current_head()

    assert current_head is not None

    command.upgrade(
        config,
        "head",
    )

    upgraded_tables = read_database_tables(temporary_postgresql_database)

    assert upgraded_tables == (
        EXPECTED_APPLICATION_TABLES
        | {
            "alembic_version",
        }
    )

    assert read_database_revision(temporary_postgresql_database) == current_head

    command.check(
        config,
    )

    command.downgrade(
        config,
        "base",
    )

    downgraded_tables = read_database_tables(temporary_postgresql_database)

    assert downgraded_tables == {
        "alembic_version",
    }

    assert read_database_revision(temporary_postgresql_database) is None

    command.upgrade(
        config,
        "head",
    )

    reupgraded_tables = read_database_tables(temporary_postgresql_database)

    assert reupgraded_tables == (
        EXPECTED_APPLICATION_TABLES
        | {
            "alembic_version",
        }
    )

    assert read_database_revision(temporary_postgresql_database) == current_head

    command.check(
        config,
    )


# DATABASE SAFETY BOUNDARY:
# Migration integration tests never upgrade, downgrade, drop, or recreate
# the configured development database. Each test creates a uniquely named
# temporary PostgreSQL database and drops only that database afterward.

# MIGRATION BOUNDARY:
# FastAPI startup does not execute Alembic commands. Schema changes remain
# explicit migration operations invoked by deployment or test workflows.

# CREDENTIAL BOUNDARY:
# Tests use DATABASE_URL only at runtime. Credentials and complete connection
# strings are never written to alembic.ini, migration files, or test output.
