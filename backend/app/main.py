from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.core.database import get_db
from app.core.request_context import (
    RequestContextMiddleware,
    configure_request_logging,
)
from app.integrations.partner_auth import (
    PARTNER_EXECUTION_TOKEN_HEADER,
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
APP_VERSION = "1.0.0"

HealthState = Literal["healthy"]
ReadinessState = Literal[
    "ready",
    "not_ready",
]
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


settings = get_settings()

request_logger = configure_request_logging(log_level=settings.log_level)

documentation_url = "/docs" if settings.enable_api_docs else None

redoc_url = "/redoc" if settings.enable_api_docs else None

openapi_url = "/openapi.json" if settings.enable_api_docs else None


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
        "summaries, privacy-safe gradebook CSV exports, validated runtime "
        "security configuration, request correlation IDs, privacy-safe "
        "structured request logging, and explicit liveness and readiness "
        "contracts."
    ),
    version=APP_VERSION,
    openapi_tags=OPENAPI_TAGS,
    docs_url=documentation_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)


if settings.allowed_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(settings.allowed_hosts),
        www_redirect=False,
    )


if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allowed_origins),
        allow_credentials=(settings.cors_allow_credentials),
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            PARTNER_EXECUTION_TOKEN_HEADER,
            settings.correlation_id_header,
        ],
        expose_headers=[
            settings.correlation_id_header,
        ],
        max_age=600,
    )


# Add request context last so it remains the outermost application
# middleware and covers CORS and trusted-host responses as well.
app.add_middleware(
    RequestContextMiddleware,
    correlation_id_header=(settings.correlation_id_header),
    logger=request_logger,
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
            detail=("The database connection is available."),
        )

    except SQLAlchemyError:
        db.rollback()

        return ReadinessComponentResponse(
            name="database",
            status="not_ready",
            required=True,
            detail=("The database connection is unavailable."),
        )


def check_execution_partner_auth_readiness() -> ReadinessComponentResponse:
    runtime_settings = get_settings()

    if not runtime_settings.partner_execution_token_configured:
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
    tags=[
        "System",
    ],
    summary="Read API information",
)
def read_root() -> dict[str, str]:
    return {
        "message": (f"{APP_TITLE} is running."),
        "version": APP_VERSION,
        "documentation": ("/docs" if settings.enable_api_docs else "disabled"),
        "health": "/health",
        "readiness": "/ready",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=[
        "System",
    ],
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
    tags=[
        "System",
    ],
    summary="Check required integration readiness",
    description=(
        "Checks required database and execution-partner authentication "
        "boundaries. OTP email and local LLM integrations are reported as "
        "contract-only because concrete providers remain outside the "
        "current backend implementation."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": ("All required components are ready."),
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
                "concrete provider is selected by the backend."
            ),
        ),
        build_contract_only_component(
            name="local_llm_adapter",
            detail=(
                "The local LLM assistance interface is defined; no "
                "runtime or model provider is selected by the backend."
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
        status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
        content=response.model_dump(mode="json"),
    )


# CONFIGURATION BOUNDARY:
# Application environment, documentation exposure, trusted hosts, CORS,
# partner readiness, logging level, and correlation-header configuration
# are obtained only through the validated immutable settings layer.

# CORS BOUNDARY:
# CORS middleware is installed only when explicit trusted origins are
# configured. Wildcard origins are rejected by configuration validation.
# Only approved HTTP methods and request headers are allowed.

# TRUSTED-HOST BOUNDARY:
# Trusted-host middleware is installed only when an explicit host allowlist
# is configured. Production configuration rejects wildcard trusted hosts.

# DOCUMENTATION BOUNDARY:
# OpenAPI, Swagger UI, and ReDoc are enabled or disabled through validated
# environment configuration. Production defaults to disabled.

# REQUEST-CONTEXT BOUNDARY:
# Every HTTP request receives a validated UUID correlation ID. The ID is
# returned through the configured response header and is available through
# trusted request state and context-local access.

# STRUCTURED-LOGGING BOUNDARY:
# Request logs include only approved metadata: timestamp, level, event,
# correlation ID, method, path, status code, and duration. Bodies, query
# strings, headers, credentials, tokens, source code, execution data,
# clipboard or paste contents, and surveillance data are excluded.

# HEALTH BOUNDARY:
# /health is a liveness contract only. It does not test the database,
# execution partner, OTP provider, local LLM runtime, or external services.

# READINESS BOUNDARY:
# /ready checks required backend dependencies without returning credentials,
# raw exceptions, connection strings, provider names, or secret lengths.

# OPTIONAL-INTEGRATION BOUNDARY:
# OTP email and local LLM integrations remain contract-only. Their absence
# does not make the core API unready until concrete adapters become required.
