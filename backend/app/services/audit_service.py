import json
import math
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain_models import AuditRecord
from app.schemas.audit_schema import (
    AuditActionType,
    AuditOutcome,
    AuditRecordCreateInternal,
    AuditRecordListResponse,
    AuditRecordResponse,
    AuditResourceType,
)


MAX_AUDIT_DATA_BYTES = 16_384


class AuditServiceError(Exception):
    """Base exception for trusted audit-service failures."""


class AuditRecordConflictError(AuditServiceError):
    """Raised when an audit key is reused for a different action."""


class AuditRecordNotFoundError(AuditServiceError):
    """Raised when an actor-owned audit record does not exist."""


class AuditMetadataTooLargeError(AuditServiceError):
    """Raised when privacy-safe metadata exceeds the storage limit."""


def _validated_payload(
    payload: AuditRecordCreateInternal | dict[str, Any],
) -> AuditRecordCreateInternal:
    if isinstance(payload, AuditRecordCreateInternal):
        return payload

    return AuditRecordCreateInternal.model_validate(payload)


def _ensure_metadata_size(
    audit_data: dict[str, Any],
) -> None:
    serialized = json.dumps(
        audit_data,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    if len(serialized) > MAX_AUDIT_DATA_BYTES:
        raise AuditMetadataTooLargeError(
            "Audit metadata exceeds the maximum allowed size."
        )


def _datetimes_match(
    existing_value: datetime,
    expected_value: datetime | None,
) -> bool:
    if expected_value is None:
        return True

    return existing_value == expected_value


def _ensure_existing_record_matches(
    existing: AuditRecord,
    payload: AuditRecordCreateInternal,
) -> None:
    matches = (
        existing.actor_user_id == payload.actor_user_id
        and existing.action_type == payload.action_type
        and existing.resource_type == payload.resource_type
        and existing.resource_id == payload.resource_id
        and existing.outcome == payload.outcome
        and existing.audit_data == payload.audit_data
        and _datetimes_match(
            existing.occurred_at,
            payload.occurred_at,
        )
    )

    if not matches:
        raise AuditRecordConflictError(
            "The audit key is already assigned to a different accountable action."
        )


def create_audit_record(
    db: Session,
    payload: AuditRecordCreateInternal | dict[str, Any],
    *,
    commit: bool = True,
) -> AuditRecord:
    """
    Create one immutable, privacy-safe audit record.

    The caller must supply a backend-generated audit key. Reusing the same
    key with the same accountable action is idempotent. Reusing it with
    different action data raises a conflict instead of rewriting history.

    Set commit=False when the audit row must be committed atomically with
    the originating domain operation. In that mode, this function flushes
    the row but leaves commit and rollback control to the caller.
    """

    validated = _validated_payload(payload)
    _ensure_metadata_size(validated.audit_data)

    existing = (
        db.query(AuditRecord)
        .filter(
            AuditRecord.audit_key == validated.audit_key,
        )
        .one_or_none()
    )

    if existing is not None:
        _ensure_existing_record_matches(
            existing,
            validated,
        )
        return existing

    record = AuditRecord(
        audit_key=validated.audit_key,
        actor_user_id=validated.actor_user_id,
        action_type=validated.action_type,
        resource_type=validated.resource_type,
        resource_id=validated.resource_id,
        outcome=validated.outcome,
        audit_data=validated.audit_data,
    )

    if validated.occurred_at is not None:
        record.occurred_at = validated.occurred_at

    db.add(record)

    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()

    return record


def get_actor_owned_audit_record(
    db: Session,
    *,
    audit_id: str,
    actor_user_id: int,
) -> AuditRecord:
    """
    Return one audit record created by the authenticated actor.

    This owner-scoped helper intentionally does not expose audit records
    created by other users. Resource-based authorized review is added only
    through explicit domain ownership checks.
    """

    record = (
        db.query(AuditRecord)
        .filter(
            AuditRecord.audit_id == audit_id,
            AuditRecord.actor_user_id == actor_user_id,
        )
        .one_or_none()
    )

    if record is None:
        raise AuditRecordNotFoundError("Audit record was not found.")

    return record


def list_actor_owned_audit_records(
    db: Session,
    *,
    actor_user_id: int,
    page: int = 1,
    page_size: int = 20,
    action_type: AuditActionType | None = None,
    resource_type: AuditResourceType | None = None,
    resource_id: str | None = None,
    outcome: AuditOutcome | None = None,
) -> AuditRecordListResponse:
    """
    Return a deterministic, paginated list of actor-owned audit records.

    The authenticated actor identifier is mandatory. This prevents a
    general audit-table listing operation from becoming an information
    disclosure path.
    """

    if actor_user_id <= 0:
        raise ValueError("actor_user_id must be greater than zero.")

    if page < 1:
        raise ValueError("page must be at least 1.")

    if page_size < 1 or page_size > 100:
        raise ValueError("page_size must be between 1 and 100.")

    query = db.query(AuditRecord).filter(
        AuditRecord.actor_user_id == actor_user_id,
    )

    if action_type is not None:
        query = query.filter(
            AuditRecord.action_type == action_type,
        )

    if resource_type is not None:
        query = query.filter(
            AuditRecord.resource_type == resource_type,
        )

    if resource_id is not None:
        normalized_resource_id = resource_id.strip()

        if not normalized_resource_id:
            raise ValueError("resource_id must not be blank.")

        query = query.filter(
            AuditRecord.resource_id == normalized_resource_id,
        )

    if outcome is not None:
        query = query.filter(
            AuditRecord.outcome == outcome,
        )

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    records = (
        query.order_by(
            AuditRecord.occurred_at.desc(),
            AuditRecord.audit_id.desc(),
        )
        .offset(
            (page - 1) * page_size,
        )
        .limit(page_size)
        .all()
    )

    return AuditRecordListResponse(
        items=[AuditRecordResponse.model_validate(record) for record in records],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )
