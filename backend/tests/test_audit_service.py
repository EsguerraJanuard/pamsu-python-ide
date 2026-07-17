from datetime import datetime

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.domain_models import (
    AuditRecord,
    User,
)
from app.schemas.audit_schema import AuditRecordCreateInternal
from app.services.audit_service import (
    AuditMetadataTooLargeError,
    AuditRecordConflictError,
    AuditRecordNotFoundError,
    create_audit_record,
    get_actor_owned_audit_record,
    list_actor_owned_audit_records,
)


def create_user(
    db_session: Session,
    *,
    school_id: str,
    email: str,
    role: str = "instructor",
) -> User:
    user = User(
        name="Audit Service User",
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


def audit_payload(
    *,
    audit_key: str,
    actor_user_id: int | None,
    action_type: str = "activity_published",
    resource_type: str = "task",
    resource_id: str = "100",
    outcome: str = "succeeded",
    audit_data: dict | None = None,
    occurred_at: datetime | None = None,
) -> AuditRecordCreateInternal:
    return AuditRecordCreateInternal(
        audit_key=audit_key,
        actor_user_id=actor_user_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        audit_data=audit_data or {},
        occurred_at=occurred_at,
    )


def test_create_audit_record_commits_by_default(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000001",
        email="audit.service1@pampangastateu.edu.ph",
    )

    actor_user_id = actor.user_id

    record = create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:activity-published:task:100",
            actor_user_id=actor_user_id,
            audit_data={
                "class_id": 10,
                "new_state": "published",
            },
        ),
    )

    audit_id = record.audit_id

    db_session.expunge_all()

    persisted = (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.audit_id == audit_id,
        )
        .one()
    )

    assert persisted.audit_key == "audit:activity-published:task:100"
    assert persisted.actor_user_id == actor_user_id
    assert persisted.action_type == "activity_published"
    assert persisted.resource_type == "task"
    assert persisted.resource_id == "100"
    assert persisted.outcome == "succeeded"
    assert persisted.audit_data == {
        "class_id": 10,
        "new_state": "published",
    }


def test_create_audit_record_accepts_dictionary_payload(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000002",
        email="audit.service2@pampangastateu.edu.ph",
    )

    record = create_audit_record(
        db_session,
        {
            "audit_key": "audit:classroom-created:classroom:200",
            "actor_user_id": actor.user_id,
            "action_type": "classroom_created",
            "resource_type": "classroom",
            "resource_id": "200",
            "outcome": "succeeded",
            "audit_data": {
                "subject_code": "CS101",
            },
        },
    )

    assert record.audit_id is not None
    assert record.action_type == "classroom_created"
    assert record.audit_data == {
        "subject_code": "CS101",
    }


def test_create_audit_record_is_idempotent_for_same_payload(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000003",
        email="audit.service3@pampangastateu.edu.ph",
    )

    payload = audit_payload(
        audit_key="audit:submission-created:submission:300",
        actor_user_id=actor.user_id,
        action_type="submission_created",
        resource_type="submission",
        resource_id="300",
        audit_data={
            "attempt_number": 1,
        },
    )

    first = create_audit_record(
        db_session,
        payload,
    )
    second = create_audit_record(
        db_session,
        payload,
    )

    assert second.audit_id == first.audit_id

    count = (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.audit_key == "audit:submission-created:submission:300",
        )
        .count()
    )

    assert count == 1


def test_create_audit_record_rejects_conflicting_reused_key(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000004",
        email="audit.service4@pampangastateu.edu.ph",
    )

    create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:grade-updated:grade:400",
            actor_user_id=actor.user_id,
            action_type="grade_updated",
            resource_type="grade",
            resource_id="400",
            audit_data={
                "changed_fields": ["feedback"],
            },
        ),
    )

    with pytest.raises(
        AuditRecordConflictError,
        match="different accountable action",
    ):
        create_audit_record(
            db_session,
            audit_payload(
                audit_key="audit:grade-updated:grade:400",
                actor_user_id=actor.user_id,
                action_type="grade_updated",
                resource_type="grade",
                resource_id="400",
                audit_data={
                    "changed_fields": ["release_state"],
                },
            ),
        )


