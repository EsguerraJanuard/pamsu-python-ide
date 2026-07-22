import hashlib
import json
import os
from functools import lru_cache
from typing import Literal, cast
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr


load_dotenv()


ApplicationEnvironment = Literal[
    "development",
    "test",
    "production",
]

SupportedJWTAlgorithm = Literal[
    "HS256",
    "HS384",
    "HS512",
]

SupportedLogLevel = Literal[
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


DATABASE_URL_ENV = "DATABASE_URL"
JWT_SECRET_KEY_ENV = "JWT_SECRET_KEY"
JWT_ALGORITHM_ENV = "JWT_ALGORITHM"
ACCESS_TOKEN_EXPIRE_MINUTES_ENV = "ACCESS_TOKEN_EXPIRE_MINUTES"

APPLICATION_ENVIRONMENT_ENV = "PAMSU_ENVIRONMENT"
PARTNER_EXECUTION_TOKEN_ENV = "PAMSU_PARTNER_EXECUTION_TOKEN"

CORS_ALLOWED_ORIGINS_ENV = "PAMSU_CORS_ALLOWED_ORIGINS"
CORS_ALLOW_CREDENTIALS_ENV = "PAMSU_CORS_ALLOW_CREDENTIALS"

ALLOWED_HOSTS_ENV = "PAMSU_ALLOWED_HOSTS"
ENABLE_API_DOCS_ENV = "PAMSU_ENABLE_API_DOCS"

LOG_LEVEL_ENV = "PAMSU_LOG_LEVEL"
CORRELATION_ID_HEADER_ENV = "PAMSU_CORRELATION_ID_HEADER"


DEFAULT_APPLICATION_ENVIRONMENT: ApplicationEnvironment = "development"
DEFAULT_JWT_ALGORITHM: SupportedJWTAlgorithm = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_LOG_LEVEL: SupportedLogLevel = "INFO"
DEFAULT_CORRELATION_ID_HEADER = "X-Correlation-ID"

MIN_JWT_SECRET_KEY_LENGTH = 32
MIN_PARTNER_EXECUTION_TOKEN_LENGTH = 32
MAX_ACCESS_TOKEN_EXPIRE_MINUTES = 10_080
MAX_CORRELATION_ID_HEADER_LENGTH = 100

SETTINGS_ENVIRONMENT_VARIABLES = (
    DATABASE_URL_ENV,
    JWT_SECRET_KEY_ENV,
    JWT_ALGORITHM_ENV,
    ACCESS_TOKEN_EXPIRE_MINUTES_ENV,
    APPLICATION_ENVIRONMENT_ENV,
    PARTNER_EXECUTION_TOKEN_ENV,
    CORS_ALLOWED_ORIGINS_ENV,
    CORS_ALLOW_CREDENTIALS_ENV,
    ALLOWED_HOSTS_ENV,
    ENABLE_API_DOCS_ENV,
    LOG_LEVEL_ENV,
    CORRELATION_ID_HEADER_ENV,
)


class ApplicationConfigurationError(RuntimeError):
    """Raised when application environment configuration is invalid."""


class ApplicationSettings(BaseModel):
    environment: ApplicationEnvironment

    database_url: SecretStr = Field(
        repr=False,
    )

    jwt_secret_key: SecretStr = Field(
        repr=False,
    )
    jwt_algorithm: SupportedJWTAlgorithm
    access_token_expire_minutes: int

    partner_execution_token: SecretStr | None = Field(
        default=None,
        repr=False,
    )

    cors_allowed_origins: tuple[str, ...]
    cors_allow_credentials: bool

    allowed_hosts: tuple[str, ...]
    enable_api_docs: bool

    log_level: SupportedLogLevel
    correlation_id_header: str

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def partner_execution_token_configured(
        self,
    ) -> bool:
        if self.partner_execution_token is None:
            return False

        return (
            len(self.partner_execution_token.get_secret_value())
            >= MIN_PARTNER_EXECUTION_TOKEN_LENGTH
        )


def _read_environment_value(
    name: str,
    *,
    default: str | None = None,
) -> str:
    value = os.getenv(
        name,
        default,
    )

    if value is None:
        return ""

    return value.strip()


def _require_environment_value(
    name: str,
) -> str:
    value = _read_environment_value(name)

    if not value:
        raise ApplicationConfigurationError(
            f"{name} environment variable is not configured."
        )

    return value


def _parse_application_environment(
    raw_value: str,
) -> ApplicationEnvironment:
    normalized = raw_value.strip().lower()

    allowed_values = {
        "development",
        "test",
        "production",
    }

    if normalized not in allowed_values:
        raise ApplicationConfigurationError(
            f"{APPLICATION_ENVIRONMENT_ENV} must be one of: "
            "development, test, or production."
        )

    return cast(
        ApplicationEnvironment,
        normalized,
    )


def _parse_jwt_algorithm(
    raw_value: str,
) -> SupportedJWTAlgorithm:
    normalized = raw_value.strip().upper()

    supported_algorithms = {
        "HS256",
        "HS384",
        "HS512",
    }

    if normalized not in supported_algorithms:
        raise ApplicationConfigurationError(
            f"{JWT_ALGORITHM_ENV} must be one of: HS256, HS384, or HS512."
        )

    return cast(
        SupportedJWTAlgorithm,
        normalized,
    )


def _parse_log_level(
    raw_value: str,
) -> SupportedLogLevel:
    normalized = raw_value.strip().upper()

    supported_levels = {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }

    if normalized not in supported_levels:
        raise ApplicationConfigurationError(
            f"{LOG_LEVEL_ENV} must be one of: DEBUG, INFO, WARNING, ERROR, or CRITICAL."
        )

    return cast(
        SupportedLogLevel,
        normalized,
    )


def _parse_positive_integer(
    *,
    name: str,
    raw_value: str,
    maximum: int | None = None,
) -> int:
    try:
        parsed_value = int(raw_value)
    except (
        TypeError,
        ValueError,
    ) as error:
        raise ApplicationConfigurationError(
            f"{name} must be a whole number."
        ) from error

    if parsed_value <= 0:
        raise ApplicationConfigurationError(f"{name} must be greater than zero.")

    if maximum is not None and parsed_value > maximum:
        raise ApplicationConfigurationError(f"{name} must not exceed {maximum}.")

    return parsed_value


def _parse_boolean(
    *,
    name: str,
    raw_value: str,
) -> bool:
    normalized = raw_value.strip().lower()

    true_values = {
        "1",
        "true",
        "yes",
        "on",
    }

    false_values = {
        "0",
        "false",
        "no",
        "off",
    }

    if normalized in true_values:
        return True

    if normalized in false_values:
        return False

    raise ApplicationConfigurationError(
        f"{name} must be one of: true, false, 1, 0, yes, no, on, or off."
    )


def _parse_string_list(
    *,
    name: str,
    raw_value: str,
) -> tuple[str, ...]:
    normalized = raw_value.strip()

    if not normalized:
        return ()

    values: list[str]

    if normalized.startswith("["):
        try:
            decoded_value = json.loads(normalized)
        except json.JSONDecodeError as error:
            raise ApplicationConfigurationError(
                f"{name} must be a comma-separated list or a JSON array of strings."
            ) from error

        if not isinstance(
            decoded_value,
            list,
        ) or not all(
            isinstance(
                item,
                str,
            )
            for item in decoded_value
        ):
            raise ApplicationConfigurationError(
                f"{name} JSON value must be an array of strings."
            )

        values = decoded_value
    else:
        values = normalized.split(",")

    cleaned_values: list[str] = []
    seen_values: set[str] = set()

    for value in values:
        cleaned_value = value.strip()

        if not cleaned_value:
            continue

        if cleaned_value in seen_values:
            continue

        seen_values.add(cleaned_value)
        cleaned_values.append(cleaned_value)

    return tuple(cleaned_values)


def _validate_cors_origins(
    *,
    origins: tuple[str, ...],
    environment: ApplicationEnvironment,
    allow_credentials: bool,
) -> tuple[str, ...]:
    for origin in origins:
        if origin == "*":
            raise ApplicationConfigurationError(
                f"{CORS_ALLOWED_ORIGINS_ENV} must not contain '*'. "
                "Configure explicit trusted origins."
            )

        parsed_origin = urlparse(origin)

        if (
            parsed_origin.scheme
            not in {
                "http",
                "https",
            }
            or not parsed_origin.netloc
            or parsed_origin.path
            not in {
                "",
                "/",
            }
            or parsed_origin.params
            or parsed_origin.query
            or parsed_origin.fragment
        ):
            raise ApplicationConfigurationError(
                f"{CORS_ALLOWED_ORIGINS_ENV} contains an invalid "
                f"origin: {origin!r}. Use values such as "
                "'https://ide.example.edu'."
            )

        if environment == "production" and parsed_origin.scheme != "https":
            raise ApplicationConfigurationError(
                f"{CORS_ALLOWED_ORIGINS_ENV} must contain only "
                "HTTPS origins in production."
            )

    if allow_credentials and not origins:
        raise ApplicationConfigurationError(
            f"{CORS_ALLOW_CREDENTIALS_ENV}=true requires at "
            f"least one explicit origin in "
            f"{CORS_ALLOWED_ORIGINS_ENV}."
        )

    return origins


def _validate_allowed_hosts(
    *,
    hosts: tuple[str, ...],
    environment: ApplicationEnvironment,
) -> tuple[str, ...]:
    for host in hosts:
        if "://" in host or "/" in host:
            raise ApplicationConfigurationError(
                f"{ALLOWED_HOSTS_ENV} must contain host names "
                "only, without URL schemes or paths."
            )

        if host == "*" and environment == "production":
            raise ApplicationConfigurationError(
                f"{ALLOWED_HOSTS_ENV} must not contain '*' in production."
            )

    return hosts


def _validate_correlation_id_header(
    raw_value: str,
) -> str:
    normalized = raw_value.strip()

    if not normalized:
        raise ApplicationConfigurationError(
            f"{CORRELATION_ID_HEADER_ENV} must not be blank."
        )

    if len(normalized) > MAX_CORRELATION_ID_HEADER_LENGTH:
        raise ApplicationConfigurationError(
            f"{CORRELATION_ID_HEADER_ENV} must not exceed "
            f"{MAX_CORRELATION_ID_HEADER_LENGTH} characters."
        )

    if any(
        character.isspace()
        or character
        in {
            ":",
            "\r",
            "\n",
        }
        for character in normalized
    ):
        raise ApplicationConfigurationError(
            f"{CORRELATION_ID_HEADER_ENV} must be a valid HTTP header name."
        )

    return normalized


def _load_application_settings() -> ApplicationSettings:
    environment = _parse_application_environment(
        _read_environment_value(
            APPLICATION_ENVIRONMENT_ENV,
            default=DEFAULT_APPLICATION_ENVIRONMENT,
        )
    )

    database_url = _require_environment_value(
        DATABASE_URL_ENV,
    )

    jwt_secret_key = _require_environment_value(
        JWT_SECRET_KEY_ENV,
    )

    if len(jwt_secret_key) < MIN_JWT_SECRET_KEY_LENGTH:
        raise ApplicationConfigurationError(
            f"{JWT_SECRET_KEY_ENV} must be configured with "
            f"at least {MIN_JWT_SECRET_KEY_LENGTH} characters."
        )

    jwt_algorithm = _parse_jwt_algorithm(
        _read_environment_value(
            JWT_ALGORITHM_ENV,
            default=DEFAULT_JWT_ALGORITHM,
        )
    )

    access_token_expire_minutes = _parse_positive_integer(
        name=ACCESS_TOKEN_EXPIRE_MINUTES_ENV,
        raw_value=_read_environment_value(
            ACCESS_TOKEN_EXPIRE_MINUTES_ENV,
            default=str(DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        maximum=MAX_ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    raw_partner_execution_token = _read_environment_value(
        PARTNER_EXECUTION_TOKEN_ENV,
    )

    partner_execution_token = (
        SecretStr(raw_partner_execution_token) if raw_partner_execution_token else None
    )

    cors_allowed_origins = _parse_string_list(
        name=CORS_ALLOWED_ORIGINS_ENV,
        raw_value=_read_environment_value(
            CORS_ALLOWED_ORIGINS_ENV,
        ),
    )

    cors_allow_credentials = _parse_boolean(
        name=CORS_ALLOW_CREDENTIALS_ENV,
        raw_value=_read_environment_value(
            CORS_ALLOW_CREDENTIALS_ENV,
            default="false",
        ),
    )

    cors_allowed_origins = _validate_cors_origins(
        origins=cors_allowed_origins,
        environment=environment,
        allow_credentials=cors_allow_credentials,
    )

    allowed_hosts = _parse_string_list(
        name=ALLOWED_HOSTS_ENV,
        raw_value=_read_environment_value(
            ALLOWED_HOSTS_ENV,
        ),
    )

    allowed_hosts = _validate_allowed_hosts(
        hosts=allowed_hosts,
        environment=environment,
    )

    default_enable_api_docs = "false" if environment == "production" else "true"

    enable_api_docs = _parse_boolean(
        name=ENABLE_API_DOCS_ENV,
        raw_value=_read_environment_value(
            ENABLE_API_DOCS_ENV,
            default=default_enable_api_docs,
        ),
    )

    log_level = _parse_log_level(
        _read_environment_value(
            LOG_LEVEL_ENV,
            default=DEFAULT_LOG_LEVEL,
        )
    )

    correlation_id_header = _validate_correlation_id_header(
        _read_environment_value(
            CORRELATION_ID_HEADER_ENV,
            default=DEFAULT_CORRELATION_ID_HEADER,
        )
    )

    return ApplicationSettings(
        environment=environment,
        database_url=SecretStr(database_url),
        jwt_secret_key=SecretStr(jwt_secret_key),
        jwt_algorithm=jwt_algorithm,
        access_token_expire_minutes=(access_token_expire_minutes),
        partner_execution_token=(partner_execution_token),
        cors_allowed_origins=(cors_allowed_origins),
        cors_allow_credentials=(cors_allow_credentials),
        allowed_hosts=allowed_hosts,
        enable_api_docs=enable_api_docs,
        log_level=log_level,
        correlation_id_header=(correlation_id_header),
    )


def _build_environment_fingerprint() -> tuple[str, ...]:
    """
    Build a non-reversible fingerprint of the relevant environment.

    This allows isolated tests to modify environment variables without
    exposing secret values inside cache keys or requiring request handlers
    to clear global configuration state manually.
    """

    fingerprints: list[str] = []

    for variable_name in SETTINGS_ENVIRONMENT_VARIABLES:
        raw_value = (
            os.getenv(
                variable_name,
                "",
            )
            or ""
        ).strip()

        value_digest = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()

        fingerprints.append(f"{variable_name}:{value_digest}")

    return tuple(fingerprints)


@lru_cache(maxsize=8)
def _get_cached_settings(
    environment_fingerprint: tuple[str, ...],
) -> ApplicationSettings:
    """
    Cache one settings object for each distinct environment snapshot.

    The fingerprint parameter is intentionally used only as the cache key.
    Actual values are parsed from the current process environment.
    """

    del environment_fingerprint

    return _load_application_settings()


def get_settings() -> ApplicationSettings:
    """
    Return validated immutable settings for the current environment.

    Secrets remain wrapped in SecretStr. A new cached settings object is
    created only when one of the recognized environment variables changes.
    """

    return _get_cached_settings(_build_environment_fingerprint())


def clear_settings_cache() -> None:
    """
    Clear all cached environment snapshots for isolated tests.
    """

    _get_cached_settings.cache_clear()


# CONFIGURATION BOUNDARY:
# Environment variables are parsed and validated only through this module.
# Settings are cached per recognized process-environment snapshot.

# SECRET HANDLING BOUNDARY:
# Database credentials, JWT signing secrets, and execution-partner tokens
# remain wrapped in SecretStr. Cache keys contain only SHA-256 digests.

# PARTNER AUTH BOUNDARY:
# A missing or short execution-partner token does not prevent the core API
# from starting. The partner-auth dependency and readiness endpoint report
# that required integration as unavailable.

# CORS BOUNDARY:
# Wildcard origins are rejected. Production permits HTTPS origins only.
# Credentials require an explicit non-empty trusted-origin allowlist.

# DOCUMENTATION BOUNDARY:
# API documentation defaults to enabled in development and test
# environments and disabled in production.

# HOST BOUNDARY:
# Production cannot use a wildcard trusted-host configuration.
