"""
In-process TTL cache (zero-budget stand-in for a Redis query cache) and its
use for system settings, which every student request reads.
"""

import pytest

from app.core import system_settings, ttl_cache
from app.core.system_settings import (get_all_system_settings,
                                      get_system_setting,
                                      invalidate_system_settings_cache,
                                      set_system_setting)
from app.core.ttl_cache import TTLCache
from app.models.domain_models import SystemSetting


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(ttl_cache.time, "monotonic", fake)
    return fake


def test_entries_expire_after_the_ttl(clock):
    cache = TTLCache(ttl_seconds=10)
    cache.set("k", "v")

    clock.now += 9.9
    assert cache.get("k") == "v"

    clock.now += 0.2
    assert cache.get("k", "gone") == "gone"
    assert len(cache) == 0


def test_get_or_load_loads_once_until_expiry(clock):
    cache = TTLCache(ttl_seconds=5)
    calls = []

    def loader():
        calls.append(1)
        return len(calls)

    assert cache.get_or_load("k", loader) == 1
    assert cache.get_or_load("k", loader) == 1
    clock.now += 6
    assert cache.get_or_load("k", loader) == 2


def test_a_failed_load_is_not_cached():
    cache = TTLCache(ttl_seconds=60)

    def broken():
        raise RuntimeError("database down")

    with pytest.raises(RuntimeError):
        cache.get_or_load("k", broken)

    assert cache.get_or_load("k", lambda: "ok") == "ok"


def test_oldest_entries_are_dropped_past_max_entries():
    cache = TTLCache(ttl_seconds=60, max_entries=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")  # "a" is now the most recently used
    cache.set("c", 3)

    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_invalidate_and_clear():
    cache = TTLCache(ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)

    cache.invalidate("a")
    assert cache.get("a") is None and cache.get("b") == 2

    ttl_cache.clear_all_caches()
    assert len(cache) == 0


def test_settings_are_read_from_memory_between_saves(db_session, monkeypatch):
    set_system_setting(db_session, "maintenance_mode", True)

    queries = []
    real_load = system_settings._load_stored_settings

    def counting_load(db):
        queries.append(1)
        return real_load(db)

    monkeypatch.setattr(system_settings, "_load_stored_settings", counting_load)

    for _ in range(5):
        assert get_system_setting(db_session, "maintenance_mode") is True
    assert get_all_system_settings(db_session)["maintenance_mode"] is True
    assert len(queries) == 1

    # Saving clears the copy: the new value is read at once.
    set_system_setting(db_session, "maintenance_mode", False)
    assert get_system_setting(db_session, "maintenance_mode") is False
    assert len(queries) == 2


def test_settings_changed_elsewhere_show_up_after_the_ttl(db_session, clock):
    assert get_system_setting(db_session, "maintenance_mode") is False

    # Another process (or a manual SQL fix) changes the row directly.
    db_session.add(SystemSetting(key="maintenance_mode", value="true"))
    db_session.commit()

    assert get_system_setting(db_session, "maintenance_mode") is False
    clock.now += system_settings.SETTINGS_CACHE_TTL_SECONDS + 1
    assert get_system_setting(db_session, "maintenance_mode") is True


def test_a_database_error_falls_back_to_defaults_without_caching_them(db_session, monkeypatch):
    set_system_setting(db_session, "default_ast_strictness", "strict")
    invalidate_system_settings_cache()

    def broken(_db):
        raise RuntimeError("database down")

    monkeypatch.setattr(system_settings, "_load_stored_settings", broken)
    assert get_system_setting(db_session, "default_ast_strictness") == "moderate"

    monkeypatch.undo()
    assert get_system_setting(db_session, "default_ast_strictness") == "strict"


def test_saving_settings_through_the_api_takes_effect_at_once(client, db_session):
    from app.core.security import create_access_token, get_password_hash
    from app.models.domain_models import User

    admin = User(
        name="Settings Admin",
        email="settings.admin@pampangastateu.edu.ph",
        role="admin",
        school_id="ADM0000099",
        password_hash=get_password_hash("Admin#2026"),
        email_verified=True,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin.user_id)})}"}

    assert get_system_setting(db_session, "maintenance_mode") is False  # now cached

    response = client.patch(
        "/admin/settings",
        headers=headers,
        json={"maintenance_mode": True, "default_ast_strictness": "moderate", "registration_enabled": False},
    )

    assert response.status_code == 200, response.text
    assert get_system_setting(db_session, "maintenance_mode") is True
