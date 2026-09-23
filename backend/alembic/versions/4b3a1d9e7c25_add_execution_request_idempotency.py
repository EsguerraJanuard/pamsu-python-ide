"""Add student execution-request idempotency metadata.

Revision ID: 4b3a1d9e7c25
Revises: 18d3ef8f020d
Create Date: 2026-07-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "4b3a1d9e7c25"
down_revision: str | None = "18d3ef8f020d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "execution_requests",
        sa.Column(
            "request_idempotency_key",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.add_column(
        "execution_requests",
        sa.Column(
            "request_payload_digest",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_execution_request_idempotency_key_length",
        "execution_requests",
        ("request_idempotency_key IS NULL OR length(request_idempotency_key) = 36"),
    )

    op.create_check_constraint(
        "ck_execution_request_idempotency_pair",
        "execution_requests",
        (
            "(request_idempotency_key IS NULL "
            "AND request_payload_digest IS NULL) "
            "OR (request_idempotency_key IS NOT NULL "
            "AND request_payload_digest IS NOT NULL)"
        ),
    )

    op.create_check_constraint(
        "ck_execution_request_payload_digest_length",
        "execution_requests",
        ("request_payload_digest IS NULL OR length(request_payload_digest) = 64"),
    )

    op.create_unique_constraint(
        "uq_execution_requests_student_idempotency_key",
        "execution_requests",
        [
            "student_id",
            "request_idempotency_key",
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_execution_requests_student_idempotency_key",
        "execution_requests",
        type_="unique",
    )

    op.drop_constraint(
        "ck_execution_request_payload_digest_length",
        "execution_requests",
        type_="check",
    )

    op.drop_constraint(
        "ck_execution_request_idempotency_pair",
        "execution_requests",
        type_="check",
    )

    op.drop_constraint(
        "ck_execution_request_idempotency_key_length",
        "execution_requests",
        type_="check",
    )

    op.drop_column(
        "execution_requests",
        "request_payload_digest",
    )

    op.drop_column(
        "execution_requests",
        "request_idempotency_key",
    )
