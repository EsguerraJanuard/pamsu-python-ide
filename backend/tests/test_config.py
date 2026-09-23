import pytest

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES_ENV,
    ALLOWED_HOSTS_ENV,
    APPLICATION_ENVIRONMENT_ENV,
    CORRELATION_ID_HEADER_ENV,
    CORS_ALLOWED_ORIGINS_ENV,
    CORS_ALLOW_CREDENTIALS_ENV,
    DATABASE_URL_ENV,
    ENABLE_API_DOCS_ENV,
    JWT_ALGORITHM_ENV,
    JWT_SECRET_KEY_ENV,
    LOG_LEVEL_ENV,
    PARTNER_EXECUTION_TOKEN_ENV,
    SETTINGS_ENVIRONMENT_VARIABLES,
    ApplicationConfigurationError,
    clear_settings_cache,
    get_settings,
)


VALID_DATABASE_URL = "sqlite:///./config-test.db"
VALID_JWT_SECRET = "j" * 64
VALID_PARTNER_TOKEN = "p" * 64


@pytest.fixture(autouse=True)
def configure_valid_environment(
    monkeypatch: pytest.MonkeyPatch,
):
    for variable_name in SETTINGS_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(
            variable_name,
            raising=False,
        )

    monkeypatch.setenv(
        DATABASE_URL_ENV,
        VALID_DATABASE_URL,
    )
    monkeypatch.setenv(
        JWT_SECRET_KEY_ENV,
        VALID_JWT_SECRET,
    )

    clear_settings_cache()

    yield

    clear_settings_cache()


def test_default_settings_are_valid_and_safe() -> None:
    settings = get_settings()

    assert settings.environment == "development"
    assert settings.database_url.get_secret_value() == VALID_DATABASE_URL
    assert settings.jwt_secret_key.get_secret_value() == VALID_JWT_SECRET
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.partner_execution_token is None
    assert settings.partner_execution_token_configured is False
    assert settings.cors_allowed_origins == ()
    assert settings.cors_allow_credentials is False
    assert settings.allowed_hosts == ()
    assert settings.enable_api_docs is True
    assert settings.log_level == "INFO"
    assert settings.correlation_id_header == "X-Correlation-ID"


def test_settings_representation_does_not_disclose_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    settings_representation = repr(get_settings())

    assert VALID_DATABASE_URL not in settings_representation
    assert VALID_JWT_SECRET not in settings_representation
    assert VALID_PARTNER_TOKEN not in settings_representation


def test_settings_cache_tracks_environment_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_partner_token = "a" * 64
    second_partner_token = "b" * 64

    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        first_partner_token,
    )

    first_settings = get_settings()

    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        second_partner_token,
    )

    second_settings = get_settings()

    assert first_settings is not second_settings
    assert first_settings.partner_execution_token is not None
    assert second_settings.partner_execution_token is not None
    assert (
        first_settings.partner_execution_token.get_secret_value() == first_partner_token
    )
    assert (
        second_settings.partner_execution_token.get_secret_value()
        == second_partner_token
    )


def test_comma_separated_cors_origins_are_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CORS_ALLOWED_ORIGINS_ENV,
        ("http://localhost:5173, https://ide.example.edu, http://localhost:5173"),
    )
    monkeypatch.setenv(
        CORS_ALLOW_CREDENTIALS_ENV,
        "true",
    )

    settings = get_settings()

    assert settings.cors_allowed_origins == (
        "http://localhost:5173",
        "https://ide.example.edu",
    )
    assert settings.cors_allow_credentials is True


def test_json_cors_origin_list_is_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CORS_ALLOWED_ORIGINS_ENV,
        ('["http://localhost:5173", "https://ide.example.edu"]'),
    )

    settings = get_settings()

    assert settings.cors_allowed_origins == (
        "http://localhost:5173",
        "https://ide.example.edu",
    )


def test_production_defaults_disable_api_documentation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        APPLICATION_ENVIRONMENT_ENV,
        "production",
    )

    settings = get_settings()

    assert settings.environment == "production"
    assert settings.enable_api_docs is False


def test_api_documentation_setting_can_be_explicitly_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        APPLICATION_ENVIRONMENT_ENV,
        "production",
    )
    monkeypatch.setenv(
        ENABLE_API_DOCS_ENV,
        "true",
    )

    settings = get_settings()

    assert settings.enable_api_docs is True


def test_missing_database_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        DATABASE_URL_ENV,
        raising=False,
    )

    with pytest.raises(
        ApplicationConfigurationError,
        match="DATABASE_URL environment variable is not configured",
    ):
        get_settings()


