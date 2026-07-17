from typing import NoReturn
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain_models import User
from app.schemas.audit_schema import (
    AuditActionType,
    AuditOutcome,
    AuditRecordListResponse,
    AuditRecordResponse,
    AuditResourceType,
)
from app.services.audit_service import (
    AuditMetadataTooLargeError,
    AuditRecordConflictError,
    AuditRecordNotFoundError,
    AuditServiceError,
    get_actor_owned_audit_record,
    list_actor_owned_audit_records,
)


router = APIRouter(
    prefix="/audit-records",
    tags=["Audit Trail"],
)


def raise_audit_http_exception(
    exc: AuditServiceError,
) -> NoReturn:
    if isinstance(
        exc,
        AuditRecordNotFoundError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        AuditRecordConflictError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        AuditMetadataTooLargeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=("The audit-record operation could not be completed."),
    ) from exc


@router.get(
    "/",
    response_model=AuditRecordListResponse,
    status_code=status.HTTP_200_OK,
    operation_id="list_my_audit_records",
    summary="List my audit records",
    description=(
        "Returns a deterministic, paginated list containing only "
        "audit records attributed to the authenticated user. "
        "Passwords, OTP values, source code, test data, execution "
        "output, analytics details, clipboard or paste contents, "
        "surveillance data, unreleased grades, and automated "
        "misconduct conclusions are excluded."
    ),
)
def list_audit_records_endpoint(
    page: int = Query(
        default=1,
        ge=1,
        description="One-based page number.",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description=("Number of audit records returned per page."),
    ),
    action_type: AuditActionType | None = Query(
        default=None,
        description=("Optional approved accountable action filter."),
    ),
    resource_type: AuditResourceType | None = Query(
        default=None,
        description=("Optional approved resource-type filter."),
    ),
    resource_id: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description=("Optional backend resource identifier filter."),
    ),
    outcome: AuditOutcome | None = Query(
        default=None,
        description=("Optional succeeded, denied, or failed outcome filter."),
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditRecordListResponse:
    try:
        result = list_actor_owned_audit_records(
            db,
            actor_user_id=current_user.user_id,
            page=page,
            page_size=page_size,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
        )
    except AuditServiceError as exc:
        raise_audit_http_exception(exc)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return AuditRecordListResponse.model_validate(result)


@router.get(
    "/{audit_id}",
    response_model=AuditRecordResponse,
    status_code=status.HTTP_200_OK,
    operation_id="get_my_audit_record",
    summary="Get one of my audit records",
    description=(
        "Returns an audit record only when it is attributed to "
        "the authenticated user. Audit records belonging to another "
        "actor are treated as not found."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "The audit record was not found for the authenticated user."
            ),
        },
    },
)
def get_audit_record_endpoint(
    audit_id: UUID = Path(
        ...,
        description="Audit-record UUID.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditRecordResponse:
    try:
        result = get_actor_owned_audit_record(
            db,
            audit_id=str(audit_id),
            actor_user_id=current_user.user_id,
        )
    except AuditServiceError as exc:
        raise_audit_http_exception(exc)

    return AuditRecordResponse.model_validate(result)


# AUTHORIZATION BOUNDARY:
# These endpoints return only records attributed to the authenticated
# database user. They do not expose a general system-wide audit listing
# or allow one user to select another actor identifier.

# CREATION BOUNDARY:
# This router exposes no audit creation, update, or delete endpoint.
# Audit records are created only by trusted backend domain workflows.

# IMMUTABILITY BOUNDARY:
# Audit records represent accountable historical facts. API clients may
# read authorized records but cannot alter or remove them.

# PRIVACY BOUNDARY:
# Audit responses exclude passwords, password hashes, OTP values, source
# code, starter code, standard input, hidden test data, execution output,
# AST and similarity details, clipboard contents, pasted text, browsing
# history, individual keystrokes, screen/webcam/microphone data,
# unreleased grades, and automated misconduct conclusions.
