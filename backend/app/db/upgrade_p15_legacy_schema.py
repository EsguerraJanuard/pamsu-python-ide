from __future__ import annotations

import argparse
from collections.abc import Iterable

from sqlalchemy import Connection, inspect, text

from app.core.database import engine


EXPECTED_DATABASE = "pamsu_ide_db"
EXPECTED_DIALECT = "postgresql"
ADVISORY_LOCK_KEY = 150015

REQUIRED_TABLES = {
    "users",
    "classrooms",
    "tasks",
    "coding_sessions",
    "submissions",
    "behavioral_logs",
    "execution_requests",
}

CURRENT_COLUMNS = {
    "users": {
        "school_id",
        "email",
        "email_verified",
        "is_active",
        "created_at",
        "updated_at",
    },
    "tasks": {
        "class_id",
        "description",
        "instructions",
        "activity_type",
        "starter_code",
        "paste_policy",
        "is_graded",
        "is_published",
        "due_at",
        "published_at",
        "created_at",
        "updated_at",
    },
    "submissions": {
        "coding_session_id",
        "attempt_number",
        "standard_input",
        "status",
        "is_official",
        "submitted_at",
        "accepted_at",
    },
    "behavioral_logs": {
        "blocked_paste_count",
        "run_attempt_count",
        "idle_duration_seconds",
        "last_blocked_paste_at",
        "created_at",
        "updated_at",
    },
}


