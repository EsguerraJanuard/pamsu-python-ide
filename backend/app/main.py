import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.integrations.partner_auth import (
    MIN_PARTNER_EXECUTION_TOKEN_LENGTH,
    PARTNER_EXECUTION_TOKEN_ENV,
)
from app.routers import (
    activities,
    audit_records,
    auth,
    classrooms,
    evaluation,
    execution,
    instructor,
    logs,
    notifications,
    registration,
    reporting,
    submissions,
)


APP_TITLE = "PAMSU Python IDE Backend"
APP_VERSION = "0.14.0"

HealthState = Literal["healthy"]
ReadinessState = Literal["ready", "not_ready"]
ReadinessComponentState = Literal[
    "ready",
    "not_ready",
    "contract_only",
]


class HealthResponse(BaseModel):
    status: HealthState
    service: str
    version: str
    checked_at: datetime

    model_config = ConfigDict(
        extra="forbid",
    )


class ReadinessComponentResponse(BaseModel):
    name: str
    status: ReadinessComponentState
    required: bool
    detail: str

    model_config = ConfigDict(
        extra="forbid",
    )


class ReadinessResponse(BaseModel):
    status: ReadinessState
    service: str
    version: str
    checked_at: datetime
    components: list[ReadinessComponentResponse]

    model_config = ConfigDict(
        extra="forbid",
    )


OPENAPI_TAGS = [
    {
        "name": "System",
        "description": (
            "Application information, liveness checks, and readiness "
            "contracts. Health responses do not expose credentials, "
            "provider configuration, or internal exception details."
        ),
    },
    {
        "name": "Authentication",
        "description": ("Verified-user login and access-token operations."),
    },
    {
        "name": "Registration",
        "description": (
            "University-email registration and OTP verification through "
            "an injected email-delivery adapter contract. Client "
            "applications cannot assign account roles, and plaintext OTP "
            "codes are never persisted or returned."
        ),
    },
    {
        "name": "Classrooms",
        "description": (
            "Instructor-owned classroom management, backend-generated "
            "class codes, student enrollment operations, privacy-safe "
            "classroom archive notifications, and immutable "
            "accountability records for meaningful changes."
        ),
    },
    {
        "name": "Instructor",
        "description": (
            "Instructor-authorized activity, test-case, submission, "
            "execution-request, coding-session, evaluation, "
            "review-queue, gradebook, and manual grading operations. "
            "Review and gradebook summaries exclude source code and "
            "sensitive analytics. Automated indicators remain "
            "review-only, while accountable academic changes create "
            "privacy-safe immutable audit records."
        ),
    },
    {
        "name": "Activities",
        "description": (
            "Student-safe access to published laboratory and homework "
            "activities, public sample test cases, student-owned "
            "coding-session lifecycle operations, and the "
            "authenticated student's own released manual grades."
        ),
    },
    {
        "name": "Submissions",
        "description": (
            "Student-owned immutable submission attempts. Student "
            "identity, attempt numbering, official-attempt state, "
            "status, timestamps, approved instructor notifications, "
            "and submission-accountability records are controlled by "
            "the backend."
        ),
    },
    {
        "name": "Execution",
        "description": (
            "Student-owned run, check, and submit execution-request "
            "snapshots plus authenticated isolated-worker result updates. "
            "Partner updates require correlation IDs, idempotency keys, "
            "strict sequence ordering, replay validation, and allowed "
            "lifecycle transitions. FastAPI never executes student Python "
            "code; execution remains exclusive to the partner-owned "
            "isolated sandbox."
        ),
    },
    {
        "name": "Behavioral Logs",
        "description": (
            "Privacy-conscious aggregate session indicators without "
            "clipboard contents, pasted text, individual keystrokes, "
            "browsing history, screen recording, webcam, or microphone "
            "collection."
        ),
    },
    {
        "name": "Evaluation",
        "description": (
            "Static AST and source-similarity indicators for "
            "authorized instructor review, student-safe "
            "released-grade viewing, explicit review-status updates, "
            "manual instructor grading, privacy-safe grade-release "
            "notifications, and immutable grading-accountability "
            "records. Automated indicators and local LLM assistance "
            "never assign official grades or determine plagiarism, "
            "cheating, copying, or misconduct."
        ),
    },
    {
        "name": "Notifications",
        "description": (
            "Authenticated students and instructors may access only "
            "their own backend-generated in-app notifications, unread "
            "counts, and read-state operations. Notification creation, "
            "recipient selection, titles, messages, and event payloads "
            "remain exclusive to trusted academic workflows."
        ),
    },
    {
        "name": "Audit Trail",
        "description": (
            "Authenticated users may read only audit records attributed "
            "to their own account. Audit creation remains exclusive to "
            "trusted backend workflows, and records exclude source code, "
            "credentials, OTP values, hidden test data, execution output, "
            "surveillance data, unreleased grades, and automated "
            "misconduct conclusions."
        ),
    },
    {
        "name": "Reporting",
        "description": (
            "Ownership-scoped classroom and activity completion summaries, "
            "manual-grade distributions, missing-submission reports, "
            "authenticated student progress, and privacy-safe gradebook CSV "
            "exports. Reporting excludes raw source code, standard input, "
            "hidden tests, AST or similarity details, execution output, "
            "session telemetry, unreleased student-grade data, surveillance "
            "data, and automated misconduct rankings."
        ),
    },
]


