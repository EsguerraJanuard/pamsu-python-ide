from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine

from app.core.database import engine
from app.models.domain_models import (
    PartnerExecutionUpdateRecord,
)


EXECUTION_REQUESTS_TABLE = "execution_requests"
PARTNER_UPDATES_TABLE = "partner_execution_updates"

SUPPORTED_DIALECTS = {
    "postgresql",
    "sqlite",
}

REQUIRED_EXECUTION_COLUMNS = {
    "correlation_id",
    "dispatch_idempotency_key",
    "last_partner_sequence",
}


class Pillar14SchemaUpgradeError(RuntimeError):
    """Raised when the explicit Pillar 14 schema upgrade cannot complete."""


@dataclass(frozen=True)
class Pillar14SchemaUpgradeResult:
    dialect: str
    execution_rows_backfilled: int
    partner_update_table_created: bool


def _table_names(
    connection: Connection,
) -> set[str]:
    return set(inspect(connection).get_table_names())


def _column_names(
    connection: Connection,
    table_name: str,
) -> set[str]:
    return {
        str(column["name"])
        for column in inspect(connection).get_columns(
            table_name,
        )
    }


def _check_constraint_names(
    connection: Connection,
    table_name: str,
) -> set[str]:
    return {
        str(constraint["name"])
        for constraint in inspect(connection).get_check_constraints(table_name)
        if constraint.get("name")
    }


def _ensure_supported_dialect(
    connection: Connection,
) -> str:
    dialect = connection.dialect.name

    if dialect not in SUPPORTED_DIALECTS:
        raise Pillar14SchemaUpgradeError(
            "The Pillar 14 schema upgrade supports only PostgreSQL "
            "and SQLite development databases."
        )

    return dialect


def _ensure_execution_requests_table(
    connection: Connection,
) -> None:
    if EXECUTION_REQUESTS_TABLE not in _table_names(connection):
        raise Pillar14SchemaUpgradeError(
            "The execution_requests table does not exist. Initialize "
            "the base application schema before running the Pillar 14 "
            "upgrade."
        )


def _add_missing_execution_columns(
    connection: Connection,
) -> None:
    existing_columns = _column_names(
        connection,
        EXECUTION_REQUESTS_TABLE,
    )

    if "correlation_id" not in existing_columns:
        connection.execute(
            text("ALTER TABLE execution_requests ADD COLUMN correlation_id VARCHAR(36)")
        )

    if "dispatch_idempotency_key" not in existing_columns:
        connection.execute(
            text(
                "ALTER TABLE execution_requests "
                "ADD COLUMN dispatch_idempotency_key VARCHAR(36)"
            )
        )

    if "last_partner_sequence" not in existing_columns:
        connection.execute(
            text(
                "ALTER TABLE execution_requests "
                "ADD COLUMN last_partner_sequence "
                "INTEGER NOT NULL DEFAULT 0"
            )
        )


def _backfill_execution_partner_identity(
    connection: Connection,
) -> int:
    rows = list(
        connection.execute(
            text(
                "SELECT execution_id, correlation_id, "
                "dispatch_idempotency_key, last_partner_sequence "
                "FROM execution_requests"
            )
        ).mappings()
    )

    backfilled_rows = 0

    for row in rows:
        correlation_id = row["correlation_id"]
        dispatch_key = row["dispatch_idempotency_key"]
        last_sequence = row["last_partner_sequence"]

        if correlation_id and dispatch_key and last_sequence is not None:
            continue

        connection.execute(
            text(
                "UPDATE execution_requests "
                "SET correlation_id = :correlation_id, "
                "dispatch_idempotency_key = "
                ":dispatch_idempotency_key, "
                "last_partner_sequence = "
                ":last_partner_sequence "
                "WHERE execution_id = :execution_id"
            ),
            {
                "execution_id": row["execution_id"],
                "correlation_id": (correlation_id or str(uuid4())),
                "dispatch_idempotency_key": (dispatch_key or str(uuid4())),
                "last_partner_sequence": (
                    0 if last_sequence is None else last_sequence
                ),
            },
        )

        backfilled_rows += 1

    return backfilled_rows


def _enforce_postgresql_execution_constraints(
    connection: Connection,
) -> None:
    if connection.dialect.name != "postgresql":
        return

    connection.execute(
        text("ALTER TABLE execution_requests ALTER COLUMN correlation_id SET NOT NULL")
    )
    connection.execute(
        text(
            "ALTER TABLE execution_requests "
            "ALTER COLUMN dispatch_idempotency_key SET NOT NULL"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE execution_requests "
            "ALTER COLUMN last_partner_sequence "
            "SET DEFAULT 0"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE execution_requests "
            "ALTER COLUMN last_partner_sequence SET NOT NULL"
        )
    )

    constraint_names = _check_constraint_names(
        connection,
        EXECUTION_REQUESTS_TABLE,
    )

    if "ck_execution_last_partner_sequence" not in constraint_names:
        connection.execute(
            text(
                "ALTER TABLE execution_requests "
                "ADD CONSTRAINT "
                "ck_execution_last_partner_sequence "
                "CHECK (last_partner_sequence >= 0)"
            )
        )


