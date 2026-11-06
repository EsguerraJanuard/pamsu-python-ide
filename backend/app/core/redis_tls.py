"""TLS options for rediss:// connections (Upstash in production).

The server certificate is verified, against certifi's CA bundle so the
result doesn't depend on the host's certificate store. Before this, both
the API's Redis client and Celery used ssl_cert_reqs=none, which accepts
any certificate and leaves the connection open to interception.

REDIS_SSL_CERT_REQS=none switches verification off again. It's only an
emergency switch for the case where the provider's certificate stops
validating; on Render it takes effect with "Save and deploy".
"""

import logging
import os
import ssl

logger = logging.getLogger(__name__)

CERT_REQS_ENV = "REDIS_SSL_CERT_REQS"


def redis_ssl_cert_reqs() -> ssl.VerifyMode:
    """CERT_REQUIRED unless REDIS_SSL_CERT_REQS is exactly "none"."""

    value = os.getenv(CERT_REQS_ENV, "").strip().lower()

    if value == "none":
        logger.warning(
            "Redis TLS certificate verification is OFF (%s=none).",
            CERT_REQS_ENV,
        )
        return ssl.CERT_NONE

    if value not in ("", "required"):
        logger.warning(
            "Ignoring unknown %s value; verifying certificates.",
            CERT_REQS_ENV,
        )

    return ssl.CERT_REQUIRED


def _ca_bundle_path() -> str | None:
    try:
        import certifi
    except ImportError:
        return None

    return certifi.where()


def redis_tls_options(url: str) -> dict | None:
    """
    ssl_* options for a Redis URL, or None when the URL isn't rediss://.

    The keys are the ones redis-py and Celery's broker_use_ssl /
    redis_backend_use_ssl both accept.
    """

    if not url.startswith("rediss://"):
        return None

    cert_reqs = redis_ssl_cert_reqs()
    options: dict = {"ssl_cert_reqs": cert_reqs}

    if cert_reqs != ssl.CERT_NONE:
        ca_bundle = _ca_bundle_path()
        if ca_bundle:
            options["ssl_ca_certs"] = ca_bundle

    return options
