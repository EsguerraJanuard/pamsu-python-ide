"""
Migration 61330560eec5: admin audit action and resource types.

PostgreSQL only (skipped otherwise). Each test runs in its own temporary
database created and dropped by `temporary_postgresql_database`; the
configured development database is never touched.

`alembic check` does not compare CHECK constraints, so these tests also
compare the allowed values in the database with the ORM model.
"""

import re
from uuid import uuid4

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError

from app.models.domain_models import AuditRecord
from tests.test_alembic_migrations import (  # noqa: F401  (fixture import)
    build_alembic_config, temporary_postgresql_database)

REVISION = "61330560eec5"
PREVIOUS_REVISION = "c25114413200"
NEW_ACTIONS = {
    "user_created",
    "user_status_changed",
    "user_password_reset",
    "user_deleted",
    "system_settings_updated",
    "masterlist_imported",
}
NEW_RESOURCES = {"system_setting", "masterlist_import"}


def build_script_head() -> str:
    # Later revisions (b7e4c2a91f03, practice attempt status) chain after this one.
    return ScriptDirectory.from_config(build_alembic_config()).get_current_head()


def _insert_audit(url: URL, action_type: str, resource_type: str) -> None:
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO audit_records "
                    "(audit_id, audit_key, action_type, resource_type, resource_id, outcome, audit_data) "
                    "VALUES (:id, :key, :action, :resource, '1', 'succeeded', '{}')"
                ),
                {"id": str(uuid4()), "key": f"test:{uuid4()}", "action": action_type, "resource": resource_type},
            )
    finally:
        engine.dispose()


def _scalar(url: URL, sql: str):
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            return connection.execute(text(sql)).scalar_one()
    finally:
        engine.dispose()


def _database_values(url: URL, constraint: str) -> set[str]:
    definition = _scalar(
        url,
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        f"WHERE conrelid = 'audit_records'::regclass AND conname = '{constraint}'",
    )
    return set(re.findall(r"'([a-z_]+)'", definition))


def _model_values(constraint: str) -> set[str]:
    for table_constraint in AuditRecord.__table__.constraints:
        if table_constraint.name == constraint:
            return set(re.findall(r"'([a-z_]+)'", str(table_constraint.sqltext)))
    raise AssertionError(f"{constraint} is not declared on AuditRecord")


def test_upgrade_allows_admin_types_and_matches_the_model(temporary_postgresql_database: URL):
    url = temporary_postgresql_database
    config = build_alembic_config()

    command.upgrade(config, PREVIOUS_REVISION)
    with pytest.raises(IntegrityError):
        _insert_audit(url, "user_created", "user")

    _insert_audit(url, "login_succeeded", "user")
    command.upgrade(config, REVISION)

    for action in NEW_ACTIONS:
        _insert_audit(url, action, "user")
    _insert_audit(url, "system_settings_updated", "system_setting")
    _insert_audit(url, "masterlist_imported", "masterlist_import")

    # Existing rows survive and unknown values are still rejected.
    assert _scalar(url, "SELECT count(*) FROM audit_records WHERE action_type = 'login_succeeded'") == 1
    with pytest.raises(IntegrityError):
        _insert_audit(url, "made_up_action", "user")
    with pytest.raises(IntegrityError):
        _insert_audit(url, "user_created", "made_up_resource")

    for constraint in ("ck_audit_records_action_type", "ck_audit_records_resource_type"):
        assert _database_values(url, constraint) == _model_values(constraint)

    # `alembic check` compares the model with a database at head.
    command.upgrade(config, "head")
    command.check(config)


def test_downgrade_refuses_while_new_types_are_in_use(temporary_postgresql_database: URL):
    url = temporary_postgresql_database
    config = build_alembic_config()

    command.upgrade(config, REVISION)
    _insert_audit(url, "user_deleted", "user")

    with pytest.raises(RuntimeError, match="Cannot downgrade 61330560eec5"):
        command.downgrade(config, PREVIOUS_REVISION)

    # Nothing changed: same revision, same constraint, the record is kept.
    assert _scalar(url, "SELECT version_num FROM alembic_version") == REVISION
    assert NEW_ACTIONS <= _database_values(url, "ck_audit_records_action_type")
    assert _scalar(url, "SELECT count(*) FROM audit_records WHERE action_type = 'user_deleted'") == 1


def test_downgrade_restores_baseline_lists_when_unused(temporary_postgresql_database: URL):
    url = temporary_postgresql_database
    config = build_alembic_config()

    command.upgrade(config, PREVIOUS_REVISION)
    baseline_actions = _database_values(url, "ck_audit_records_action_type")
    baseline_resources = _database_values(url, "ck_audit_records_resource_type")

    command.upgrade(config, REVISION)
    _insert_audit(url, "grade_released", "grade")
    command.downgrade(config, PREVIOUS_REVISION)

    assert _database_values(url, "ck_audit_records_action_type") == baseline_actions
    assert _database_values(url, "ck_audit_records_resource_type") == baseline_resources
    assert baseline_actions.isdisjoint(NEW_ACTIONS)
    assert baseline_resources.isdisjoint(NEW_RESOURCES)
    assert _scalar(url, "SELECT count(*) FROM audit_records WHERE action_type = 'grade_released'") == 1
    with pytest.raises(IntegrityError):
        _insert_audit(url, "user_created", "user")

    command.upgrade(config, "head")
    assert _scalar(url, "SELECT version_num FROM alembic_version") == build_script_head()
    assert NEW_ACTIONS <= _database_values(url, "ck_audit_records_action_type")
