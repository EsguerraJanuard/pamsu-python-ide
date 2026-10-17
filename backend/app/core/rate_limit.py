"""
Fixed-window rate limiting backed by the shared Redis instance.

Authenticated routes are limited per account, never per IP address. On
Render every request reaches the app through the platform proxy, so
request.client.host is the proxy's address for all users; an IP-keyed limit
would act as one global bucket for the whole school. Anonymous routes are
limited per submitted identifier (an email, an OTP challenge) and, where an
IP key is still useful, with limits generous enough for a shared address.

When Redis is unreachable the limiter fails open and logs a warning: the
platform keeps working, and the same outage already stops the execution
queue and token revocation, which are reported elsewhere.
"""

import hashlib
import logging

from app.core.redis_client import redis_client
from fastapi import Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)

RATE_LIMIT_KEY_PREFIX = "rl"


class RateLimitExceededError(Exception):
    def __init__(self, retry_after_seconds: int):
        super().__init__("Rate limit exceeded.")
        self.retry_after_seconds = retry_after_seconds


def _hash_identifier(identifier: str) -> str:
    # Keys never contain raw emails or other personal identifiers.
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:32]


def hit_rate_limit(*, scope: str, identifier: str, limit: int, window_seconds: int) -> None:
    """
    Count one request for (scope, identifier) and raise
    RateLimitExceededError once more than `limit` arrive in the window.
    """

    key = f"{RATE_LIMIT_KEY_PREFIX}:{scope}:{_hash_identifier(identifier)}"

    try:
        count = redis_client.incr(key)

        if count == 1:
            redis_client.expire(key, window_seconds)

        if count > limit:
            ttl = redis_client.ttl(key)
            raise RateLimitExceededError(ttl if isinstance(ttl, int) and ttl > 0 else window_seconds)
    except RateLimitExceededError:
        raise
    except Exception:
        logger.warning("Rate limiter unavailable for scope %s; request allowed.", scope)


def too_many_requests(retry_after_seconds: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please wait a moment and try again.",
        headers={"Retry-After": str(retry_after_seconds)},
    )


def enforce_rate_limit(*, scope: str, identifier: str, limit: int, window_seconds: int) -> None:
    """hit_rate_limit() that raises the HTTP 429 response directly."""

    try:
        hit_rate_limit(scope=scope, identifier=identifier, limit=limit, window_seconds=window_seconds)
    except RateLimitExceededError as error:
        raise too_many_requests(error.retry_after_seconds) from error


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def limit_per_ip(scope: str, *, limit: int, window_seconds: int):
    """Dependency for anonymous routes. See the module note on shared IPs."""

    def dependency(request: Request) -> None:
        enforce_rate_limit(
            scope=scope,
            identifier=client_ip(request),
            limit=limit,
            window_seconds=window_seconds,
        )

    return dependency


def limit_per_user(scope: str, *, limit: int, window_seconds: int):
    """Dependency for authenticated routes, keyed by the verified account."""

    from app.core.security import get_current_user
    from app.models.domain_models import User

    def dependency(current_user: User = Depends(get_current_user)) -> None:
        enforce_rate_limit(
            scope=scope,
            identifier=str(current_user.user_id),
            limit=limit,
            window_seconds=window_seconds,
        )

    return dependency
