import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.domain_models import (
    AuditRecord,
    User,
)


def create_audit_user(
    db_session: Session,
    *,
    school_id: str,
    email: str,
    role: str = "instructor",
) -> User:
    user = User(
        name="Audit Model User",
        school_id=school_id,
        email=email,
        role=role,
        password_hash="fakehash",
        email_verified=True,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def create_audit_record(
    db_session: Session,
    *,
    audit_key: str,
    actor_user_id: int | None,
    action_type: str = "activity_published",
    resource_type: str = "task",
    resource_id: str = "101",
    outcome: str = "succeeded",
    audit_data: dict | None = None,
) -> AuditRecord:
    record = AuditRecord(
        audit_key=audit_key,
        actor_user_id=actor_user_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        audit_data=audit_data or {},
    )

    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    return record


def test_audit_record_table_is_registered():
    assert "audit_records" in Base.metadata.tables


def test_audit_record_can_be_created_with_authenticated_actor(
    db_session: Session,
):
    actor = create_audit_user(
        db_session,
        school_id="8400000001",
        email="audit.actor1@pampangastateu.edu.ph",
    )

    record = create_audit_record(
        db_session,
        audit_key="audit:activity-published:task:101",
        actor_user_id=actor.user_id,
        audit_data={
            "class_id": 10,
            "previous_state": "draft",
            "new_state": "published",
        },
    )

    assert record.audit_id is not None
    assert len(record.audit_id) == 36
    assert record.actor_user_id == actor.user_id
    assert record.action_type == "activity_published"
    assert record.resource_type == "task"
    assert record.resource_id == "101"
    assert record.outcome == "succeeded"
    assert record.occurred_at is not None
    assert record.created_at is not None


def test_audit_record_allows_null_actor_for_pre_authentication_event(
    db_session: Session,
):
    record = create_audit_record(
        db_session,
        audit_key="audit:login-failed:request:001",
        actor_user_id=None,
        action_type="login_failed",
        resource_type="user",
        resource_id="unknown",
        outcome="denied",
        audit_data={
            "reason": "invalid_credentials",
        },
    )

    assert record.actor_user_id is None
    assert record.action_type == "login_failed"
    assert record.outcome == "denied"


def test_duplicate_audit_key_is_rejected(
    db_session: Session,
):
    actor = create_audit_user(
        db_session,
        school_id="8400000002",
        email="audit.actor2@pampangastateu.edu.ph",
    )

    create_audit_record(
        db_session,
        audit_key="audit:submission-created:submission:202",
        actor_user_id=actor.user_id,
        action_type="submission_created",
        resource_type="submission",
        resource_id="202",
    )

    duplicate = AuditRecord(
        audit_key="audit:submission-created:submission:202",
        actor_user_id=actor.user_id,
        action_type="submission_created",
        resource_type="submission",
        resource_id="202",
        outcome="succeeded",
        audit_data={},
    )

    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

    count = (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.audit_key == "audit:submission-created:submission:202",
        )
        .count()
    )

    assert count == 1


@pytest.mark.parametrize(
    "invalid_action_type",
    [
        "password_viewed",
        "automatic_misconduct_decision",
    ],
)
def test_invalid_audit_action_type_is_rejected(
    db_session: Session,
    invalid_action_type: str,
):
    record = AuditRecord(
        audit_key=f"audit:invalid-action:{invalid_action_type}",
        actor_user_id=None,
        action_type=invalid_action_type,
        resource_type="user",
        resource_id="1",
        outcome="failed",
        audit_data={},
    )

    db_session.add(record)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "invalid_resource_type",
    [
        "password",
        "source_code",
    ],
)
def test_invalid_audit_resource_type_is_rejected(
    db_session: Session,
    invalid_resource_type: str,
):
    record = AuditRecord(
        audit_key=f"audit:invalid-resource:{invalid_resource_type}",
        actor_user_id=None,
        action_type="login_failed",
        resource_type=invalid_resource_type,
        resource_id="1",
        outcome="failed",
        audit_data={},
    )

    db_session.add(record)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    "invalid_outcome",
    [
        "unknown",
        "automatic_verdict",
    ],
)
def test_invalid_audit_outcome_is_rejected(
    db_session: Session,
    invalid_outcome: str,
):
    record = AuditRecord(
        audit_key=f"audit:invalid-outcome:{invalid_outcome}",
        actor_user_id=None,
        action_type="login_failed",
        resource_type="user",
        resource_id="1",
        outcome=invalid_outcome,
        audit_data={},
    )

    db_session.add(record)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_user_relationship_lists_created_audit_records(
    db_session: Session,
):
    actor = create_audit_user(
        db_session,
        school_id="8400000003",
        email="audit.actor3@pampangastateu.edu.ph",
    )

    first_record = create_audit_record(
        db_session,
        audit_key="audit:classroom-created:classroom:301",
        actor_user_id=actor.user_id,
        action_type="classroom_created",
        resource_type="classroom",
        resource_id="301",
    )

    second_record = create_audit_record(
        db_session,
        audit_key="audit:activity-created:task:302",
        actor_user_id=actor.user_id,
        action_type="activity_created",
        resource_type="task",
        resource_id="302",
    )

    db_session.refresh(actor)

    returned_ids = {record.audit_id for record in actor.audit_records_created}

    assert returned_ids == {
        first_record.audit_id,
        second_record.audit_id,
    }

    assert first_record.actor.user_id == actor.user_id
    assert second_record.actor.user_id == actor.user_id


def test_privacy_safe_audit_data_round_trips(
    db_session: Session,
):
    actor = create_audit_user(
        db_session,
        school_id="8400000004",
        email="audit.actor4@pampangastateu.edu.ph",
    )

    approved_data = {
        "class_id": 401,
        "previous_status": "active",
        "new_status": "disabled",
        "reason_code": "instructor_action",
    }

    record = create_audit_record(
        db_session,
        audit_key="audit:enrollment-status:enrollment:401",
        actor_user_id=actor.user_id,
        action_type="enrollment_status_changed",
        resource_type="enrollment",
        resource_id="401",
        audit_data=approved_data,
    )

    assert record.audit_data == approved_data

    prohibited_keys = {
        "password",
        "password_hash",
        "otp",
        "otp_code",
        "raw_code",
        "source_code",
        "starter_code",
        "standard_input",
        "expected_output",
        "hidden_test_cases",
        "stdout",
        "stderr",
        "ast_details",
        "similarity_results",
        "clipboard_content",
        "pasted_text",
        "keystrokes",
        "browsing_history",
        "screen_recording",
        "webcam",
        "microphone",
        "misconduct_verdict",
    }

    assert prohibited_keys.isdisjoint(record.audit_data)


def test_same_resource_accepts_distinct_accountable_actions(
    db_session: Session,
):
    actor = create_audit_user(
        db_session,
        school_id="8400000005",
        email="audit.actor5@pampangastateu.edu.ph",
    )

    created = create_audit_record(
        db_session,
        audit_key="audit:grade-created:grade:501",
        actor_user_id=actor.user_id,
        action_type="grade_created",
        resource_type="grade",
        resource_id="501",
    )

    released = create_audit_record(
        db_session,
        audit_key="audit:grade-released:grade:501",
        actor_user_id=actor.user_id,
        action_type="grade_released",
        resource_type="grade",
        resource_id="501",
    )

    records = (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.resource_type == "grade",
            AuditRecord.resource_id == "501",
        )
        .order_by(
            AuditRecord.created_at.asc(),
            AuditRecord.audit_id.asc(),
        )
        .all()
    )

    assert {record.audit_id for record in records} == {
        created.audit_id,
        released.audit_id,
    }
