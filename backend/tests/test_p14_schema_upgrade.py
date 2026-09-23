import os
from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool


os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///./test_p14_schema_upgrade_bootstrap.db",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-jwt-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "OTP_SECRET_KEY",
    "test-otp-secret-key-with-at-least-thirty-two-characters",
)


from app.db.upgrade_p14_partner_execution import (
    PARTNER_UPDATES_TABLE,
    Pillar14SchemaUpgradeError,
    upgrade_pillar14_partner_execution_schema,
)


LEGACY_SOURCE_ONE = "print('legacy-one')\n"
LEGACY_SOURCE_TWO = "print('legacy-two')\n"


@pytest.fixture()
def sqlite_engine() -> Generator[Engine, None, None]:
    database_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    try:
        yield database_engine
    finally:
        database_engine.dispose()


def create_legacy_execution_table(
    database_engine: Engine,
) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE execution_requests ("
                "execution_id VARCHAR(36) PRIMARY KEY, "
                "status VARCHAR(30) NOT NULL, "
                "source_code TEXT NOT NULL"
                ")"
            )
        )


def create_partially_upgraded_execution_table(
    database_engine: Engine,
) -> None:
    with database_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE execution_requests ("
                "execution_id VARCHAR(36) PRIMARY KEY, "
                "correlation_id VARCHAR(36), "
                "dispatch_idempotency_key VARCHAR(36), "
                "last_partner_sequence INTEGER DEFAULT 0, "
                "status VARCHAR(30) NOT NULL, "
                "source_code TEXT NOT NULL"
                ")"
            )
        )


def insert_execution(
    database_engine: Engine,
    *,
    execution_id: str,
    status_value: str = "queued",
    source_code: str = LEGACY_SOURCE_ONE,
    correlation_id: str | None = None,
    dispatch_idempotency_key: str | None = None,
    last_partner_sequence: int | None = None,
    include_partner_columns: bool = False,
) -> None:
    with database_engine.begin() as connection:
        if include_partner_columns:
            connection.execute(
                text(
                    "INSERT INTO execution_requests ("
                    "execution_id, correlation_id, "
                    "dispatch_idempotency_key, "
                    "last_partner_sequence, status, source_code"
                    ") VALUES ("
                    ":execution_id, :correlation_id, "
                    ":dispatch_idempotency_key, "
                    ":last_partner_sequence, :status, :source_code"
                    ")"
                ),
                {
                    "execution_id": execution_id,
                    "correlation_id": correlation_id,
                    "dispatch_idempotency_key": (dispatch_idempotency_key),
                    "last_partner_sequence": (last_partner_sequence),
                    "status": status_value,
                    "source_code": source_code,
                },
            )
            return

        connection.execute(
            text(
                "INSERT INTO execution_requests ("
                "execution_id, status, source_code"
                ") VALUES ("
                ":execution_id, :status, :source_code"
                ")"
            ),
            {
                "execution_id": execution_id,
                "status": status_value,
                "source_code": source_code,
            },
        )


def read_execution_rows(
    database_engine: Engine,
) -> list[dict[str, object]]:
    with database_engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text(
                    "SELECT execution_id, correlation_id, "
                    "dispatch_idempotency_key, "
                    "last_partner_sequence, status, source_code "
                    "FROM execution_requests "
                    "ORDER BY execution_id"
                )
            ).mappings()
        ]


def assert_uuid_string(value: object) -> None:
    assert isinstance(value, str)
    assert str(UUID(value)) == value


def test_upgrade_rejects_database_without_base_execution_table(
    sqlite_engine: Engine,
):
    with pytest.raises(
        Pillar14SchemaUpgradeError,
        match="execution_requests table does not exist",
    ):
        upgrade_pillar14_partner_execution_schema(sqlite_engine)

    assert PARTNER_UPDATES_TABLE not in inspect(sqlite_engine).get_table_names()


