import json
import logging
import sys
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import UUID, uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)


REQUEST_LOGGER_NAME = "pamsu.request"

_correlation_id_context: ContextVar[str | None] = ContextVar(
    "pamsu_correlation_id",
    default=None,
)


class PrivacySafeJsonFormatter(logging.Formatter):
    """
    Serialize approved application log fields as one JSON object.

    Exception tracebacks, request bodies, query strings, headers,
    credentials, tokens, source code, standard input, and response
    bodies are intentionally excluded.
    """

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        if isinstance(
            record.msg,
            dict,
        ):
            event_data = dict(record.msg)
        else:
            event_data = {
                "event": "application_log",
                "message": record.getMessage(),
            }

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            **event_data,
        }

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            sort_keys=True,
            default=str,
        )


def configure_request_logging(
    *,
    log_level: str,
) -> logging.Logger:
    """
    Configure one privacy-safe structured request logger.

    Repeated calls update the logger level but do not install duplicate
    handlers.
    """

    logger = logging.getLogger(REQUEST_LOGGER_NAME)

    logger.setLevel(log_level)
    logger.propagate = False

    configured_handler: logging.Handler | None = None

    for handler in logger.handlers:
        if getattr(
            handler,
            "_pamsu_privacy_safe_handler",
            False,
        ):
            configured_handler = handler
            break

    if configured_handler is None:
        configured_handler = logging.StreamHandler(sys.stdout)

        setattr(
            configured_handler,
            "_pamsu_privacy_safe_handler",
            True,
        )

        configured_handler.setFormatter(PrivacySafeJsonFormatter())

        logger.addHandler(configured_handler)

    configured_handler.setLevel(log_level)

    return logger


def get_current_correlation_id() -> str | None:
    """
    Return the correlation ID associated with the current request context.
    """

    return _correlation_id_context.get()


def _generate_correlation_id() -> str:
    return str(uuid4())


def _normalize_correlation_id(
    supplied_value: str | None,
) -> str:
    """
    Accept only UUID correlation identifiers.

    Missing, blank, malformed, or non-canonical client values are replaced
    with a new backend-generated UUID instead of being reflected into logs
    or response headers.
    """

    if supplied_value is None:
        return _generate_correlation_id()

    normalized_value = supplied_value.strip()

    if not normalized_value:
        return _generate_correlation_id()

    try:
        parsed_value = UUID(normalized_value)
    except (
        AttributeError,
        TypeError,
        ValueError,
    ):
        return _generate_correlation_id()

    return str(parsed_value)


def _read_request_header(
    scope: Scope,
    *,
    header_name: str,
) -> str | None:
    expected_name = header_name.lower().encode("latin-1")

    for raw_name, raw_value in scope.get(
        "headers",
        [],
    ):
        if raw_name.lower() != expected_name:
            continue

        try:
            return raw_value.decode("latin-1")
        except UnicodeDecodeError:
            return None

    return None


def _build_request_log_event(
    *,
    event: str,
    correlation_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> dict[str, Any]:
    return {
        "event": event,
        "correlation_id": correlation_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(
            duration_ms,
            2,
        ),
    }


class RequestContextMiddleware:
    """
    Attach one correlation ID to every HTTP request and response.

    A valid client-supplied UUID is preserved. Invalid or absent values are
    replaced with a backend-generated UUID. Only privacy-safe request
    metadata is emitted through structured logging.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        correlation_id_header: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self.app = app
        self.correlation_id_header = correlation_id_header
        self.logger = (
            logger if logger is not None else logging.getLogger(REQUEST_LOGGER_NAME)
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )
            return

        supplied_correlation_id = _read_request_header(
            scope,
            header_name=(self.correlation_id_header),
        )

        correlation_id = _normalize_correlation_id(supplied_correlation_id)

        context_token: Token[str | None] = _correlation_id_context.set(correlation_id)

        scope.setdefault(
            "state",
            {},
        )

        scope["state"]["correlation_id"] = correlation_id

        request_started_at = perf_counter()
        response_status_code: int | None = None

        async def send_with_correlation_id(
            message: Message,
        ) -> None:
            nonlocal response_status_code

            if message["type"] == "http.response.start":
                response_status_code = int(message["status"])

                response_headers = MutableHeaders(scope=message)

                response_headers[self.correlation_id_header] = correlation_id

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_correlation_id,
            )

        except Exception:
            duration_ms = (perf_counter() - request_started_at) * 1000.0

            self.logger.error(
                _build_request_log_event(
                    event="http_request_failed",
                    correlation_id=correlation_id,
                    method=str(
                        scope.get(
                            "method",
                            "",
                        )
                    ),
                    path=str(
                        scope.get(
                            "path",
                            "",
                        )
                    ),
                    status_code=(
                        response_status_code
                        if response_status_code is not None
                        else 500
                    ),
                    duration_ms=duration_ms,
                )
            )

            raise

        else:
            duration_ms = (perf_counter() - request_started_at) * 1000.0

            self.logger.info(
                _build_request_log_event(
                    event="http_request_completed",
                    correlation_id=correlation_id,
                    method=str(
                        scope.get(
                            "method",
                            "",
                        )
                    ),
                    path=str(
                        scope.get(
                            "path",
                            "",
                        )
                    ),
                    status_code=(
                        response_status_code
                        if response_status_code is not None
                        else 500
                    ),
                    duration_ms=duration_ms,
                )
            )

        finally:
            _correlation_id_context.reset(context_token)


# CORRELATION BOUNDARY:
# Correlation IDs are UUIDs. Missing or malformed client values are replaced
# with backend-generated values and are never reflected directly.

# REQUEST STATE BOUNDARY:
# The active correlation ID is available through request.state and a
# ContextVar for trusted internal code. It is not persisted automatically.

# LOGGING PRIVACY BOUNDARY:
# Request logs contain only timestamp, level, event name, correlation ID,
# HTTP method, URL path, status code, and duration. They exclude request and
# response bodies, query strings, headers, cookies, credentials, JWTs,
# partner tokens, OTPs, source code, standard input, execution output,
# clipboard or paste contents, and surveillance information.

# ERROR BOUNDARY:
# Failed-request logs do not contain raw exception messages or tracebacks.
# The original exception is re-raised for FastAPI and deployment error
# handlers to process normally.
