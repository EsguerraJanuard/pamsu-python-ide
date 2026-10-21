"""
MIS masterlist import (POST /admin/students/bulk-register/file).

Every account must carry the student's own email, school ID and name from
the file. Nothing is inferred, no password is shared or emailed, and a
database conflict creates nothing.
"""

import io

import pytest
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.domain_models import Classroom, Enrollment, PendingEnrollment, User
from app.services import student_provisioning_service
from app.services.student_provisioning_service import (MAX_MASTERLIST_ROWS,
                                                      UNUSABLE_PASSWORD_PREFIX)

DOMAIN = "@pampangastateu.edu.ph"
URL = "/admin/students/bulk-register/file"


def make_user(db: Session, *, email: str, role: str, school_id: str, name: str = "Existing User") -> User:
    user = User(
        name=name,
        email=email,
        role=role,
        school_id=school_id,
        password_hash=get_password_hash("Existing#2026"),
        email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"}


def upload(client, user: User, content: bytes, filename: str = "masterlist.csv"):
    return client.post(URL, headers=auth(user), files={"file": (filename, content, "text/csv")})


def csv_bytes(*rows: str, header: str = "email,school_id,name") -> bytes:
    return ("\n".join([header, *rows]) + "\n").encode()


def students(db: Session) -> list[User]:
    db.expire_all()
    return db.query(User).filter(User.role == "student").order_by(User.school_id).all()


@pytest.fixture
def admin(db_session):
    return make_user(db_session, email=f"mis{DOMAIN}", role="admin", school_id="9000000001", name="MIS Admin")


class SentEmails(list):
    """(email, temp_password, role) per queued email; .details has the rest."""

    def __init__(self):
        super().__init__()
        self.details = []


@pytest.fixture
def sent_emails(monkeypatch):
    sent = SentEmails()

    def fake_send(recipient_email, first_name, temp_password, role, **details):
        sent.append((recipient_email, temp_password, role))
        sent.details.append({"email": recipient_email, "first_name": first_name, **details})

    monkeypatch.setattr("app.routers.admin.send_provisioning_email", fake_send)
    return sent


def test_creates_accounts_with_identity_exactly_as_given(client, db_session, admin, sent_emails):
    response = upload(
        client,
        admin,
        csv_bytes(
            f"2023304120{DOMAIN},2023304120,Juan Dela Cruz",
            f"maria.santos{DOMAIN},2023-00042,Maria   Santos",
        ),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["created"], body["skipped"], body["failed"]) == (2, 0, 0)
    assert [row["status"] for row in body["rows"]] == ["created", "created"]

    created = {user.email: user for user in students(db_session)}
    assert created[f"2023304120{DOMAIN}"].school_id == "2023304120"
    assert created[f"2023304120{DOMAIN}"].name == "Juan Dela Cruz"
    assert created[f"maria.santos{DOMAIN}"].school_id == "2023-00042"
    assert created[f"maria.santos{DOMAIN}"].name == "Maria Santos"
    assert all(user.email_verified and user.is_active for user in created.values())


def test_student_number_and_email_are_separate_and_never_inferred(client, db_session, admin, sent_emails):
    response = upload(
        client,
        admin,
        csv_bytes(
            f"2023304120{DOMAIN},,Missing Number",
            ",2023304121,Missing Email",
        ),
    )

    assert response.status_code == 200
    rows = response.json()["rows"]
    assert rows[0] == {"row": 2, "email": f"2023304120{DOMAIN}", "status": "failed", "reason": "Missing school ID."}
    assert rows[1]["status"] == "failed"
    assert rows[1]["reason"] == "Missing email."
    assert students(db_session) == []


def test_first_and_last_name_columns_are_combined(client, db_session, admin, sent_emails):
    response = upload(
        client,
        admin,
        csv_bytes(
            f"ana{DOMAIN},2023000001,Ana,Reyes,Lopez",
            header="Email,School ID,First Name,Middle Name,Last Name",
        ),
    )

    assert response.status_code == 200, response.text
    assert students(db_session)[0].name == "Ana Reyes Lopez"
    # The welcome email greets "Lopez, Ana" from the file's own columns.
    assert sent_emails.details == [
        {"email": f"ana{DOMAIN}", "first_name": "Ana", "last_name": "Lopez", "school_id": "2023000001"}
    ]


@pytest.mark.parametrize(
    ("row", "reason_fragment"),
    [
        ("someone@gmail.com,2023000001,Outside Domain", "pampangastateu.edu.ph"),
        (f"short{DOMAIN},12345,Short Id", "10 digits"),
        (f"noname{DOMAIN},2023000001,", "Missing name."),
        (f"long{DOMAIN},2023000001," + "x" * 151, "150 characters"),
    ],
)
def test_invalid_rows_fail_with_row_reason(client, db_session, admin, sent_emails, row, reason_fragment):
    response = upload(client, admin, csv_bytes(row))

    assert response.status_code == 200
    result = response.json()["rows"][0]
    assert result["status"] == "failed"
    assert reason_fragment in result["reason"]
    assert students(db_session) == []


def test_duplicates_inside_the_file_all_fail(client, db_session, admin, sent_emails):
    response = upload(
        client,
        admin,
        csv_bytes(
            f"a{DOMAIN},2023000001,Student A",
            f"b{DOMAIN},2023000001,Student B",
            f"c{DOMAIN},2023000003,Student C",
            f"C{DOMAIN},2023000004,Student C Again",
        ),
    )

    body = response.json()
    assert (body["created"], body["failed"]) == (0, 4)
    assert students(db_session) == []


def test_existing_accounts_are_skipped_or_rejected_never_changed(client, db_session, admin, sent_emails):
    existing = make_user(db_session, email=f"existing{DOMAIN}", role="student", school_id="2023000010")
    original_hash = existing.password_hash

    same_account = upload(client, admin, csv_bytes(f"EXISTING{DOMAIN},2023000010,Renamed Student"))
    other_email = upload(client, admin, csv_bytes(f"other{DOMAIN},2023000010,Steals Number"))
    other_number = upload(client, admin, csv_bytes(f"existing{DOMAIN},2023000011,Changes Number"))

    assert same_account.json()["rows"][0]["status"] == "skipped"
    assert other_email.json()["rows"][0]["status"] == "failed"
    assert "school ID already belongs" in other_email.json()["rows"][0]["reason"]
    assert other_number.json()["rows"][0]["status"] == "failed"
    assert "email already belongs" in other_number.json()["rows"][0]["reason"]

    db_session.refresh(existing)
    assert existing.name == "Existing User"
    assert existing.password_hash == original_hash
    assert len(students(db_session)) == 1


def test_email_of_non_student_account_fails(client, db_session, admin, sent_emails):
    make_user(db_session, email=f"teacher{DOMAIN}", role="instructor", school_id="2023000020")

    response = upload(client, admin, csv_bytes(f"teacher{DOMAIN},2023000020,Teacher"))

    assert response.json()["rows"][0]["status"] == "failed"
    assert "non-student" in response.json()["rows"][0]["reason"]


def test_no_shared_or_emailed_password(client, db_session, admin, sent_emails):
    response = upload(
        client,
        admin,
        csv_bytes(f"one{DOMAIN},2023000001,Student One", f"two{DOMAIN},2023000002,Student Two"),
    )

    assert response.status_code == 200
    accounts = students(db_session)
    hashes = [user.password_hash for user in accounts]
    assert len(set(hashes)) == 2
    assert all(value.startswith(UNUSABLE_PASSWORD_PREFIX) for value in hashes)
    for user in accounts:
        assert not verify_password("PamsU@2026", user.password_hash)
        assert not verify_password(user.password_hash, user.password_hash)

    assert sorted(email for email, _, _ in sent_emails) == [f"one{DOMAIN}", f"two{DOMAIN}"]
    assert all(temp_password is None for _, temp_password, _ in sent_emails)
    # A single name column is used whole; a surname is never guessed from it.
    assert sorted((d["first_name"], d["last_name"], d["school_id"]) for d in sent_emails.details) == [
        ("Student One", "", "2023000001"),
        ("Student Two", "", "2023000002"),
    ]


def test_provisioned_student_cannot_log_in_until_password_reset(client, db_session, admin, sent_emails):
    upload(client, admin, csv_bytes(f"one{DOMAIN},2023000001,Student One"))

    response = client.post("/login", data={"username": f"one{DOMAIN}", "password": "anything-at-all"})

    assert response.status_code == 401


def test_database_conflict_creates_nothing(client, db_session, admin, sent_emails, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    def failing_apply(**kwargs):
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    monkeypatch.setattr(student_provisioning_service, "apply_pending_enrollments", failing_apply)

    response = upload(client, admin, csv_bytes(f"one{DOMAIN},2023000001,Student One"))

    assert response.status_code == 409
    assert "No accounts were created" in response.json()["detail"]
    assert students(db_session) == []
    assert sent_emails == []


def test_pending_enrollment_is_completed_for_created_student(client, db_session, admin, sent_emails):
    instructor = make_user(db_session, email=f"faculty{DOMAIN}", role="instructor", school_id="9000000002")
    classroom = Classroom(
        instructor_id=instructor.user_id,
        name="Programming 1",
        subject_code="CCS101",
        section="BSIT 1A",
        class_code="CLASSA01",
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.add(PendingEnrollment(class_id=classroom.class_id, email=f"one{DOMAIN}"))
    db_session.commit()

    response = upload(client, admin, csv_bytes(f"one{DOMAIN},2023000001,Student One"))

    assert response.json()["enrolled_from_pending"] == 1
    db_session.expire_all()
    assert db_session.query(Enrollment).filter(Enrollment.class_id == classroom.class_id).count() == 1


def test_xlsx_is_supported_and_numeric_ids_get_a_hint(client, db_session, admin, sent_emails):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["email", "school_id", "name"])
    sheet.append([f"text{DOMAIN}", "0123456789", "Text Id"])
    sheet.append([f"number{DOMAIN}", 123456789, "Lost Leading Zero"])
    buffer = io.BytesIO()
    workbook.save(buffer)

    response = upload(client, admin, buffer.getvalue(), filename="masterlist.xlsx")

    assert response.status_code == 200, response.text
    rows = response.json()["rows"]
    assert rows[0]["status"] == "created"
    assert rows[1]["status"] == "failed"
    assert "format the school_id column as Text" in rows[1]["reason"]
    assert students(db_session)[0].school_id == "0123456789"


@pytest.mark.parametrize(
    ("content", "filename", "fragment"),
    [
        (b"", "masterlist.csv", "empty"),
        (b"\xff\xfe\x00bad", "masterlist.csv", "UTF-8"),
        (b"email,name\nx@y,z\n", "masterlist.csv", "school_id"),
        (b"email,school_id,name\n", "masterlist.csv", "no student rows"),
        (b"anything", "masterlist.xls", ".xls"),
        (b"anything", "masterlist.txt", ".csv or .xlsx"),
        (b"not a zip", "masterlist.xlsx", "could not be read"),
    ],
)
def test_unreadable_files_are_rejected_whole(client, db_session, admin, sent_emails, content, filename, fragment):
    response = upload(client, admin, content, filename=filename)

    assert response.status_code == 400
    assert fragment in response.json()["detail"]
    assert students(db_session) == []


def test_row_limit_is_enforced(client, db_session, admin, sent_emails):
    rows = [f"s{i}{DOMAIN},{2023000000 + i},Student {i}" for i in range(MAX_MASTERLIST_ROWS + 1)]

    response = upload(client, admin, csv_bytes(*rows))

    assert response.status_code == 400
    assert str(MAX_MASTERLIST_ROWS) in response.json()["detail"]
    assert students(db_session) == []


@pytest.mark.parametrize("role", ["student", "instructor"])
def test_only_admins_can_import(client, db_session, admin, sent_emails, role):
    user = make_user(db_session, email=f"{role}.user{DOMAIN}", role=role, school_id="2023000099")

    response = upload(client, user, csv_bytes(f"one{DOMAIN},2023000001,Student One"))

    assert response.status_code == 403
    assert db_session.query(User).filter(User.email == f"one{DOMAIN}").first() is None


def test_unauthenticated_import_is_rejected(client):
    response = client.post(URL, files={"file": ("m.csv", csv_bytes(f"one{DOMAIN},2023000001,One"), "text/csv")})

    assert response.status_code == 401