def _create_execution_partner_indexes(
    connection: Connection,
) -> None:
    connection.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "uq_execution_requests_correlation_id "
            "ON execution_requests (correlation_id)"
        )
    )
    connection.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "uq_execution_requests_dispatch_idempotency_key "
            "ON execution_requests "
            "(dispatch_idempotency_key)"
        )
    )
    connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS "
            "ix_execution_requests_partner_state "
            "ON execution_requests "
            "(status, last_partner_sequence)"
        )
    )


def _create_partner_update_table(
    connection: Connection,
) -> bool:
    table_exists_before = PARTNER_UPDATES_TABLE in _table_names(connection)

    PartnerExecutionUpdateRecord.__table__.create(
        bind=connection,
        checkfirst=True,
    )

    return not table_exists_before


def _verify_upgrade(
    connection: Connection,
) -> None:
    table_names = _table_names(connection)

    if PARTNER_UPDATES_TABLE not in table_names:
        raise Pillar14SchemaUpgradeError(
            "The partner_execution_updates table was not created."
        )

    execution_columns = _column_names(
        connection,
        EXECUTION_REQUESTS_TABLE,
    )

    missing_columns = REQUIRED_EXECUTION_COLUMNS - execution_columns

    if missing_columns:
        raise Pillar14SchemaUpgradeError(
            "The execution_requests table is missing Pillar 14 "
            f"columns: {sorted(missing_columns)}"
        )

    invalid_row_count = connection.execute(
        text(
            "SELECT COUNT(*) "
            "FROM execution_requests "
            "WHERE correlation_id IS NULL "
            "OR correlation_id = '' "
            "OR dispatch_idempotency_key IS NULL "
            "OR dispatch_idempotency_key = '' "
            "OR last_partner_sequence IS NULL "
            "OR last_partner_sequence < 0"
        )
    ).scalar_one()

    if invalid_row_count:
        raise Pillar14SchemaUpgradeError(
            "One or more execution requests have invalid Pillar 14 "
            "partner-integration metadata."
        )

    duplicate_correlation_count = connection.execute(
        text(
            "SELECT COUNT(*) FROM ("
            "SELECT correlation_id "
            "FROM execution_requests "
            "GROUP BY correlation_id "
            "HAVING COUNT(*) > 1"
            ") AS duplicate_correlations"
        )
    ).scalar_one()

    if duplicate_correlation_count:
        raise Pillar14SchemaUpgradeError(
            "Duplicate execution correlation IDs remain after upgrade."
        )

    duplicate_dispatch_count = connection.execute(
        text(
            "SELECT COUNT(*) FROM ("
            "SELECT dispatch_idempotency_key "
            "FROM execution_requests "
            "GROUP BY dispatch_idempotency_key "
            "HAVING COUNT(*) > 1"
            ") AS duplicate_dispatch_keys"
        )
    ).scalar_one()

    if duplicate_dispatch_count:
        raise Pillar14SchemaUpgradeError(
            "Duplicate execution dispatch idempotency keys remain after upgrade."
        )


def upgrade_pillar14_partner_execution_schema(
    database_engine: Engine = engine,
) -> Pillar14SchemaUpgradeResult:
    """
    Explicitly upgrade an existing database for Pillar 14.

    This function is intentionally not called during application import or
    startup. Operators must run it as a deliberate deployment step so schema
    changes do not occur unexpectedly while the API is serving requests.
    """

    try:
        with database_engine.begin() as connection:
            dialect = _ensure_supported_dialect(connection)
            _ensure_execution_requests_table(connection)
            _add_missing_execution_columns(connection)
            backfilled_rows = _backfill_execution_partner_identity(connection)
            _enforce_postgresql_execution_constraints(connection)
            _create_execution_partner_indexes(connection)
            partner_table_created = _create_partner_update_table(connection)
            _verify_upgrade(connection)

            return Pillar14SchemaUpgradeResult(
                dialect=dialect,
                execution_rows_backfilled=(backfilled_rows),
                partner_update_table_created=(partner_table_created),
            )
    except Pillar14SchemaUpgradeError:
        raise
    except Exception as error:
        raise Pillar14SchemaUpgradeError(
            "The Pillar 14 partner-execution schema upgrade failed."
        ) from error


def main() -> None:
    result = upgrade_pillar14_partner_execution_schema()

    print("Pillar 14 partner-execution schema upgrade completed.")
    print(f"Database dialect: {result.dialect}")
    print(f"Execution rows backfilled: {result.execution_rows_backfilled}")
    print(f"Partner-update table created: {result.partner_update_table_created}")


if __name__ == "__main__":
    main()


# DEPLOYMENT BOUNDARY:
# Run this module explicitly before starting a Pillar 14 deployment against
# an existing database. Do not invoke it automatically from FastAPI startup.

# IDEMPOTENCY BOUNDARY:
# Re-running the upgrade does not replace existing partner identifiers,
# recreate existing tables, or duplicate indexes.

# PRIVACY BOUNDARY:
# The upgrade stores only backend-generated UUIDs and lifecycle sequencing
# metadata. It does not copy source code, standard input, execution output,
# credentials, OTPs, grades, analytics, telemetry, or misconduct conclusions.
