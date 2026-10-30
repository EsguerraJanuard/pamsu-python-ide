"""
While Redis is unreachable, rate limits and logout revocation fall back to
this process's memory instead of failing open.

conftest.py points REDIS_URL at a closed port, so every request in these
tests runs as if Upstash were down.
"""

import logging

import pytest

from app.core import rate_limit, token_revocation
from app.core.memory_fallback import ExpiringMemoryStore
from app.core.security import get_password_hash
from app.models.domain_models import User

DOMAIN = "@pampangastateu.edu.ph"
PASSWORD = "Correct#2026"


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class FakeRedis:
    def __init__(self):
        self.values: dict[str, str] = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)


@pytest.fixture
def account(db_session):
    user = User(
        name="Stu Dent",
        email=f"stu.dent{DOMAIN}",
        role="student",
        school_id="2026000001",
        password_hash=get_password_hash(PASSWORD),
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def login(client, email: str, password: str):
    return client.post("/login", data={"username": email, "password": password})


# ------------------------------------------------------------ memory store


def test_store_counts_within_a_window_and_resets_after_it():
    clock = FakeClock()
    store = ExpiringMemoryStore(clock=clock)

    assert [store.incr("k", 60)[0] for _ in range(3)] == [1, 2, 3]
    clock.now += 30
    assert store.incr("k", 60) == (4, 30)
    clock.now += 31
    assert store.incr("k", 60) == (1, 60)


def test_store_set_entries_expire():
    clock = FakeClock()
    store = ExpiringMemoryStore(clock=clock)

    store.set("revoked", 10)
    assert store.contains("revoked")
    clock.now += 10
    assert not store.contains("revoked")
    assert len(store) == 0


def test_store_size_is_capped_expired_first_then_oldest():
    clock = FakeClock()
    store = ExpiringMemoryStore(max_entries=3, clock=clock)

    store.set("short", 5)
    store.set("a", 100)
    store.set("b", 100)
    clock.now += 6
    store.set("c", 100)  # full: the expired key goes first
    assert (store.contains("a"), store.contains("b"), store.contains("c")) == (True, True, True)

    store.set("d", 100)  # full, nothing expired: the oldest goes
    assert len(store) == 3
    assert not store.contains("a")
    assert store.contains("d")


# ------------------------------------------------------------ rate limits


def test_login_limit_still_applies_while_redis_is_down(client, account, caplog):
    with caplog.at_level(logging.WARNING):
        statuses = [login(client, account.email, "wrong").status_code for _ in range(11)]

    assert statuses == [401] * 10 + [429]
    assert "counting in memory" in caplog.text
    # Keys in memory are hashed like the Redis keys: no raw email is kept.
    assert len(rate_limit.memory_counters) == 1


def test_limits_are_per_identifier_while_redis_is_down(client, account):
    for _ in range(11):
        login(client, account.email, "wrong")

    assert login(client, f"someone.else{DOMAIN}", "wrong").status_code == 401


# ------------------------------------------------------------ logout


def test_logout_revokes_the_token_while_redis_is_down(client, account):
    token = login(client, account.email, PASSWORD).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/notifications/unread-count", headers=headers).status_code == 200

    assert client.post("/logout", headers=headers).status_code == 204

    assert client.get("/notifications/unread-count", headers=headers).status_code == 401


def test_revocation_kept_in_memory_survives_redis_coming_back_empty(monkeypatch):
    token_revocation.revoke_token("jti-1", 60)  # Redis down: memory only

    monkeypatch.setattr(token_revocation, "redis_client", FakeRedis())

    assert token_revocation.is_token_revoked("jti-1")


def test_revocation_is_written_to_redis_and_read_from_it(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(token_revocation, "redis_client", fake)

    token_revocation.revoke_token("jti-2", 60)
    assert fake.values == {"blacklist:jti-2": "revoked"}

    # Another process (or a restart) has no memory entry: Redis decides.
    token_revocation.revoked_in_memory.clear()
    assert token_revocation.is_token_revoked("jti-2")
    assert not token_revocation.is_token_revoked("jti-unknown")
