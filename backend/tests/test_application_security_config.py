import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]

CONFIGURATION_ENVIRONMENT_VARIABLES = {
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "JWT_ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "PAMSU_ENVIRONMENT",
    "PAMSU_PARTNER_EXECUTION_TOKEN",
    "PAMSU_CORS_ALLOWED_ORIGINS",
    "PAMSU_CORS_ALLOW_CREDENTIALS",
    "PAMSU_ALLOWED_HOSTS",
    "PAMSU_ENABLE_API_DOCS",
    "PAMSU_LOG_LEVEL",
    "PAMSU_CORRELATION_ID_HEADER",
}

VALID_JWT_SECRET = "j" * 64
VALID_PARTNER_TOKEN = "p" * 64


def _build_subprocess_environment(
    overrides: Mapping[str, str | None] | None = None,
) -> dict[str, str]:
    environment = os.environ.copy()

    for variable_name in CONFIGURATION_ENVIRONMENT_VARIABLES:
        environment.pop(variable_name, None)

    environment.update(
        {
            "DATABASE_URL": "sqlite://",
            "JWT_SECRET_KEY": VALID_JWT_SECRET,
            "JWT_ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "PAMSU_ENVIRONMENT": "development",
            "PAMSU_PARTNER_EXECUTION_TOKEN": VALID_PARTNER_TOKEN,
            "PAMSU_CORS_ALLOWED_ORIGINS": "",
            "PAMSU_CORS_ALLOW_CREDENTIALS": "false",
            "PAMSU_ALLOWED_HOSTS": "",
            "PAMSU_ENABLE_API_DOCS": "true",
            "PAMSU_LOG_LEVEL": "INFO",
            "PAMSU_CORRELATION_ID_HEADER": "X-Correlation-ID",
        }
    )

    if overrides is not None:
        for variable_name, value in overrides.items():
            if value is None:
                environment.pop(variable_name, None)
            else:
                environment[variable_name] = value

    existing_python_path = environment.get("PYTHONPATH", "")
    python_path_parts = [str(BACKEND_ROOT)]

    if existing_python_path:
        python_path_parts.append(existing_python_path)

    environment["PYTHONPATH"] = os.pathsep.join(python_path_parts)

    return environment


def _run_python(
    *,
    temporary_directory: Path,
    script: str,
    overrides: Mapping[str, str | None] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-c",
            script,
        ],
        cwd=temporary_directory,
        env=_build_subprocess_environment(overrides),
        capture_output=True,
        text=True,
        check=False,
    )


def _parse_json_probe(
    result: subprocess.CompletedProcess[str],
) -> dict[str, object]:
    assert result.returncode == 0, (
        f"Application probe failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    assert output_lines, (
        f"Application probe returned no JSON output.\nSTDERR:\n{result.stderr}"
    )

    parsed = json.loads(output_lines[-1])

    assert isinstance(parsed, dict)

    return parsed


def test_explicit_cors_origin_supports_approved_frontend_headers(
    tmp_path: Path,
) -> None:
    allowed_origin = "https://ide.example.edu"

    result = _run_python(
        temporary_directory=tmp_path,
        overrides={
            "PAMSU_CORS_ALLOWED_ORIGINS": allowed_origin,
            "PAMSU_CORS_ALLOW_CREDENTIALS": "true",
        },
        script=r"""
import json

from fastapi.testclient import TestClient

from app.main import app


allowed_origin = "https://ide.example.edu"
denied_origin = "https://untrusted.example.edu"

with TestClient(app) as client:
    approved_preflight = client.options(
        "/health",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": (
                "Authorization, Content-Type, "
                "Idempotency-Key, X-Correlation-ID"
            ),
        },
    )

    approved_response = client.get(
        "/health",
        headers={
            "Origin": allowed_origin,
        },
    )

    denied_preflight = client.options(
        "/health",
        headers={
            "Origin": denied_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    print(
        json.dumps(
            {
                "approved_preflight_status": approved_preflight.status_code,
                "approved_allow_origin": approved_preflight.headers.get(
                    "access-control-allow-origin"
                ),
                "approved_allow_credentials": approved_preflight.headers.get(
                    "access-control-allow-credentials"
                ),
                "approved_allow_methods": approved_preflight.headers.get(
                    "access-control-allow-methods",
                    "",
                ).lower(),
                "approved_allow_headers": approved_preflight.headers.get(
                    "access-control-allow-headers",
                    "",
                ).lower(),
                "approved_max_age": approved_preflight.headers.get(
                    "access-control-max-age"
                ),
                "actual_status": approved_response.status_code,
                "actual_allow_origin": approved_response.headers.get(
                    "access-control-allow-origin"
                ),
                "actual_expose_headers": approved_response.headers.get(
                    "access-control-expose-headers",
                    "",
                ).lower(),
                "denied_preflight_status": denied_preflight.status_code,
                "denied_allow_origin": denied_preflight.headers.get(
                    "access-control-allow-origin"
                ),
            }
        )
    )
""",
    )

    probe = _parse_json_probe(result)

    assert probe["approved_preflight_status"] == 200
    assert probe["approved_allow_origin"] == allowed_origin
    assert probe["approved_allow_credentials"] == "true"
    assert probe["approved_max_age"] == "600"

    allowed_methods = str(probe["approved_allow_methods"])

    for method in (
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "options",
    ):
        assert method in allowed_methods

    allowed_headers = str(probe["approved_allow_headers"])

    for header in (
        "authorization",
        "content-type",
        "idempotency-key",
        "x-correlation-id",
    ):
        assert header in allowed_headers

    assert probe["actual_status"] == 200
    assert probe["actual_allow_origin"] == allowed_origin
    assert "x-correlation-id" in str(probe["actual_expose_headers"])

    assert probe["denied_preflight_status"] == 400
    assert probe["denied_allow_origin"] is None