app = FastAPI(
    title=APP_TITLE,
    description=(
        "Backend API for the PAMSU Web-Based Python IDE with "
        "university-email authentication, OTP registration through an "
        "email-adapter contract, classroom and enrollment management, "
        "activity and test-case management, student-owned coding sessions, "
        "privacy-safe aggregate session telemetry, immutable submission "
        "attempts, queued execution requests, backend-controlled "
        "execution-attempt counters, authenticated isolated-worker result "
        "contracts, correlation and idempotency controls, replay-safe "
        "partner updates, local LLM assistance boundaries, static "
        "structural and source-similarity analytics, instructor-owned "
        "paginated review queues, privacy-safe gradebook summaries, "
        "student-safe released manual-grade lists, explicit "
        "evaluation-status control, manual instructor grading workflows, "
        "immutable approved academic events, recipient-owned in-app "
        "notifications, notification unread counts, owner-scoped "
        "read-state operations, immutable privacy-safe audit records, "
        "ownership-safe completion summaries, manual-grade distributions, "
        "missing-submission reports, authenticated student progress "
        "summaries, privacy-safe gradebook CSV exports, and explicit "
        "liveness and readiness contracts."
    ),
    version=APP_VERSION,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.include_router(auth.router)
app.include_router(registration.router)
app.include_router(classrooms.router)
app.include_router(instructor.router)
app.include_router(activities.router)
app.include_router(submissions.router)
app.include_router(execution.router)
app.include_router(logs.router)
app.include_router(evaluation.router)
app.include_router(notifications.router)
app.include_router(audit_records.router)
app.include_router(reporting.router)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def check_database_readiness(
    db: Session,
) -> ReadinessComponentResponse:
    try:
        db.execute(text("SELECT 1"))

        return ReadinessComponentResponse(
            name="database",
            status="ready",
            required=True,
            detail="The database connection is available.",
        )
    except SQLAlchemyError:
        db.rollback()

        return ReadinessComponentResponse(
            name="database",
            status="not_ready",
            required=True,
            detail="The database connection is unavailable.",
        )


def check_execution_partner_auth_readiness() -> ReadinessComponentResponse:
    configured_token = (os.getenv(PARTNER_EXECUTION_TOKEN_ENV) or "").strip()

    if len(configured_token) < MIN_PARTNER_EXECUTION_TOKEN_LENGTH:
        return ReadinessComponentResponse(
            name="execution_partner_auth",
            status="not_ready",
            required=True,
            detail=("The execution-partner authentication boundary is not configured."),
        )

    return ReadinessComponentResponse(
        name="execution_partner_auth",
        status="ready",
        required=True,
        detail=("The execution-partner authentication boundary is configured."),
    )


def build_contract_only_component(
    *,
    name: str,
    detail: str,
) -> ReadinessComponentResponse:
    return ReadinessComponentResponse(
        name=name,
        status="contract_only",
        required=False,
        detail=detail,
    )


@app.get(
    "/",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Read API information",
)
def read_root() -> dict[str, str]:
    return {
        "message": f"{APP_TITLE} is running.",
        "version": APP_VERSION,
        "documentation": "/docs",
        "health": "/health",
        "readiness": "/ready",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Check application liveness",
    description=(
        "Returns process-level liveness without contacting external "
        "providers or exposing configuration details."
    ),
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=APP_TITLE,
        version=APP_VERSION,
        checked_at=utc_now(),
    )


@app.get(
    "/ready",
    response_model=ReadinessResponse,
    tags=["System"],
    summary="Check required integration readiness",
    description=(
        "Checks required database and execution-partner authentication "
        "boundaries. OTP email and local LLM integrations are reported as "
        "contract-only because Pillar 14 intentionally does not select or "
        "implement concrete providers."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": ("All required Pillar 14 components are ready."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": ("One or more required components are not ready."),
        },
    },
)
def readiness_check(
    db: Session = Depends(get_db),
) -> ReadinessResponse | JSONResponse:
    components = [
        check_database_readiness(db),
        check_execution_partner_auth_readiness(),
        build_contract_only_component(
            name="otp_email_adapter",
            detail=(
                "The OTP email-delivery interface is defined; no "
                "concrete provider is selected by Pillar 14."
            ),
        ),
        build_contract_only_component(
            name="local_llm_adapter",
            detail=(
                "The local LLM assistance interface is defined; no "
                "runtime or model provider is selected by Pillar 14."
            ),
        ),
    ]

    required_components_ready = all(
        component.status == "ready" for component in components if component.required
    )

    response = ReadinessResponse(
        status=("ready" if required_components_ready else "not_ready"),
        service=APP_TITLE,
        version=APP_VERSION,
        checked_at=utc_now(),
        components=components,
    )

    if required_components_ready:
        return response

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response.model_dump(mode="json"),
    )


# HEALTH BOUNDARY:
# /health is a liveness contract only. It does not test the database,
# execution partner, OTP provider, local LLM runtime, or external services.

# READINESS BOUNDARY:
# /ready checks required backend dependencies without returning credentials,
# raw exceptions, connection strings, provider names, or secret lengths.

# OPTIONAL-INTEGRATION BOUNDARY:
# OTP email and local LLM integrations remain contract-only in Pillar 14.
# Their absence does not make the core API unready until concrete adapters
# become required by a later deployment pillar.