def test_upgrade_adds_columns_backfills_rows_and_creates_table(
    sqlite_engine: Engine,
):
    create_legacy_execution_table(sqlite_engine)

    first_execution_id = str(uuid4())
    second_execution_id = str(uuid4())

    insert_execution(
        sqlite_engine,
        execution_id=first_execution_id,
        source_code=LEGACY_SOURCE_ONE,
    )
    insert_execution(
        sqlite_engine,
        execution_id=second_execution_id,
        source_code=LEGACY_SOURCE_TWO,
    )

    result = upgrade_pillar14_partner_execution_schema(sqlite_engine)

    assert result.dialect == "sqlite"
    assert result.execution_rows_backfilled == 2
    assert result.partner_update_table_created is True

    inspector = inspect(sqlite_engine)
    execution_columns = {
        column["name"] for column in inspector.get_columns("execution_requests")
    }

    assert {
        "correlation_id",
        "dispatch_idempotency_key",
        "last_partner_sequence",
    }.issubset(execution_columns)

    assert PARTNER_UPDATES_TABLE in inspector.get_table_names()

    rows = read_execution_rows(sqlite_engine)

    assert len(rows) == 2
    assert {row["source_code"] for row in rows} == {
        LEGACY_SOURCE_ONE,
        LEGACY_SOURCE_TWO,
    }

    correlation_ids = {row["correlation_id"] for row in rows}
    dispatch_keys = {row["dispatch_idempotency_key"] for row in rows}

    assert len(correlation_ids) == 2
    assert len(dispatch_keys) == 2

    for row in rows:
        assert_uuid_string(row["correlation_id"])
        assert_uuid_string(row["dispatch_idempotency_key"])
        assert row["last_partner_sequence"] == 0


def test_upgrade_creates_expected_execution_indexes(
    sqlite_engine: Engine,
):
    create_legacy_execution_table(sqlite_engine)
    insert_execution(
        sqlite_engine,
        execution_id=str(uuid4()),
    )

    upgrade_pillar14_partner_execution_schema(sqlite_engine)

    indexes = {
        index["name"]: index
        for index in inspect(sqlite_engine).get_indexes("execution_requests")
    }

    assert indexes["uq_execution_requests_correlation_id"]["unique"] == 1
    assert indexes["uq_execution_requests_dispatch_idempotency_key"]["unique"] == 1

    partner_state_index = indexes["ix_execution_requests_partner_state"]

    assert partner_state_index["unique"] == 0
    assert partner_state_index["column_names"] == [
        "status",
        "last_partner_sequence",
    ]


def test_partner_update_table_contains_only_contract_metadata(
    sqlite_engine: Engine,
):
    create_legacy_execution_table(sqlite_engine)
    insert_execution(
        sqlite_engine,
        execution_id=str(uuid4()),
    )

    upgrade_pillar14_partner_execution_schema(sqlite_engine)

    actual_columns = {
        column["name"]
        for column in inspect(sqlite_engine).get_columns(PARTNER_UPDATES_TABLE)
    }

    assert actual_columns == {
        "partner_update_record_id",
        "update_id",
        "execution_id",
        "correlation_id",
        "sequence_number",
        "status",
        "payload_digest",
        "accepted_at",
    }

    prohibited_columns = {
        "source_code",
        "standard_input",
        "stdout",
        "stderr",
        "password",
        "password_hash",
        "otp",
        "otp_code",
        "jwt",
        "access_token",
        "grade",
        "official_grade",
        "ast_findings",
        "similarity_details",
        "session_telemetry",
        "clipboard_content",
        "pasted_text",
        "misconduct_verdict",
    }

    assert prohibited_columns.isdisjoint(actual_columns)


def test_upgrade_preserves_existing_valid_partner_identifiers(
    sqlite_engine: Engine,
):
    create_partially_upgraded_execution_table(sqlite_engine)

    execution_id = str(uuid4())
    correlation_id = str(uuid4())
    dispatch_key = str(uuid4())

    insert_execution(
        sqlite_engine,
        execution_id=execution_id,
        correlation_id=correlation_id,
        dispatch_idempotency_key=dispatch_key,
        last_partner_sequence=4,
        include_partner_columns=True,
    )

    result = upgrade_pillar14_partner_execution_schema(sqlite_engine)

    assert result.execution_rows_backfilled == 0

    row = read_execution_rows(sqlite_engine)[0]

    assert row["correlation_id"] == correlation_id
    assert row["dispatch_idempotency_key"] == dispatch_key
    assert row["last_partner_sequence"] == 4


@pytest.mark.parametrize(
    (
        "correlation_id",
        "dispatch_key",
        "last_sequence",
    ),
    [
        (None, None, None),
        ("", "", 0),
        (str(uuid4()), None, 3),
        (None, str(uuid4()), 2),
    ],
)
def test_upgrade_repairs_partial_partner_metadata(
    sqlite_engine: Engine,
    correlation_id: str | None,
    dispatch_key: str | None,
    last_sequence: int | None,
):
    create_partially_upgraded_execution_table(sqlite_engine)

    execution_id = str(uuid4())

    insert_execution(
        sqlite_engine,
        execution_id=execution_id,
        correlation_id=correlation_id,
        dispatch_idempotency_key=dispatch_key,
        last_partner_sequence=last_sequence,
        include_partner_columns=True,
    )

    result = upgrade_pillar14_partner_execution_schema(sqlite_engine)

    assert result.execution_rows_backfilled == 1

    row = read_execution_rows(sqlite_engine)[0]

    assert_uuid_string(row["correlation_id"])
    assert_uuid_string(row["dispatch_idempotency_key"])
    assert row["last_partner_sequence"] == (
        0 if last_sequence is None else last_sequence
    )

    if correlation_id:
        assert row["correlation_id"] == correlation_id

    if dispatch_key:
        assert row["dispatch_idempotency_key"] == dispatch_key


def test_upgrade_is_idempotent_and_does_not_replace_identifiers(
    sqlite_engine: Engine,
):
    create_legacy_execution_table(sqlite_engine)
    execution_id = str(uuid4())

    insert_execution(
        sqlite_engine,
        execution_id=execution_id,
    )

    first_result = upgrade_pillar14_partner_execution_schema(sqlite_engine)
    first_row = read_execution_rows(sqlite_engine)[0]

    second_result = upgrade_pillar14_partner_execution_schema(sqlite_engine)
    second_row = read_execution_rows(sqlite_engine)[0]

    assert first_result.execution_rows_backfilled == 1
    assert first_result.partner_update_table_created is True
    assert second_result.execution_rows_backfilled == 0
    assert second_result.partner_update_table_created is False
    assert second_row == first_row

    index_names = [
        index["name"]
        for index in inspect(sqlite_engine).get_indexes("execution_requests")
    ]

    assert index_names.count("uq_execution_requests_correlation_id") == 1
    assert index_names.count("uq_execution_requests_dispatch_idempotency_key") == 1
    assert index_names.count("ix_execution_requests_partner_state") == 1


def test_upgrade_rejects_invalid_negative_sequence(
    sqlite_engine: Engine,
):
    create_partially_upgraded_execution_table(sqlite_engine)

    insert_execution(
        sqlite_engine,
        execution_id=str(uuid4()),
        correlation_id=str(uuid4()),
        dispatch_idempotency_key=str(uuid4()),
        last_partner_sequence=-1,
        include_partner_columns=True,
    )

    with pytest.raises(
        Pillar14SchemaUpgradeError,
        match="invalid Pillar 14 partner-integration metadata",
    ):
        upgrade_pillar14_partner_execution_schema(sqlite_engine)


def test_upgrade_rejects_duplicate_existing_correlation_ids(
    sqlite_engine: Engine,
):
    create_partially_upgraded_execution_table(sqlite_engine)

    duplicate_correlation_id = str(uuid4())

    insert_execution(
        sqlite_engine,
        execution_id=str(uuid4()),
        correlation_id=duplicate_correlation_id,
        dispatch_idempotency_key=str(uuid4()),
        last_partner_sequence=0,
        include_partner_columns=True,
    )
    insert_execution(
        sqlite_engine,
        execution_id=str(uuid4()),
        correlation_id=duplicate_correlation_id,
        dispatch_idempotency_key=str(uuid4()),
        last_partner_sequence=0,
        include_partner_columns=True,
    )

    with pytest.raises(
        Pillar14SchemaUpgradeError,
        match="schema upgrade failed",
    ):
        upgrade_pillar14_partner_execution_schema(sqlite_engine)


def test_upgrade_does_not_modify_source_code_or_status(
    sqlite_engine: Engine,
):
    create_legacy_execution_table(sqlite_engine)

    execution_id = str(uuid4())

    insert_execution(
        sqlite_engine,
        execution_id=execution_id,
        status_value="completed",
        source_code="print('preserve exactly')\n",
    )

    upgrade_pillar14_partner_execution_schema(sqlite_engine)

    row = read_execution_rows(sqlite_engine)[0]

    assert row["status"] == "completed"
    assert row["source_code"] == ("print('preserve exactly')\n")
