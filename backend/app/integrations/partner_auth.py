import secrets
from typing import Annotated, Literal

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import (
    MIN_PARTNER_EXECUTION_TOKEN_LENGTH,
    PARTNER_EXECUTION_TOKEN_ENV,
    get_settings,
)


PARTNER_EXECUTION_TOKEN_HEADER = "X-Partner-Token"

PartnerExecutionIdentity = Literal["isolated_execution_worker",]


partner_execution_token_header = APIKeyHeader(
    name=PARTNER_EXECUTION_TOKEN_HEADER,
    scheme_name="PartnerExecutionToken",
    description=(
        "Internal token used only by the trusted isolated-execution "
        "partner when submitting lifecycle and result updates."
    ),
    auto_error=False,
)


def _configured_partner_execution_token() -> str:
    settings = get_settings()

    configured_secret = settings.partner_execution_token

    if configured_secret is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("The execution-partner authentication boundary is not configured."),
        )

    configured_token = configured_secret.get_secret_value()

    if len(configured_token) < MIN_PARTNER_EXECUTION_TOKEN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=("The execution-partner authentication boundary is not configured."),
        )

    return configured_token


def get_authenticated_execution_partner(
    supplied_token: Annotated[
        str | None,
        Security(partner_execution_token_header),
    ],
) -> PartnerExecutionIdentity:
    """
    Authenticate the trusted isolated-execution partner.

    The shared token is accepted only through the dedicated HTTP header.
    It is never accepted in a request body, query string, path, log,
    database row, response model, or student/instructor API.
    """

    configured_token = _configured_partner_execution_token()

    if supplied_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=("Execution-partner authentication is required."),
            headers={
                "WWW-Authenticate": "PartnerExecutionToken",
            },
        )

    normalized_supplied_token = supplied_token.strip()

    if not secrets.compare_digest(
        normalized_supplied_token,
        configured_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=("Execution-partner authentication failed."),
            headers={
                "WWW-Authenticate": "PartnerExecutionToken",
            },
        )

    return "isolated_execution_worker"


# CONFIGURATION BOUNDARY:
# The execution-partner secret is loaded only through the validated
# immutable application settings object. This module does not parse
# process environment variables independently.

# AUTHENTICATION BOUNDARY:
# This dependency authenticates only the partner-owned isolated execution
# adapter. It must never be used as student or instructor authentication.

# SECRET HANDLING BOUNDARY:
# The token is unwrapped only for constant-time authentication comparison.
# It must never be persisted, logged, returned, or copied into an execution
# request, partner update record, audit record, or notification.

# TRANSPORT BOUNDARY:
# Production deployment must provide HTTPS at the reverse proxy or platform
# edge. This module defines authentication contracts only and does not
# implement TLS termination, secret rotation, or partner runtime delivery.
