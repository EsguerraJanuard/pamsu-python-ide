import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import SessionLocal, engine, engine_options


SENSITIVE_VALUE = "pbkdf2-sha256$leak-canary-7f3c9a"


def _build_canary_table() -> Table:
    return Table(
        "leak_canary_credentials",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("password_hash", String(255), nullable=False, unique=True),
    )


def _violate_unique_constraint(session_factory, bind) -> IntegrityError:
    credentials = _build_canary_table()
    credentials.create(bind, checkfirst=True)

    session = session_factory()

    try:
        session.execute(
            credentials.insert().values(password_hash=SENSITIVE_VALUE)
        )

        with pytest.raises(IntegrityError) as raised:
            session.execute(
                credentials.insert().values(password_hash=SENSITIVE_VALUE)
            )
            session.commit()

        return raised.value
    finally:
        session.rollback()
        session.close()
        credentials.drop(bind, checkfirst=True)


def test_application_engine_hides_statement_parameters():
    assert engine_options["hide_parameters"] is True
    assert engine.hide_parameters is True


def test_application_session_error_omits_bound_parameter_values():
    # conftest points DATABASE_URL at in-memory SQLite unless a dedicated
    # PostgreSQL test server is configured; never touch anything else here.
    if engine.url.get_backend_name() != "sqlite":
        pytest.skip("Runs only against the in-memory SQLite application engine.")

    error = _violate_unique_constraint(SessionLocal, engine)

    message = str(error)

    assert "UNIQUE constraint failed" in message
    assert "hidden due to hide_parameters=True" in message
    assert SENSITIVE_VALUE not in message
    assert SENSITIVE_VALUE not in repr(error)


def test_engine_without_hide_parameters_would_leak_values():
    # Control case: proves the canary assertions above are meaningful.
    control_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    try:
        error = _violate_unique_constraint(
            sessionmaker(bind=control_engine),
            control_engine,
        )
    finally:
        control_engine.dispose()

    assert SENSITIVE_VALUE in str(error)


# LOGGING PRIVACY BOUNDARY:
# FastAPI logs unhandled exceptions with their message text. SQLAlchemy
# includes bound parameters in that text unless the engine hides them, so
# the application engine must keep hide_parameters enabled.
