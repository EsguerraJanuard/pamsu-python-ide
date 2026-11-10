"""
Audit records for administrator actions.

Successful actions: `record_admin_action` adds the record to the caller's
open transaction (commit=False), so the change and its record are committed
or rolled back together. If the record cannot be built or written,
AdminAuditError is raised and the caller must roll back and report that
nothing was saved; a change is never committed without its record.

Failed or refused actions: `record_admin_failure` runs after the caller has
rolled back, writes one record with outcome "failed" or "denied" in its own
transaction, and never masks the caller's original error. If that write
fails it is logged (not swallowed silently) and the original error is still
returned to the client.

Logging: only exception class names are logged or carried in AdminAuditError.
Exception text can hold the rejected metadata (pydantic's input_value) or SQL
parameters of the flushed changes, such as a pending password hash.

Metadata goes through the audit schema's privacy validation: credentials,
password hashes, OTPs, reset codes and tokens are rejected, by key name
and by value shape. Callers pass only identifiers, roles, flags and counts.
"""

import logging
from typing import Any
from uuid import uuid4

from app.schemas.audit_schema import AuditActionType, AuditResourceType
from app.services.audit_service import AuditServiceError, create_audit_record
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

AUDIT_UNAVAILABLE_DETAIL = (
    "The change was not saved because it could not be recorded in the audit log. Please try again."
)


class AdminAuditError(RuntimeError):
    """The audit record for an admin action could not be written."""


def safe_error_summary(error: BaseException) -> str:
    """Exception class names only, never the message or its parameters."""

    original = getattr(error, "orig", None)
    summary = type(error).__name__
    return f"{summary}/{type(original).__name__}" if original is not None else summary


def build_admin_audit_key(
    *,
    action_type: str,
    resource_type: str,
    resource_id: int | str,
    repeatable: bool,
) -> str:
    base_key = f"audit:{action_type}:{resource_type}:{resource_id}"
    return f"{base_key}:{uuid4()}" if repeatable else base_key


def record_admin_action(
    db: Session,
    *,
    actor_user_id: int,
    action_type: AuditActionType,
    resource_type: AuditResourceType,
    resource_id: int | str,
    audit_data: dict[str, Any] | None = None,
    repeatable: bool = True,
) -> None:
    """Add a "succeeded" record to the caller's transaction (no commit)."""

    try:
        create_audit_record(
            db,
            {
                "audit_key": build_admin_audit_key(
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    repeatable=repeatable,
                ),
                "actor_user_id": actor_user_id,
                "action_type": action_type,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "outcome": "succeeded",
                "audit_data": audit_data or {},
            },
            commit=False,
        )
    except (AuditServiceError, ValidationError, SQLAlchemyError) as error:
        # `from None`: the original exception's text must not reach logs.
        raise AdminAuditError(
            f"Could not record {action_type} ({safe_error_summary(error)})."
        ) from None


def record_admin_failure(
    db: Session,
    *,
    actor_user_id: int,
    action_type: AuditActionType,
    resource_type: AuditResourceType,
    resource_id: int | str,
    reason: str,
    outcome: str = "failed",
    audit_data: dict[str, Any] | None = None,
) -> None:
    """Record a failed or refused action in its own transaction.

    Call only after the action's own transaction was rolled back.
    """

    try:
        create_audit_record(
            db,
            {
                "audit_key": build_admin_audit_key(
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    repeatable=True,
                ),
                "actor_user_id": actor_user_id,
                "action_type": action_type,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "outcome": outcome,
                "audit_data": {**(audit_data or {}), "reason": reason},
            },
            commit=True,
        )
    except (AuditServiceError, ValidationError, SQLAlchemyError) as error:
        db.rollback()
        logger.error(
            "Could not record a %s %s by admin %s on %s %s (reason: %s; %s).",
            outcome,
            action_type,
            actor_user_id,
            resource_type,
            resource_id,
            reason,
            safe_error_summary(error),
        )