def test_no_cors_allowlist_produces_no_cors_response_headers(
    tmp_path: Path,
) -> None:
    result = _run_python(
        temporary_directory=tmp_path,
        script=r"""
import json

from fastapi.testclient import TestClient

from app.main import app


with TestClient(app) as client:
    response = client.get(
        "/health",
        headers={
            "Origin": "https://unconfigured.example.edu",
        },
    )

    print(
        json.dumps(
            {
                "status": response.status_code,
                "allow_origin": response.headers.get(
                    "access-control-allow-origin"
                ),
                "allow_credentials": response.headers.get(
                    "access-control-allow-credentials"
                ),
            }
        )
    )
""",
    )

    probe = _parse_json_probe(result)

    assert probe == {
        "status": 200,
        "allow_origin": None,
        "allow_credentials": None,
    }


def test_trusted_host_middleware_accepts_only_configured_hosts(
    tmp_path: Path,
) -> None:
    result = _run_python(
        temporary_directory=tmp_path,
        overrides={
            "PAMSU_ALLOWED_HOSTS": "api.example.edu,testserver",
        },
        script=r"""
import json

from fastapi.testclient import TestClient

from app.main import app


with TestClient(app) as client:
    allowed_response = client.get(
        "/health",
        headers={
            "Host": "api.example.edu",
        },
    )

    test_client_response = client.get(
        "/health",
        headers={
            "Host": "testserver",
        },
    )

    denied_response = client.get(
        "/health",
        headers={
            "Host": "evil.example.com",
        },
    )

    print(
        json.dumps(
            {
                "allowed_status": allowed_response.status_code,
                "test_client_status": test_client_response.status_code,
                "denied_status": denied_response.status_code,
                "denied_body": denied_response.text,
            }
        )
    )
""",
    )

    probe = _parse_json_probe(result)

    assert probe["allowed_status"] == 200
    assert probe["test_client_status"] == 200
    assert probe["denied_status"] == 400
    assert "invalid host header" in str(probe["denied_body"]).lower()


def test_production_defaults_disable_api_documentation(
    tmp_path: Path,
) -> None:
    result = _run_python(
        temporary_directory=tmp_path,
        overrides={
            "PAMSU_ENVIRONMENT": "production",
            "PAMSU_ALLOWED_HOSTS": "testserver",
            "PAMSU_ENABLE_API_DOCS": None,
        },
        script=r"""
import json

from fastapi.testclient import TestClient

from app.main import app


with TestClient(app) as client:
    root_response = client.get("/")
    docs_response = client.get("/docs")
    redoc_response = client.get("/redoc")
    openapi_response = client.get("/openapi.json")

    print(
        json.dumps(
            {
                "docs_url": app.docs_url,
                "redoc_url": app.redoc_url,
                "openapi_url": app.openapi_url,
                "root_status": root_response.status_code,
                "documentation_value": root_response.json()["documentation"],
                "docs_status": docs_response.status_code,
                "redoc_status": redoc_response.status_code,
                "openapi_status": openapi_response.status_code,
            }
        )
    )
""",
    )

    probe = _parse_json_probe(result)

    assert probe == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
        "root_status": 200,
        "documentation_value": "disabled",
        "docs_status": 404,
        "redoc_status": 404,
        "openapi_status": 404,
    }


def test_development_defaults_enable_api_documentation(
    tmp_path: Path,
) -> None:
    result = _run_python(
        temporary_directory=tmp_path,
        overrides={
            "PAMSU_ENVIRONMENT": "development",
            "PAMSU_ENABLE_API_DOCS": None,
        },
        script=r"""
import json

from fastapi.testclient import TestClient

from app.main import app


with TestClient(app) as client:
    docs_response = client.get("/docs")
    redoc_response = client.get("/redoc")
    openapi_response = client.get("/openapi.json")

    print(
        json.dumps(
            {
                "docs_url": app.docs_url,
                "redoc_url": app.redoc_url,
                "openapi_url": app.openapi_url,
                "docs_status": docs_response.status_code,
                "redoc_status": redoc_response.status_code,
                "openapi_status": openapi_response.status_code,
            }
        )
    )
""",
    )

    probe = _parse_json_probe(result)

    assert probe == {
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "docs_status": 200,
        "redoc_status": 200,
        "openapi_status": 200,
    }


@pytest.mark.parametrize(
    (
        "environment_overrides",
        "expected_message",
    ),
    [
        (
            {
                "PAMSU_ENVIRONMENT": "production",
                "PAMSU_ALLOWED_HOSTS": "testserver",
                "PAMSU_CORS_ALLOWED_ORIGINS": "*",
            },
            "PAMSU_CORS_ALLOWED_ORIGINS must not contain '*'",
        ),
        (
            {
                "PAMSU_ENVIRONMENT": "production",
                "PAMSU_ALLOWED_HOSTS": "*",
            },
            "PAMSU_ALLOWED_HOSTS must not contain '*' in production",
        ),
    ],
)
def test_unsafe_wildcard_configuration_blocks_application_startup(
    tmp_path: Path,
    environment_overrides: dict[str, str],
    expected_message: str,
) -> None:
    result = _run_python(
        temporary_directory=tmp_path,
        overrides=environment_overrides,
        script="from app.main import app",
    )

    assert result.returncode != 0
    assert expected_message in result.stderr

    combined_output = result.stdout + result.stderr

    for prohibited_value in (
        VALID_JWT_SECRET,
        VALID_PARTNER_TOKEN,
        "sqlite://",
    ):
        assert prohibited_value not in combined_output
