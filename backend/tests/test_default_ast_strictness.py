"""
The admin's "Default AST strictness" (backend audit "Still open" item 8).

Owner decision: it is the starting level of new instructor accounts and the
level used for practice modules (which have no instructor). Instructors
keep the level they chose.
"""

from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.core.system_settings import get_default_ast_strictness, set_system_setting
from app.models.domain_models import PracticeModule, PracticeTask, User
from app.routers import practice as practice_router

DOMAIN = "@pampangastateu.edu.ph"
TWO_LOOPS = "for i in range(1):\n    pass\nfor j in range(1):\n    print('ok')\n"


def make_user(db: Session, *, email: str, role: str, school_id: str, strictness: str = "moderate") -> User:
    user = User(name="Test User", email=email, role=role, school_id=school_id,
                password_hash=get_password_hash("Original#2026"), email_verified=True, is_active=True,
                ast_strictness_level=strictness)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id), 'pwd_ver': user.password_version})}"}


@pytest.fixture
def admin(db_session):
    return make_user(db_session, email=f"mis{DOMAIN}", role="admin", school_id="9000000001")


@pytest.fixture
def student(db_session):
    return make_user(db_session, email=f"2023000001{DOMAIN}", role="student", school_id="2023000001")


@pytest.fixture
def practice_task(db_session):
    module = PracticeModule(title="Loops", order_index=0)
    db_session.add(module)
    db_session.commit()
    # Exactly one for loop under "strict"; at least one otherwise.
    task = PracticeTask(module_id=module.module_id, title="One loop", instructions="Use a for loop.",
                        expected_output="ok\n", expected_ast_patterns={"require_for_loop": 1}, order_index=0)
    db_session.add(task)
    db_session.commit()
    return task


@pytest.fixture
def judge0_accepts(monkeypatch):
    """Judge0 reports "Accepted" without any network call."""

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, *args, **kwargs):
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"status": {"id": 3}})

    monkeypatch.setattr(practice_router, "httpx",
                        SimpleNamespace(Client=FakeClient, Timeout=httpx.Timeout, HTTPError=httpx.HTTPError))


# ------------------------------------------------------------ setting


@pytest.mark.parametrize(("stored", "expected"), [
    (None, "moderate"), ("lax", "lax"), ("moderate", "moderate"), ("strict", "strict"), ("banana", "moderate"),
])
def test_default_strictness_reads_the_setting_and_rejects_unknown_values(db_session, stored, expected):
    if stored is not None:
        set_system_setting(db_session, "default_ast_strictness", stored)

    assert get_default_ast_strictness(db_session) == expected


# ------------------------------------------------------------ new instructors


def test_new_instructor_starts_at_the_admin_default(client, db_session, admin):
    existing = make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="9000000002",
                         strictness="lax")
    settings = {"maintenance_mode": False, "default_ast_strictness": "strict", "registration_enabled": False}
    assert client.patch("/admin/settings", json=settings, headers=auth(admin)).status_code == 200

    response = client.post("/admin/instructors", headers=auth(admin), json={
        "email": f"new.faculty{DOMAIN}", "first_name": "New", "last_name": "Faculty", "password": "Faculty#2026",
    })

    assert response.status_code == 200, response.text
    db_session.expire_all()
    created = db_session.query(User).filter(User.email == f"new.faculty{DOMAIN}").one()
    assert created.ast_strictness_level == "strict"
    # Existing instructors keep the level they chose.
    assert db_session.get(User, existing.user_id).ast_strictness_level == "lax"


# ------------------------------------------------------------ practice


@pytest.mark.parametrize(("default", "passes"), [("moderate", True), ("lax", True), ("strict", False)])
def test_practice_structure_check_uses_the_admin_default(client, db_session, student, practice_task,
                                                         judge0_accepts, default, passes):
    set_system_setting(db_session, "default_ast_strictness", default)

    response = client.post(f"/practice/tasks/{practice_task.task_id}/submit", json={"code": TWO_LOOPS},
                           headers=auth(student))

    assert response.status_code == 200, response.text
    assert response.json()["is_successful"] is passes
