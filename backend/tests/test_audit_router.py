from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.main import app
from app.models.domain_models import (
    AuditRecord,
    User,
)


@pytest.fixture
def audit_actor(
    db_session: Session,
) -> User:
    user = User(
        name="Audit Router Actor",
        school_id="8600000001",
        email="audit.router.actor@pampangastateu.edu.ph",
        role="instructor",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def other_audit_actor(
    db_session: Session,
) -> User:
    user = User(
        name="Other Audit Router Actor",
        school_id="8600000002",
        email="audit.router.other@pampangastateu.edu.ph",
        role="student",
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def audit_router_records(
    db_session: Session,
    audit_actor: User,
    other_audit_actor: User,
) -> dict[str, AuditRecord]:
    now = datetime.now(timezone.utc)

    oldest = AuditRecord(
        audit_key="audit:router:classroom-created:101",
        actor_user_id=audit_actor.user_id,
        action_type="classroom_created",
        resource_type="classroom",
        resource_id="101",
        outcome="succeeded",
        audit_data={
            "subject_code": "CS101",
        },
        occurred_at=now - timedelta(days=3),
        created_at=now - timedelta(days=3),
    )

    middle = AuditRecord(
        audit_key="audit:router:activity-published:202",
        actor_user_id=audit_actor.user_id,
        action_type="activity_published",
        resource_type="task",
        resource_id="202",
        outcome="succeeded",
        audit_data={
            "class_id": 101,
            "previous_state": "draft",
            "new_state": "published",
        },
        occurred_at=now - timedelta(days=2),
        created_at=now - timedelta(days=2),
    )

    newest = AuditRecord(
        audit_key="audit:router:enrollment-status:303",
        actor_user_id=audit_actor.user_id,
        action_type="enrollment_status_changed",
        resource_type="enrollment",
        resource_id="303",
        outcome="failed",
        audit_data={
            "previous_status": "active",
            "requested_status": "disabled",
            "reason_code": "persistence_failure",
        },
        occurred_at=now - timedelta(days=1),
        created_at=now - timedelta(days=1),
    )

    other_actor_record = AuditRecord(
        audit_key="audit:router:other-user:404",
        actor_user_id=other_audit_actor.user_id,
        action_type="submission_created",
        resource_type="submission",
        resource_id="404",
        outcome="succeeded",
        audit_data={
            "attempt_number": 1,
        },
        occurred_at=now,
        created_at=now,
    )

    db_session.add_all(
        [
            oldest,
            middle,
            newest,
            other_actor_record,
        ]
    )
    db_session.commit()

    db_session.refresh(oldest)
    db_session.refresh(middle)
    db_session.refresh(newest)
    db_session.refresh(other_actor_record)

    return {
        "oldest": oldest,
        "middle": middle,
        "newest": newest,
        "other_actor_record": other_actor_record,
    }


@pytest.fixture
def audit_client(
    client: TestClient,
    audit_actor: User,
):
    app.dependency_overrides[get_current_user] = lambda: audit_actor

    yield client

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@pytest.fixture
def forbidden_audit_client(
    client: TestClient,
):
    def reject_unauthenticated_user() -> User:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=("Could not validate authentication credentials."),
        )

    app.dependency_overrides[get_current_user] = reject_unauthenticated_user

    yield client

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


def test_user_lists_only_own_audit_records(
    audit_client: TestClient,
    audit_router_records: dict[str, AuditRecord],
):
    response = audit_client.get(
        "/audit-records/",
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 3
    assert data["total_pages"] == 1

    returned_ids = [item["audit_id"] for item in data["items"]]

    assert returned_ids == [
        audit_router_records["newest"].audit_id,
        audit_router_records["middle"].audit_id,
        audit_router_records["oldest"].audit_id,
    ]

    assert audit_router_records["other_actor_record"].audit_id not in returned_ids


def test_audit_list_response_is_privacy_safe(
    audit_client: TestClient,
    audit_router_records: dict[str, AuditRecord],
):
    response = audit_client.get(
        "/audit-records/",
    )

    assert response.status_code == status.HTTP_200_OK

    prohibited_fields = {
        "audit_key",
        "password",
        "password_hash",
        "otp",
        "otp_code",
        "source_code",
        "raw_code",
        "starter_code",
        "standard_input",
        "hidden_test_cases",
        "expected_output",
        "stdout",
        "stderr",
        "ast_details",
        "similarity_details",
        "clipboard_content",
        "pasted_text",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "score",
        "max_score",
        "feedback",
        "misconduct_verdict",
    }

    for item in response.json()["items"]:
        assert prohibited_fields.isdisjoint(item.keys())
        assert prohibited_fields.isdisjoint(item["audit_data"].keys())


def test_user_paginates_own_audit_records(
    audit_client: TestClient,
    audit_router_records: dict[str, AuditRecord],
):
    first_page = audit_client.get(
        "/audit-records/",
        params={
            "page": 1,
            "page_size": 2,
        },
    )
    second_page = audit_client.get(
        "/audit-records/",
        params={
            "page": 2,
            "page_size": 2,
        },
    )

    assert first_page.status_code == status.HTTP_200_OK
    assert second_page.status_code == status.HTTP_200_OK

    first_data = first_page.json()
    second_data = second_page.json()

    assert first_data["total"] == 3
    assert first_data["total_pages"] == 2
    assert [item["audit_id"] for item in first_data["items"]] == [
        audit_router_records["newest"].audit_id,
        audit_router_records["middle"].audit_id,
    ]

    assert second_data["total"] == 3
    assert second_data["total_pages"] == 2
    assert [item["audit_id"] for item in second_data["items"]] == [
        audit_router_records["oldest"].audit_id,
    ]


def test_user_filters_own_audit_records(
    audit_client: TestClient,
    audit_router_records: dict[str, AuditRecord],
):
    response = audit_client.get(
        "/audit-records/",
        params={
            "action_type": "activity_published",
            "resource_type": "task",
            "resource_id": "202",
            "outcome": "succeeded",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total"] == 1
    assert data["total_pages"] == 1
    assert [item["audit_id"] for item in data["items"]] == [
        audit_router_records["middle"].audit_id,
    ]


def test_user_gets_one_owned_audit_record(
    audit_client: TestClient,
    audit_router_records: dict[str, AuditRecord],
):
    record = audit_router_records["middle"]

    response = audit_client.get(
        f"/audit-records/{record.audit_id}",
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["audit_id"] == record.audit_id
    assert data["actor_user_id"] == record.actor_user_id
    assert data["action_type"] == "activity_published"
    assert data["resource_type"] == "task"
    assert data["resource_id"] == "202"
    assert data["outcome"] == "succeeded"
    assert data["audit_data"] == {
        "class_id": 101,
        "previous_state": "draft",
        "new_state": "published",
    }
    assert "audit_key" not in data


def test_user_cannot_get_another_actors_audit_record(
    audit_client: TestClient,
    audit_router_records: dict[str, AuditRecord],
):
    record = audit_router_records["other_actor_record"]

    response = audit_client.get(
        f"/audit-records/{record.audit_id}",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == ("Audit record was not found.")


def test_missing_audit_record_returns_not_found(
    audit_client: TestClient,
):
    response = audit_client.get(
        "/audit-records/00000000-0000-0000-0000-000000000001",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == ("Audit record was not found.")


@pytest.mark.parametrize(
    ("query_name", "query_value"),
    [
        ("page", 0),
        ("page_size", 0),
        ("page_size", 101),
        ("action_type", "password_viewed"),
        ("resource_type", "source_code"),
        ("outcome", "automatic_verdict"),
        ("resource_id", "   "),
    ],
)
def test_audit_list_rejects_invalid_query_values(
    audit_client: TestClient,
    query_name: str,
    query_value,
):
    response = audit_client.get(
        "/audit-records/",
        params={
            query_name: query_value,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_invalid_audit_uuid_returns_validation_error(
    audit_client: TestClient,
):
    response = audit_client.get(
        "/audit-records/not-a-valid-uuid",
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_audit_list_requires_authentication(
    forbidden_audit_client: TestClient,
):
    response = forbidden_audit_client.get(
        "/audit-records/",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_audit_detail_requires_authentication(
    forbidden_audit_client: TestClient,
):
    response = forbidden_audit_client.get(
        "/audit-records/00000000-0000-0000-0000-000000000001",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    "method",
    [
        "post",
        "put",
        "patch",
        "delete",
    ],
)
def test_audit_router_exposes_no_client_write_operations(
    audit_client: TestClient,
    method: str,
):
    response = audit_client.request(
        method.upper(),
        "/audit-records/",
        json={
            "audit_key": "client-controlled-key",
            "actor_user_id": 999,
            "action_type": "activity_published",
            "resource_type": "task",
            "resource_id": "1",
            "outcome": "succeeded",
            "audit_data": {},
        },
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