def test_missing_jwt_secret_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        JWT_SECRET_KEY_ENV,
        raising=False,
    )

    with pytest.raises(
        ApplicationConfigurationError,
        match="JWT_SECRET_KEY environment variable is not configured",
    ):
        get_settings()


def test_short_jwt_secret_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        JWT_SECRET_KEY_ENV,
        "too-short",
    )

    with pytest.raises(
        ApplicationConfigurationError,
        match="at least 32 characters",
    ):
        get_settings()


@pytest.mark.parametrize(
    (
        "variable_name",
        "invalid_value",
        "expected_message",
    ),
    [
        (
            APPLICATION_ENVIRONMENT_ENV,
            "staging",
            "must be one of",
        ),
        (
            JWT_ALGORITHM_ENV,
            "RS256",
            "must be one of",
        ),
        (
            ACCESS_TOKEN_EXPIRE_MINUTES_ENV,
            "abc",
            "must be a whole number",
        ),
        (
            ACCESS_TOKEN_EXPIRE_MINUTES_ENV,
            "0",
            "must be greater than zero",
        ),
        (
            ACCESS_TOKEN_EXPIRE_MINUTES_ENV,
            "10081",
            "must not exceed 10080",
        ),
        (
            CORS_ALLOW_CREDENTIALS_ENV,
            "sometimes",
            "must be one of",
        ),
        (
            ENABLE_API_DOCS_ENV,
            "perhaps",
            "must be one of",
        ),
        (
            LOG_LEVEL_ENV,
            "TRACE",
            "must be one of",
        ),
        (
            CORRELATION_ID_HEADER_ENV,
            "X Correlation ID",
            "valid HTTP header name",
        ),
        (
            CORRELATION_ID_HEADER_ENV,
            "X-Correlation-ID:Unsafe",
            "valid HTTP header name",
        ),
    ],
)
def test_invalid_scalar_configuration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    variable_name: str,
    invalid_value: str,
    expected_message: str,
) -> None:
    monkeypatch.setenv(
        variable_name,
        invalid_value,
    )

    with pytest.raises(
        ApplicationConfigurationError,
        match=expected_message,
    ):
        get_settings()


@pytest.mark.parametrize(
    "invalid_origin",
    [
        "*",
        "localhost:5173",
        "https://ide.example.edu/path",
        "https://ide.example.edu?debug=true",
        "ftp://ide.example.edu",
    ],
)
def test_invalid_cors_origins_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    invalid_origin: str,
) -> None:
    monkeypatch.setenv(
        CORS_ALLOWED_ORIGINS_ENV,
        invalid_origin,
    )

    with pytest.raises(
        ApplicationConfigurationError,
    ):
        get_settings()


def test_production_rejects_non_https_cors_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        APPLICATION_ENVIRONMENT_ENV,
        "production",
    )
    monkeypatch.setenv(
        CORS_ALLOWED_ORIGINS_ENV,
        "http://ide.example.edu",
    )

    with pytest.raises(
        ApplicationConfigurationError,
        match="only HTTPS origins",
    ):
        get_settings()


def test_cors_credentials_require_explicit_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        CORS_ALLOW_CREDENTIALS_ENV,
        "true",
    )

    with pytest.raises(
        ApplicationConfigurationError,
        match="requires at least one explicit origin",
    ):
        get_settings()


@pytest.mark.parametrize(
    "invalid_hosts",
    [
        "https://api.example.edu",
        "api.example.edu/path",
    ],
)
def test_allowed_hosts_accept_hostnames_only(
    monkeypatch: pytest.MonkeyPatch,
    invalid_hosts: str,
) -> None:
    monkeypatch.setenv(
        ALLOWED_HOSTS_ENV,
        invalid_hosts,
    )

    with pytest.raises(
        ApplicationConfigurationError,
        match="host names only",
    ):
        get_settings()


def test_production_rejects_wildcard_allowed_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        APPLICATION_ENVIRONMENT_ENV,
        "production",
    )
    monkeypatch.setenv(
        ALLOWED_HOSTS_ENV,
        "*",
    )

    with pytest.raises(
        ApplicationConfigurationError,
        match="must not contain '\\*' in production",
    ):
        get_settings()


def test_missing_partner_token_does_not_block_core_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        raising=False,
    )

    settings = get_settings()

    assert settings.partner_execution_token is None
    assert settings.partner_execution_token_configured is False


def test_short_partner_token_is_reported_as_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        "too-short",
    )

    settings = get_settings()

    assert settings.partner_execution_token is not None
    assert settings.partner_execution_token_configured is False


def test_valid_partner_token_is_reported_as_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        PARTNER_EXECUTION_TOKEN_ENV,
        VALID_PARTNER_TOKEN,
    )

    settings = get_settings()

    assert settings.partner_execution_token is not None
    assert settings.partner_execution_token_configured is True
