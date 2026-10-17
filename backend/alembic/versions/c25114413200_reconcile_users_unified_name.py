"""reconcile_users_unified_name

Revision ID: c25114413200
Revises: 7a1b8c2d3e4f
Create Date: 2026-10-17 12:00:00.000000+00:00

DRAFT FOR REVIEW - NOT APPLIED ANYWHERE.
Read docs/remediation/users-name-schema-drift.md before running it.

Some databases (confirmed: the local development PostgreSQL) carry legacy
users.first_name / users.last_name NOT NULL and users.middle_name columns that
no migration in this chain creates. They came from an earlier, since-reverted
body of c5d2f62cc22e (see backend/write_migration.py). The ORM only writes the
unified `name` column, so every user insert on those databases fails with
NotNullViolation on first_name.

This migration brings `users` back in line with
app.models.domain_models.User (`name = Column(String(150), nullable=False)`).
Every step checks information_schema first, so it is a no-op on a database
that never drifted and safe to run more than once:

1. make first_name / middle_name / last_name nullable, if present;
2. add `name` if it is missing (the state the reverted migration left);
3. backfill `name` from the legacy columns where it is NULL or blank;
4. stop with an error if any row still has no name (no placeholder is made up);
5. bring `name` to VARCHAR(150) when the stored values fit;
6. make `name` NOT NULL.

The legacy columns are kept. Dropping them is an explicit, commented option
below, to be enabled only after the production schema has been checked and
backed up.

Offline mode (`alembic upgrade ... --sql`) is refused with a clear error,
because there is no live schema to inspect.
"""
import logging
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c25114413200'
down_revision: Union[str, Sequence[str], None] = '7a1b8c2d3e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


log = logging.getLogger("alembic.runtime.migration")

# Same order User.__init__ uses when it builds `name` from split parts.
LEGACY_NAME_COLUMNS = ("first_name", "middle_name", "last_name")
# Matches User.name = Column(String(150), nullable=False) and the baseline.
NAME_LENGTH = 150


def _require_online(direction: str) -> None:
    # Checked before anything else, including the dialect: offline (--sql)
    # mode has no live connection, and every step here depends on what the
    # live schema contains, so a rendered script would be wrong or empty.
    if context.is_offline_mode():
        raise RuntimeError(
            f"c25114413200 ({direction}) cannot run in offline (--sql) mode: it "
            "inspects the live users table to decide what to change. Run it "
            "online (`alembic upgrade head`). To review what it would do, run the "
            "read-only SQL check in docs/remediation/users-name-schema-drift.md."
        )


def _users_columns(bind) -> dict[str, dict]:
    rows = bind.execute(
        sa.text(
            """
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'users'
            """
        )
    ).mappings()
    return {
        row["column_name"]: {
            "data_type": row["data_type"],
            "nullable": row["is_nullable"] == "YES",
            "length": row["character_maximum_length"],
        }
        for row in rows
    }


def _legacy_full_name_sql(legacy_columns: list[str]) -> str:
    # concat_ws skips NULLs, and NULLIF turns blank parts into NULLs, so the
    # result has single spaces and no leading or trailing ones.
    parts = ", ".join(f"NULLIF(btrim({column}), '')" for column in legacy_columns)
    return f"concat_ws(' ', {parts})"


def upgrade() -> None:
    _require_online("upgrade")
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # The drift is only known on PostgreSQL. SQLite databases in this
        # project are built from the ORM metadata, which already matches.
        log.info("c25114413200: not PostgreSQL, nothing to reconcile")
        return

    columns = _users_columns(bind)
    if not columns:
        raise RuntimeError("c25114413200: table 'users' not found in the current schema")

    # Fail fast instead of queueing behind long transactions on `users`.
    # SET LOCAL ends with the migration transaction.
    op.execute("SET LOCAL lock_timeout = '10s'")

    legacy_columns = [column for column in LEGACY_NAME_COLUMNS if column in columns]

    # 1. Legacy columns must stop blocking ORM inserts, which never set them.
    for column in legacy_columns:
        if not columns[column]["nullable"]:
            log.info("c25114413200: users.%s -> nullable", column)
            op.alter_column("users", column, nullable=True)

    # 2. The reverted migration dropped `name`; bring it back if it is gone.
    if "name" not in columns:
        log.info("c25114413200: adding users.name")
        op.add_column(
            "users",
            sa.Column("name", sa.String(length=NAME_LENGTH), nullable=True),
        )
        columns = _users_columns(bind)

    # 3. Backfill `name` from the legacy parts where it is NULL or blank.
    if legacy_columns:
        full_name = _legacy_full_name_sql(legacy_columns)
        needs_name = f"(name IS NULL OR btrim(name) = '') AND {full_name} <> ''"

        name_length = columns["name"]["length"]
        if name_length is not None:
            too_long = bind.execute(
                sa.text(
                    f"SELECT user_id FROM users "
                    f"WHERE {needs_name} AND length({full_name}) > :limit "
                    f"ORDER BY user_id LIMIT 20"
                ),
                {"limit": name_length},
            ).scalars().all()
            if too_long:
                raise RuntimeError(
                    "c25114413200: the joined legacy name is longer than "
                    f"users.name ({name_length}) for user_id {too_long}. "
                    "Fix those rows by hand; nothing was changed."
                )

        result = bind.execute(
            sa.text(f"UPDATE users SET name = {full_name} WHERE {needs_name}")
        )
        log.info("c25114413200: backfilled users.name on %s row(s)", result.rowcount)

    # 4. No invented names: stop if a row still has none.
    missing = bind.execute(
        sa.text("SELECT user_id FROM users WHERE name IS NULL ORDER BY user_id LIMIT 20")
    ).scalars().all()
    if missing:
        raise RuntimeError(
            "c25114413200: users.name is still NULL for user_id "
            f"{missing} (and no legacy name parts to build it from). "
            "Set those names by hand; nothing was changed."
        )
    blank = bind.execute(
        sa.text("SELECT count(*) FROM users WHERE btrim(name) = ''")
    ).scalar_one()
    if blank:
        log.warning("c25114413200: %s user(s) have a blank users.name", blank)

    # 5. Match the ORM length, but never cut stored data.
    name_column = columns["name"]
    if name_column["data_type"] != "character varying" or name_column["length"] != NAME_LENGTH:
        longest = bind.execute(
            sa.text("SELECT coalesce(max(length(name)), 0) FROM users")
        ).scalar_one()
        if longest <= NAME_LENGTH:
            log.info(
                "c25114413200: users.name %s(%s) -> VARCHAR(%s)",
                name_column["data_type"], name_column["length"], NAME_LENGTH,
            )
            op.alter_column(
                "users",
                "name",
                type_=sa.String(length=NAME_LENGTH),
                existing_nullable=True,
            )
        else:
            log.warning(
                "c25114413200: users.name kept as %s(%s); longest value is %s characters",
                name_column["data_type"], name_column["length"], longest,
            )

    # 6. The ORM requires a name.
    if columns["name"]["nullable"]:
        log.info("c25114413200: users.name -> NOT NULL")
        op.alter_column("users", "name", nullable=False)

    # OPTIONAL, DESTRUCTIVE - keep commented until production has been
    # checked and backed up (see the note). The legacy values are lost for
    # good; the downgrade below cannot bring them back.
    # for column in legacy_columns:
    #     op.drop_column("users", column)


def downgrade() -> None:
    # Safe by design: removes no column, loses no data, and does not bring
    # back the NOT NULL constraints that broke user inserts.
    #
    # `name` stays NOT NULL: that is what every revision up to 7a1b8c2d3e4f
    # declares (baseline 18d3ef8f020d creates name VARCHAR(150) NOT NULL),
    # so it is the correct state to return to. The upgrade does not record
    # whether a database had drifted, so it cannot restore a drifted state
    # exactly, and should not.
    _require_online("downgrade")
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    columns = _users_columns(bind)
    if "name" not in columns:
        return

    op.execute("SET LOCAL lock_timeout = '10s'")

    # Rows created after the upgrade have NULL legacy parts. Fill them from
    # `name` the same way the User.first_name / User.last_name properties
    # split it, so code that still reads the legacy columns sees values.
    # Values are cut to the column length; `name` keeps the full text.
    words = "regexp_split_to_array(btrim(name), '\\s+')"
    legacy_parts = {
        "first_name": f"({words})[1]",
        "last_name": f"array_to_string(({words})[2:], ' ')",
    }
    for column, expression in legacy_parts.items():
        if column not in columns:
            continue
        length = columns[column]["length"]
        value = f"left({expression}, {int(length)})" if length else expression
        op.execute(
            f"UPDATE users SET {column} = coalesce({value}, '') "
            f"WHERE {column} IS NULL AND name IS NOT NULL"
        )

    # OPTIONAL - only if the legacy columns were dropped in upgrade() and old
    # code that needs them is being restored. The original split values
    # cannot be recovered; they are rebuilt from `name` as above.
    # op.add_column("users", sa.Column("first_name", sa.String(100), nullable=True))
    # op.add_column("users", sa.Column("middle_name", sa.String(100), nullable=True))
    # op.add_column("users", sa.Column("last_name", sa.String(100), nullable=True))
    # (then run the UPDATEs above)
    #
    # OPTIONAL - NOT RECOMMENDED: re-imposing NOT NULL on the legacy columns
    # makes every ORM user insert fail again.
    # op.alter_column("users", "first_name", nullable=False)
    # op.alter_column("users", "last_name", nullable=False)