class UpgradeError(RuntimeError):
    """Raised when the legacy-schema upgrade cannot proceed safely."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect or align the local pre-Alembic PAMSU development "
            "database with the current SQLAlchemy baseline."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply the guarded transactional upgrade. "
            "Without this flag, the command is read-only."
        ),
    )
    return parser.parse_args()


def scalar(
    connection: Connection,
    statement: str,
) -> int:
    value = connection.execute(text(statement)).scalar_one()

    return int(value)


def run(
    connection: Connection,
    statements: Iterable[str],
) -> None:
    for statement in statements:
        connection.execute(text(statement))


def check_database() -> None:
    actual_dialect = engine.dialect.name
    actual_database = engine.url.database

    if actual_dialect != EXPECTED_DIALECT:
        raise UpgradeError(
            "Upgrade blocked: expected PostgreSQL, "
            f"but connected through {actual_dialect!r}."
        )

    if actual_database != EXPECTED_DATABASE:
        raise UpgradeError(
            "Upgrade blocked: expected database "
            f"{EXPECTED_DATABASE!r}, but connected to "
            f"{actual_database!r}."
        )


def inspect_state() -> int:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    missing_tables = sorted(REQUIRED_TABLES - tables)

    if missing_tables:
        raise UpgradeError(
            "Upgrade blocked because required tables "
            "are missing: " + ", ".join(missing_tables)
        )

    missing_columns: dict[str, list[str]] = {}

    for table_name, expected_columns in CURRENT_COLUMNS.items():
        actual_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }

        missing = sorted(expected_columns - actual_columns)

        if missing:
            missing_columns[table_name] = missing

    with engine.connect() as connection:
        counts = {
            table_name: scalar(
                connection,
                f'SELECT COUNT(*) FROM "{table_name}"',
            )
            for table_name in (
                "users",
                "tasks",
                "submissions",
                "behavioral_logs",
                "execution_requests",
            )
        }

    missing_count = sum(len(columns) for columns in missing_columns.values())

    print("=== PILLAR 15 LEGACY SCHEMA INSPECTION ===")
    print(f"Database: {engine.url.database}")
    print(f"Dialect: {engine.dialect.name}")

    for table_name, count in counts.items():
        print(f"{table_name}: {count} row(s)")

    print(f"Missing current columns: {missing_count}")

    for table_name in sorted(missing_columns):
        print(f"- {table_name}: " + ", ".join(missing_columns[table_name]))

    if not missing_columns:
        print("All current columns are already present.")

    return missing_count


def preflight(
    connection: Connection,
) -> None:
    checks = (
        (
            """
            SELECT COUNT(*)
            FROM users
            WHERE role NOT IN (
                'student',
                'instructor'
            )
            """,
            "users contains unsupported role values",
        ),
        (
            """
            SELECT COUNT(*)
            FROM users
            WHERE user_id < 0
               OR user_id > 999999999
            """,
            ("a user ID cannot be converted into a 10-digit placeholder school ID"),
        ),
        (
            """
            SELECT COUNT(*)
            FROM tasks AS task
            LEFT JOIN users AS instructor
              ON instructor.user_id =
                 task.instructor_id
            WHERE instructor.user_id IS NULL
            """,
            "a task references a missing user",
        ),
        (
            """
            SELECT COUNT(*)
            FROM submissions AS submission
            LEFT JOIN users AS student
              ON student.user_id =
                 submission.student_id
            LEFT JOIN tasks AS task
              ON task.task_id =
                 submission.task_id
            WHERE student.user_id IS NULL
               OR task.task_id IS NULL
            """,
            ("a submission has a broken student or task reference"),
        ),
        (
            """
            SELECT COUNT(*)
            FROM behavioral_logs AS log
            LEFT JOIN submissions AS submission
              ON submission.sub_id = log.sub_id
            WHERE submission.sub_id IS NULL
            """,
            ("a behavioral log references a missing submission"),
        ),
    )

    for statement, message in checks:
        if scalar(
            connection,
            statement,
        ):
            raise UpgradeError(f"Upgrade blocked: {message}.")


def upgrade_users(
    connection: Connection,
) -> None:
    run(
        connection,
        (
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS
            school_id VARCHAR(10)
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS
            email VARCHAR(255)
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS
            email_verified BOOLEAN
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS
            is_active BOOLEAN
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS
            created_at TIMESTAMP WITH TIME ZONE
            DEFAULT now()
            """,
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS
            updated_at TIMESTAMP WITH TIME ZONE
            DEFAULT now()
            """,
            """
            UPDATE users
            SET school_id =
                '9' ||
                lpad(
                    user_id::text,
                    9,
                    '0'
                )
            WHERE school_id IS NULL
               OR btrim(school_id) = ''
            """,
            """
            UPDATE users
            SET email =
                'legacy+' ||
                user_id::text ||
                '@pampangastateu.edu.ph'
            WHERE email IS NULL
               OR btrim(email) = ''
            """,
            """
            UPDATE users
            SET email_verified = TRUE
            WHERE email_verified IS NULL
            """,
            """
            UPDATE users
            SET is_active = TRUE
            WHERE is_active IS NULL
            """,
            """
            UPDATE users
            SET created_at = now()
            WHERE created_at IS NULL
            """,
            """
            UPDATE users
            SET updated_at = now()
            WHERE updated_at IS NULL
            """,
        ),
    )

    validations = (
        (
            """
            SELECT COUNT(*)
            FROM users
            WHERE school_id !~ '^[0-9]{10}$'
            """,
            ("invalid school IDs remain after backfill"),
        ),
        (
            """
            SELECT COUNT(*)
            FROM (
                SELECT school_id
                FROM users
                GROUP BY school_id
                HAVING COUNT(*) > 1
            ) AS duplicate_school_ids
            """,
            ("duplicate school IDs remain after backfill"),
        ),
        (
            """
            SELECT COUNT(*)
            FROM (
                SELECT lower(email)
                FROM users
                GROUP BY lower(email)
                HAVING COUNT(*) > 1
            ) AS duplicate_emails
            """,
            ("duplicate emails remain after backfill"),
        ),
    )

    for statement, message in validations:
        if scalar(
            connection,
            statement,
        ):
            raise UpgradeError(f"Upgrade blocked: {message}.")

    run(
        connection,
        (
            """
            ALTER TABLE users
            ALTER COLUMN school_id SET NOT NULL
            """,
            """
            ALTER TABLE users
            ALTER COLUMN email SET NOT NULL
            """,
            """
            ALTER TABLE users
            ALTER COLUMN email_verified SET NOT NULL
            """,
            """
            ALTER TABLE users
            ALTER COLUMN is_active SET NOT NULL
            """,
            """
            ALTER TABLE users
            ALTER COLUMN created_at SET NOT NULL
            """,
            """
            ALTER TABLE users
            ALTER COLUMN updated_at SET NOT NULL
            """,
            """
            ALTER TABLE users
            DROP CONSTRAINT IF EXISTS
            ck_users_role
            """,
            """
            ALTER TABLE users
            ADD CONSTRAINT ck_users_role
            CHECK (
                role IN (
                    'student',
                    'instructor'
                )
            )
            """,
            """
            ALTER TABLE users
            DROP CONSTRAINT IF EXISTS
            ck_users_school_id_length
            """,
            """
            ALTER TABLE users
            ADD CONSTRAINT
            ck_users_school_id_length
            CHECK (
                length(school_id) = 10
            )
            """,
            """
            DROP INDEX IF EXISTS
            ix_users_email
            """,
            """
            CREATE UNIQUE INDEX
            ix_users_email
            ON users (email)
            """,
            """
            DROP INDEX IF EXISTS
            ix_users_school_id
            """,
            """
            CREATE UNIQUE INDEX
            ix_users_school_id
            ON users (school_id)
            """,
        ),
    )


def upgrade_tasks(
    connection: Connection,
) -> None:
    run(
        connection,
        (
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            class_id INTEGER
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            description TEXT
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            instructions TEXT
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            activity_type VARCHAR(20)
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            starter_code TEXT
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            paste_policy VARCHAR(20)
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            is_graded BOOLEAN
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            is_published BOOLEAN
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            due_at TIMESTAMP WITH TIME ZONE
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            published_at TIMESTAMP WITH TIME ZONE
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            created_at TIMESTAMP WITH TIME ZONE
            DEFAULT now()
            """,
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS
            updated_at TIMESTAMP WITH TIME ZONE
            DEFAULT now()
            """,
            """
            UPDATE tasks
            SET activity_type = 'laboratory'
            WHERE activity_type IS NULL
               OR btrim(activity_type) = ''
            """,
            """
            UPDATE tasks
            SET starter_code = ''
            WHERE starter_code IS NULL
            """,
            """
            UPDATE tasks
            SET paste_policy = 'internal_only'
            WHERE paste_policy IS NULL
               OR btrim(paste_policy) = ''
            """,
            """
            UPDATE tasks
            SET is_graded = TRUE
            WHERE is_graded IS NULL
            """,
            """
            UPDATE tasks
            SET is_published = FALSE
            WHERE is_published IS NULL
            """,
            """
            UPDATE tasks
            SET created_at = now()
            WHERE created_at IS NULL
            """,
            """
            UPDATE tasks
            SET updated_at = now()
            WHERE updated_at IS NULL
            """,
            """
            ALTER TABLE tasks
            ALTER COLUMN activity_type
            SET NOT NULL
            """,
            """
            ALTER TABLE tasks
            ALTER COLUMN starter_code
            SET NOT NULL
            """,
            """
            ALTER TABLE tasks
            ALTER COLUMN paste_policy
            SET NOT NULL
            """,
            """
            ALTER TABLE tasks
            ALTER COLUMN is_graded
            SET NOT NULL
            """,
            """
            ALTER TABLE tasks
            ALTER COLUMN is_published
            SET NOT NULL
            """,
            """
            ALTER TABLE tasks
            ALTER COLUMN created_at
            SET NOT NULL
            """,
            """
            ALTER TABLE tasks
            ALTER COLUMN updated_at
            SET NOT NULL
            """,
            """
            ALTER TABLE tasks
            DROP CONSTRAINT IF EXISTS
            ck_tasks_activity_type
            """,
            """
            ALTER TABLE tasks
            ADD CONSTRAINT
            ck_tasks_activity_type
            CHECK (
                activity_type IN (
                    'laboratory',
                    'homework'
                )
            )
            """,
            """
            ALTER TABLE tasks
            DROP CONSTRAINT IF EXISTS
            ck_tasks_paste_policy
            """,
            """
            ALTER TABLE tasks
            ADD CONSTRAINT
            ck_tasks_paste_policy
            CHECK (
                paste_policy IN (
                    'internal_only',
                    'disabled'
                )
            )
            """,
            """
            ALTER TABLE tasks
            DROP CONSTRAINT IF EXISTS
            tasks_instructor_id_fkey
            """,
            """
            ALTER TABLE tasks
            ADD CONSTRAINT
            tasks_instructor_id_fkey
            FOREIGN KEY (instructor_id)
            REFERENCES users(user_id)
            ON DELETE RESTRICT
            """,
            """
            ALTER TABLE tasks
            DROP CONSTRAINT IF EXISTS
            tasks_class_id_fkey
            """,
            """
            ALTER TABLE tasks
            ADD CONSTRAINT
            tasks_class_id_fkey
            FOREIGN KEY (class_id)
            REFERENCES classrooms(class_id)
            ON DELETE RESTRICT
            """,
            """
            CREATE INDEX IF NOT EXISTS
            ix_tasks_class_id
            ON tasks (class_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS
            ix_tasks_instructor_id
            ON tasks (instructor_id)
            """,
        ),
    )


def upgrade_submissions(
    connection: Connection,
) -> None:
    run(
        connection,
        (
            """
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS
            coding_session_id VARCHAR(36)
            """,
            """
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS
            attempt_number INTEGER
            """,
            """
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS
            standard_input TEXT
            """,
            """
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS
            status VARCHAR(30)
            """,
            """
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS
            is_official BOOLEAN
            """,
            """
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS
            submitted_at TIMESTAMP WITH TIME ZONE
            DEFAULT now()
            """,
            """
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS
            accepted_at TIMESTAMP WITH TIME ZONE
            """,
            """
            WITH ranked AS (
                SELECT
                    sub_id,
                    row_number() OVER (
                        PARTITION BY
                            student_id,
                            task_id
                        ORDER BY sub_id
                    )::integer
                    AS attempt_number,
                    (
                        row_number() OVER (
                            PARTITION BY
                                student_id,
                                task_id
                            ORDER BY sub_id DESC
                        ) = 1
                    ) AS is_official
                FROM submissions
            )
            UPDATE submissions AS submission
            SET
                attempt_number = COALESCE(
                    submission.attempt_number,
                    ranked.attempt_number
                ),
                is_official = COALESCE(
                    submission.is_official,
                    ranked.is_official
                )
            FROM ranked
            WHERE ranked.sub_id =
                  submission.sub_id
            """,
            """
            UPDATE submissions
            SET standard_input = ''
            WHERE standard_input IS NULL
            """,
            """
            UPDATE submissions
            SET status = 'awaiting_review'
            WHERE status IS NULL
               OR btrim(status) = ''
            """,
            """
            UPDATE submissions
            SET submitted_at = now()
            WHERE submitted_at IS NULL
            """,
            """
            UPDATE submissions
            SET accepted_at = submitted_at
            WHERE accepted_at IS NULL
            """,
        ),
    )

    duplicate_attempt_count = scalar(
        connection,
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                student_id,
                task_id,
                attempt_number
            FROM submissions
            GROUP BY
                student_id,
                task_id,
                attempt_number
            HAVING COUNT(*) > 1
        ) AS duplicate_attempts
        """,
    )

    if duplicate_attempt_count:
        raise UpgradeError(
            "Upgrade blocked: duplicate submission "
            "attempt numbers remain after backfill."
        )

    multiple_official_count = scalar(
        connection,
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                student_id,
                task_id
            FROM submissions
            WHERE is_official IS TRUE
            GROUP BY
                student_id,
                task_id
            HAVING COUNT(*) > 1
        ) AS duplicate_officials
        """,
    )

    if multiple_official_count:
        raise UpgradeError(
            "Upgrade blocked: more than one official "
            "submission remains for a student and task."
        )

    run(
        connection,
        (
            """
            ALTER TABLE submissions
            ALTER COLUMN attempt_number
            SET NOT NULL
            """,
            """
            ALTER TABLE submissions
            ALTER COLUMN standard_input
            SET NOT NULL
            """,
            """
            ALTER TABLE submissions
            ALTER COLUMN status
            SET NOT NULL
            """,
            """
            ALTER TABLE submissions
            ALTER COLUMN is_official
            SET NOT NULL
            """,
            """
            ALTER TABLE submissions
            ALTER COLUMN submitted_at
            SET NOT NULL
            """,
            """
            ALTER TABLE submissions
            DROP CONSTRAINT IF EXISTS
            ck_submissions_status
            """,
            """
            ALTER TABLE submissions
            ADD CONSTRAINT
            ck_submissions_status
            CHECK (
                status IN (
                    'submitted',
                    'awaiting_review',
                    'graded',
                    'rejected'
                )
            )
            """,
            """
            ALTER TABLE submissions
            DROP CONSTRAINT IF EXISTS
            ck_submission_attempt_number
            """,
            """
            ALTER TABLE submissions
            ADD CONSTRAINT
            ck_submission_attempt_number
            CHECK (
                attempt_number > 0
            )
            """,
            """
            ALTER TABLE submissions
            DROP CONSTRAINT IF EXISTS
            uq_submission_attempt
            """,
            """
            ALTER TABLE submissions
            ADD CONSTRAINT
            uq_submission_attempt
            UNIQUE (
                student_id,
                task_id,
                attempt_number
            )
            """,
            """
            ALTER TABLE submissions
            DROP CONSTRAINT IF EXISTS
            submissions_student_id_fkey
            """,
            """
            ALTER TABLE submissions
            ADD CONSTRAINT
            submissions_student_id_fkey
            FOREIGN KEY (student_id)
            REFERENCES users(user_id)
            ON DELETE RESTRICT
            """,
            """
            ALTER TABLE submissions
            DROP CONSTRAINT IF EXISTS
            submissions_task_id_fkey
            """,
            """
            ALTER TABLE submissions
            ADD CONSTRAINT
            submissions_task_id_fkey
            FOREIGN KEY (task_id)
            REFERENCES tasks(task_id)
            ON DELETE RESTRICT
            """,
            """
            ALTER TABLE submissions
            DROP CONSTRAINT IF EXISTS
            submissions_coding_session_id_fkey
            """,
            """
            ALTER TABLE submissions
            ADD CONSTRAINT
            submissions_coding_session_id_fkey
            FOREIGN KEY (coding_session_id)
            REFERENCES coding_sessions(session_id)
            ON DELETE SET NULL
            """,
            """
            CREATE INDEX IF NOT EXISTS
            ix_submissions_coding_session_id
            ON submissions (coding_session_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS
            ix_submissions_student_id
            ON submissions (student_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS
            ix_submissions_student_task
            ON submissions (
                student_id,
                task_id
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS
            ix_submissions_task_id
            ON submissions (task_id)
            """,
        ),
    )


def upgrade_behavioral_logs(
    connection: Connection,
) -> None:
    run(
        connection,
        (
            """
            ALTER TABLE behavioral_logs
            ADD COLUMN IF NOT EXISTS
            blocked_paste_count INTEGER
            """,
            """
            ALTER TABLE behavioral_logs
            ADD COLUMN IF NOT EXISTS
            run_attempt_count INTEGER
            """,
            """
            ALTER TABLE behavioral_logs
            ADD COLUMN IF NOT EXISTS
            idle_duration_seconds INTEGER
            """,
            """
            ALTER TABLE behavioral_logs
            ADD COLUMN IF NOT EXISTS
            last_blocked_paste_at
            TIMESTAMP WITH TIME ZONE
            """,
            """
            ALTER TABLE behavioral_logs
            ADD COLUMN IF NOT EXISTS
            created_at TIMESTAMP WITH TIME ZONE
            DEFAULT now()
            """,
            """
            ALTER TABLE behavioral_logs
            ADD COLUMN IF NOT EXISTS
            updated_at TIMESTAMP WITH TIME ZONE
            DEFAULT now()
            """,
            """
            UPDATE behavioral_logs
            SET blocked_paste_count = 0
            WHERE blocked_paste_count IS NULL
            """,
            """
            UPDATE behavioral_logs
            SET run_attempt_count = 0
            WHERE run_attempt_count IS NULL
            """,
            """
            UPDATE behavioral_logs
            SET idle_duration_seconds = 0
            WHERE idle_duration_seconds IS NULL
            """,
            """
            UPDATE behavioral_logs
            SET created_at = now()
            WHERE created_at IS NULL
            """,
            """
            UPDATE behavioral_logs
            SET updated_at = now()
            WHERE updated_at IS NULL
            """,
            """
            ALTER TABLE behavioral_logs
            ALTER COLUMN blocked_paste_count
            SET NOT NULL
            """,
            """
            ALTER TABLE behavioral_logs
            ALTER COLUMN run_attempt_count
            SET NOT NULL
            """,
            """
            ALTER TABLE behavioral_logs
            ALTER COLUMN idle_duration_seconds
            SET NOT NULL
            """,
            """
            ALTER TABLE behavioral_logs
            ALTER COLUMN created_at
            SET NOT NULL
            """,
            """
            ALTER TABLE behavioral_logs
            ALTER COLUMN updated_at
            SET NOT NULL
            """,
            """
            ALTER TABLE behavioral_logs
            DROP CONSTRAINT IF EXISTS
            ck_logs_blocked_paste
            """,
            """
            ALTER TABLE behavioral_logs
            ADD CONSTRAINT
            ck_logs_blocked_paste
            CHECK (
                blocked_paste_count >= 0
            )
            """,
            """
            ALTER TABLE behavioral_logs
            DROP CONSTRAINT IF EXISTS
            ck_logs_run_attempts
            """,
            """
            ALTER TABLE behavioral_logs
            ADD CONSTRAINT
            ck_logs_run_attempts
            CHECK (
                run_attempt_count >= 0
            )
            """,
            """
            ALTER TABLE behavioral_logs
            DROP CONSTRAINT IF EXISTS
            ck_logs_idle_duration
            """,
            """
            ALTER TABLE behavioral_logs
            ADD CONSTRAINT
            ck_logs_idle_duration
            CHECK (
                idle_duration_seconds >= 0
            )
            """,
            """
            ALTER TABLE behavioral_logs
            DROP CONSTRAINT IF EXISTS
            ck_logs_tab_switches
            """,
            """
            ALTER TABLE behavioral_logs
            ADD CONSTRAINT
            ck_logs_tab_switches
            CHECK (
                tab_switches_count >= 0
            )
            """,
            """
            ALTER TABLE behavioral_logs
            DROP CONSTRAINT IF EXISTS
            behavioral_logs_sub_id_fkey
            """,
            """
            ALTER TABLE behavioral_logs
            ADD CONSTRAINT
            behavioral_logs_sub_id_fkey
            FOREIGN KEY (sub_id)
            REFERENCES submissions(sub_id)
            ON DELETE RESTRICT
            """,
        ),
    )


def apply_upgrade() -> None:
    with engine.begin() as connection:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {
                "lock_key": ADVISORY_LOCK_KEY,
            },
        )

        preflight(connection)
        upgrade_users(connection)
        upgrade_tasks(connection)
        upgrade_submissions(connection)
        upgrade_behavioral_logs(connection)

        connection.execute(
            text(
                "ALTER TABLE execution_requests "
                "ALTER COLUMN "
                "last_partner_sequence "
                "DROP DEFAULT"
            )
        )

    print("=== PILLAR 15 LEGACY SCHEMA UPGRADE COMPLETE ===")
    print(f"Database: {engine.url.database}")
    print("Transaction committed successfully.")
    print("No source code, passwords, tokens, or clipboard content was printed.")
    print(
        "Legacy users received deterministic "
        "placeholder school IDs and "
        "institutional email addresses."
    )


def main() -> None:
    args = parse_args()

    check_database()

    missing_count = inspect_state()

    if not args.apply:
        print()
        print("DRY RUN ONLY: no database changes were made.")
        print("Run with --apply only after reviewing this output.")
        return

    if missing_count == 0:
        print("No legacy column upgrade is required.")
        return

    apply_upgrade()

    remaining_missing_columns = inspect_state()

    if remaining_missing_columns != 0:
        raise UpgradeError(
            "Upgrade finished, but one or more current columns are still missing."
        )


if __name__ == "__main__":
    main()
