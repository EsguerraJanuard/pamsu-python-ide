import logging
import re

from app.core.request_context import get_current_correlation_id
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]{1,63}$")


def database_error_summary(error: BaseException) -> str:
    """
    Describe a database error without its message.

    The message of a database error can contain row values even when the
    engine hides statement parameters: PostgreSQL adds details such as
    "Key (email)=(...) already exists" or "Failing row contains (...)".
    Only class names, the SQLSTATE code and the constraint name are kept.
    """

    parts = [type(error).__name__]
    original = getattr(error, "orig", None)

    if original is not None:
        parts.append(type(original).__name__)

        sqlstate = getattr(original, "pgcode", None) or getattr(original, "sqlstate", None)
        if isinstance(sqlstate, str) and _SAFE_IDENTIFIER.match(sqlstate):
            parts.append(f"sqlstate={sqlstate}")

        constraint = getattr(getattr(original, "diag", None), "constraint_name", None)
        if isinstance(constraint, str) and _SAFE_IDENTIFIER.match(constraint):
            parts.append(f"constraint={constraint}")

    return " ".join(parts)


async def handle_unhandled_database_error(request: Request, error: Exception) -> JSONResponse:
    logger.error(
        "Unhandled database error on %s %s (%s; correlation_id=%s).",
        request.method,
        request.url.path,
        database_error_summary(error),
        get_current_correlation_id(),
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


# LOGGING PRIVACY BOUNDARY:
# Unhandled SQLAlchemy errors are answered here instead of reaching the
# server's default error handler, which logs the full traceback and with it
# the database's error message. Only the summary above is logged; the
# correlation ID links it to the request log.