def test_create_audit_record_rejects_prohibited_metadata(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000005",
        email="audit.service5@pampangastateu.edu.ph",
    )

    with pytest.raises(
        ValidationError,
        match="prohibited field",
    ):
        create_audit_record(
            db_session,
            {
                "audit_key": "audit:invalid-private-data:500",
                "actor_user_id": actor.user_id,
                "action_type": "submission_created",
                "resource_type": "submission",
                "resource_id": "500",
                "audit_data": {
                    "private": {
                        "source_code": "print('private')",
                    },
                },
            },
        )

    assert (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.audit_key == "audit:invalid-private-data:500",
        )
        .count()
        == 0
    )


def test_create_audit_record_rejects_oversized_metadata(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000006",
        email="audit.service6@pampangastateu.edu.ph",
    )

    with pytest.raises(
        AuditMetadataTooLargeError,
        match="maximum allowed size",
    ):
        create_audit_record(
            db_session,
            audit_payload(
                audit_key="audit:oversized-data:600",
                actor_user_id=actor.user_id,
                audit_data={
                    "approved_note": "x" * 17_000,
                },
            ),
        )

    assert (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.audit_key == "audit:oversized-data:600",
        )
        .count()
        == 0
    )


def test_create_audit_record_commit_false_flushes_without_commit(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000007",
        email="audit.service7@pampangastateu.edu.ph",
    )

    record = create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:atomic-action:700",
            actor_user_id=actor.user_id,
            action_type="classroom_updated",
            resource_type="classroom",
            resource_id="700",
        ),
        commit=False,
    )

    assert record.audit_id is not None

    visible_before_rollback = (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.audit_id == record.audit_id,
        )
        .one_or_none()
    )

    assert visible_before_rollback is not None

    db_session.rollback()

    visible_after_rollback = (
        db_session.query(AuditRecord)
        .filter(
            AuditRecord.audit_id == record.audit_id,
        )
        .one_or_none()
    )

    assert visible_after_rollback is None


def test_get_actor_owned_audit_record_returns_owner_record(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000008",
        email="audit.service8@pampangastateu.edu.ph",
    )

    created = create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:owner-record:800",
            actor_user_id=actor.user_id,
            action_type="activity_updated",
            resource_type="task",
            resource_id="800",
        ),
    )

    returned = get_actor_owned_audit_record(
        db_session,
        audit_id=created.audit_id,
        actor_user_id=actor.user_id,
    )

    assert returned.audit_id == created.audit_id
    assert returned.actor_user_id == actor.user_id


def test_get_actor_owned_audit_record_hides_other_actor_record(
    db_session: Session,
):
    owner = create_user(
        db_session,
        school_id="8500000009",
        email="audit.service9@pampangastateu.edu.ph",
    )
    other_actor = create_user(
        db_session,
        school_id="8500000010",
        email="audit.service10@pampangastateu.edu.ph",
    )

    created = create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:private-owner-record:900",
            actor_user_id=owner.user_id,
            action_type="activity_updated",
            resource_type="task",
            resource_id="900",
        ),
    )

    with pytest.raises(
        AuditRecordNotFoundError,
        match="not found",
    ):
        get_actor_owned_audit_record(
            db_session,
            audit_id=created.audit_id,
            actor_user_id=other_actor.user_id,
        )


