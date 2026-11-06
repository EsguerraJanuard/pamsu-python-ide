"""TLS certificate checks for rediss:// ("Full backend audit", Still open, item 10).

Both the API's Redis client and Celery used ssl_cert_reqs=none, which accepts
any certificate. They now verify it (app.core.redis_tls), with
REDIS_SSL_CERT_REQS=none kept as an emergency switch.
"""

import logging
import os
import ssl
import subprocess
import sys
from pathlib import Path

import certifi
import pytest

from app.core.redis_tls import redis_tls_options

BACKEND_DIR = Path(__file__).resolve().parents[1]
TLS_URL = "rediss://default:not-a-secret@redis.example.invalid:6379/0"


@pytest.fixture(autouse=True)
def clear_switch(monkeypatch):
    monkeypatch.delenv("REDIS_SSL_CERT_REQS", raising=False)


def test_plain_redis_urls_get_no_tls_options():
    assert redis_tls_options("redis://localhost:6379/0") is None


@pytest.mark.parametrize("value", [None, "required", " REQUIRED "])
def test_rediss_verifies_against_the_certifi_bundle(monkeypatch, value):
    if value is not None:
        monkeypatch.setenv("REDIS_SSL_CERT_REQS", value)

    assert redis_tls_options(TLS_URL) == {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
        "ssl_ca_certs": certifi.where(),
    }


def test_none_switches_verification_off_with_a_warning(monkeypatch, caplog):
    monkeypatch.setenv("REDIS_SSL_CERT_REQS", "none")

    with caplog.at_level(logging.WARNING, logger="app.core.redis_tls"):
        options = redis_tls_options(TLS_URL)

    assert options == {"ssl_cert_reqs": ssl.CERT_NONE}
    assert "verification is OFF" in caplog.text


@pytest.mark.parametrize("value", ["off", "false", "optional", "0"])
def test_unknown_values_still_verify(monkeypatch, caplog, value):
    monkeypatch.setenv("REDIS_SSL_CERT_REQS", value)

    with caplog.at_level(logging.WARNING, logger="app.core.redis_tls"):
        options = redis_tls_options(TLS_URL)

    assert options["ssl_cert_reqs"] == ssl.CERT_REQUIRED
    assert "Ignoring unknown" in caplog.text
    assert value not in caplog.text


def test_without_certifi_the_system_store_is_used(monkeypatch):
    monkeypatch.setitem(sys.modules, "certifi", None)

    assert redis_tls_options(TLS_URL) == {"ssl_cert_reqs": ssl.CERT_REQUIRED}


@pytest.mark.parametrize("switch", ["", "none"])
def test_api_client_and_celery_use_the_same_tls_options(switch):
    # The clients are built at import time, so check them in a fresh process.
    script = (
        "import ssl\n"
        "from app.core.redis_client import redis_client\n"
        "from app.tasks.celery_worker import celery\n"
        "pool = redis_client.connection_pool\n"
        "print(pool.connection_class.__name__)\n"
        "print(int(pool.connection_kwargs['ssl_cert_reqs']))\n"
        "print(pool.connection_kwargs.get('ssl_ca_certs') or '-')\n"
        "print(int(celery.conf.broker_use_ssl['ssl_cert_reqs']))\n"
        "print(celery.conf.broker_use_ssl.get('ssl_ca_certs') or '-')\n"
        "print(celery.conf.broker_use_ssl == celery.conf.redis_backend_use_ssl)\n"
    )
    env = {key: value for key, value in os.environ.items() if key not in ("DATABASE_URL", "PAMSU_TEST_DATABASE_URL")}
    env["REDIS_URL"] = TLS_URL
    env["REDIS_SSL_CERT_REQS"] = switch

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stderr[-2000:]
    lines = result.stdout.strip().splitlines()[-6:]
    expected_reqs = ssl.CERT_NONE if switch == "none" else ssl.CERT_REQUIRED
    expected_ca = "-" if switch == "none" else certifi.where()
    assert lines == [
        "SSLConnection",
        str(int(expected_reqs)),
        expected_ca,
        str(int(expected_reqs)),
        expected_ca,
        "True",
    ]