def test_list_actor_owned_audit_records_isolated_and_paginated(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000011",
        email="audit.service11@pampangastateu.edu.ph",
    )
    other_actor = create_user(
        db_session,
        school_id="8500000012",
        email="audit.service12@pampangastateu.edu.ph",
    )

    first = create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:list:first:1001",
            actor_user_id=actor.user_id,
            action_type="classroom_created",
            resource_type="classroom",
            resource_id="1001",
            occurred_at=datetime(2026, 1, 1, 8, 0, 0),
        ),
    )
    second = create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:list:second:1002",
            actor_user_id=actor.user_id,
            action_type="activity_created",
            resource_type="task",
            resource_id="1002",
            occurred_at=datetime(2026, 1, 2, 8, 0, 0),
        ),
    )
    third = create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:list:third:1003",
            actor_user_id=actor.user_id,
            action_type="submission_created",
            resource_type="submission",
            resource_id="1003",
            occurred_at=datetime(2026, 1, 3, 8, 0, 0),
        ),
    )

    create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:list:other-actor:1004",
            actor_user_id=other_actor.user_id,
            action_type="classroom_created",
            resource_type="classroom",
            resource_id="1004",
            occurred_at=datetime(2026, 1, 4, 8, 0, 0),
        ),
    )

    first_page = list_actor_owned_audit_records(
        db_session,
        actor_user_id=actor.user_id,
        page=1,
        page_size=2,
    )
    second_page = list_actor_owned_audit_records(
        db_session,
        actor_user_id=actor.user_id,
        page=2,
        page_size=2,
    )

    assert first_page.total == 3
    assert first_page.total_pages == 2
    assert [item.audit_id for item in first_page.items] == [
        third.audit_id,
        second.audit_id,
    ]

    assert second_page.total == 3
    assert second_page.total_pages == 2
    assert [item.audit_id for item in second_page.items] == [
        first.audit_id,
    ]


def test_list_actor_owned_audit_records_applies_filters(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000013",
        email="audit.service13@pampangastateu.edu.ph",
    )

    matching = create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:filter:matching:1100",
            actor_user_id=actor.user_id,
            action_type="enrollment_status_changed",
            resource_type="enrollment",
            resource_id="1100",
            outcome="succeeded",
        ),
    )

    create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:filter:wrong-outcome:1100",
            actor_user_id=actor.user_id,
            action_type="enrollment_status_changed",
            resource_type="enrollment",
            resource_id="1100",
            outcome="failed",
        ),
    )

    create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:filter:wrong-resource:1101",
            actor_user_id=actor.user_id,
            action_type="enrollment_status_changed",
            resource_type="enrollment",
            resource_id="1101",
            outcome="succeeded",
        ),
    )

    response = list_actor_owned_audit_records(
        db_session,
        actor_user_id=actor.user_id,
        page=1,
        page_size=20,
        action_type="enrollment_status_changed",
        resource_type="enrollment",
        resource_id=" 1100 ",
        outcome="succeeded",
    )

    assert response.total == 1
    assert response.total_pages == 1
    assert [item.audit_id for item in response.items] == [
        matching.audit_id,
    ]


def test_actor_owned_list_excludes_null_actor_records(
    db_session: Session,
):
    actor = create_user(
        db_session,
        school_id="8500000014",
        email="audit.service14@pampangastateu.edu.ph",
    )

    create_audit_record(
        db_session,
        audit_payload(
            audit_key="audit:null-actor:1200",
            actor_user_id=None,
            action_type="login_failed",
            resource_type="user",
            resource_id="unknown",
            outcome="denied",
        ),
    )

    response = list_actor_owned_audit_records(
        db_session,
        actor_user_id=actor.user_id,
    )

    assert response.total == 0
    assert response.total_pages == 0
    assert response.items == []


@pytest.mark.parametrize(
    ("actor_user_id", "page", "page_size", "resource_id"),
    [
        (0, 1, 20, None),
        (-1, 1, 20, None),
        (1, 0, 20, None),
        (1, 1, 0, None),
        (1, 1, 101, None),
        (1, 1, 20, "   "),
    ],
)
def test_list_actor_owned_audit_records_rejects_invalid_arguments(
    db_session: Session,
    actor_user_id: int,
    page: int,
    page_size: int,
    resource_id: str | None,
):
    with pytest.raises(ValueError):
        list_actor_owned_audit_records(
            db_session,
            actor_user_id=actor_user_id,
            page=page,
            page_size=page_size,
            resource_id=resource_id,
        )
