"""Admin account directory: server-side search, role and order (2026-10-28).

Alpha tester: a new account did not appear in the directory search until
"Load more accounts" was clicked. The page filtered only the pages it had
loaded (50 accounts, oldest first). GET /admin/users now searches and
filters by role over every account, and can list the newest first.
"""

from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.domain_models import User
from app.services.guest_service import create_self_service_guest

DOMAIN = "@pampangastateu.edu.ph"


def make_user(db: Session, *, email: str, role: str, school_id: str, name: str) -> User:
    user = User(
        name=name,
        email=email,
        role=role,
        school_id=school_id,
        password_hash=get_password_hash("Original#2026"),
        email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"}


def make_admin(db: Session) -> User:
    return make_user(db, email=f"mis{DOMAIN}", role="admin", school_id="9000000001", name="MIS Admin")


def make_students(db: Session, count: int, *, start: int = 1) -> list[User]:
    return [
        make_user(
            db,
            email=f"student{n:04d}{DOMAIN}",
            role="student",
            school_id=f"2026{n:06d}",
            name=f"Student Number {n}",
        )
        for n in range(start, start + count)
    ]


def ids(response) -> list[int]:
    assert response.status_code == 200, response.text
    return [row["user_id"] for row in response.json()]


def test_search_finds_an_account_beyond_the_first_page(client, db_session):
    admin = make_admin(db_session)
    make_students(db_session, 60)
    newest = make_user(
        db_session, email=f"bagong.estudyante{DOMAIN}", role="student", school_id="2026999999", name="Bagong Estudyante"
    )

    first_page = ids(client.get("/admin/users?skip=0&limit=50", headers=auth(admin)))
    assert newest.user_id not in first_page  # the reported bug: oldest first, 50 a page

    for term in ("bagong", "ESTUDYANTE", "bagong.estudyante@", "2026999999"):
        found = ids(client.get("/admin/users", params={"q": term, "limit": 50}, headers=auth(admin)))
        assert found == [newest.user_id], term


def test_newest_first_puts_a_new_account_on_the_first_page(client, db_session):
    admin = make_admin(db_session)
    make_students(db_session, 60)
    newest = make_user(db_session, email=f"latest{DOMAIN}", role="student", school_id="2026888888", name="Latest Student")

    page = ids(client.get("/admin/users?role=student&order=newest&skip=0&limit=50", headers=auth(admin)))

    assert page[0] == newest.user_id
    assert page == sorted(page, reverse=True)
    assert len(page) == 50


def test_search_pages_through_every_match(client, db_session):
    admin = make_admin(db_session)
    students = make_students(db_session, 55)
    make_user(db_session, email=f"other{DOMAIN}", role="student", school_id="2025000001", name="Someone Else")

    params = {"q": "student number", "role": "student", "order": "newest", "limit": 50}
    first = ids(client.get("/admin/users", params={**params, "skip": 0}, headers=auth(admin)))
    second = ids(client.get("/admin/users", params={**params, "skip": 50}, headers=auth(admin)))

    assert len(first) == 50 and len(second) == 5
    assert set(first) | set(second) == {s.user_id for s in students}


def test_role_filter_keeps_faculty_and_students_apart(client, db_session):
    admin = make_admin(db_session)
    students = make_students(db_session, 3)
    teacher = make_user(db_session, email=f"maria.santos{DOMAIN}", role="instructor", school_id="FAC0000001", name="Maria Santos")

    faculty = ids(client.get("/admin/users?role=instructor", headers=auth(admin)))
    only_students = ids(client.get("/admin/users?role=student", headers=auth(admin)))

    assert faculty == [teacher.user_id]
    assert only_students == [s.user_id for s in students]
    # Admin accounts are never listed, even when searched for by name.
    assert ids(client.get("/admin/users", params={"q": "mis admin"}, headers=auth(admin))) == []


def test_search_treats_like_wildcards_as_text(client, db_session):
    admin = make_admin(db_session)
    make_students(db_session, 3)
    underscored = make_user(db_session, email=f"juan_luna{DOMAIN}", role="student", school_id="2026777777", name="Juan Luna")

    assert ids(client.get("/admin/users", params={"q": "%"}, headers=auth(admin))) == []
    assert ids(client.get("/admin/users", params={"q": "juan_"}, headers=auth(admin))) == [underscored.user_id]
    # "_" is not "any one character": "juanxluna" does not match "juan_luna".
    assert ids(client.get("/admin/users", params={"q": "n_l"}, headers=auth(admin))) == [underscored.user_id]
    assert ids(client.get("/admin/users", params={"q": "nxl"}, headers=auth(admin))) == []


def test_blank_search_lists_everything(client, db_session):
    admin = make_admin(db_session)
    students = make_students(db_session, 2)

    assert ids(client.get("/admin/users", params={"q": "   "}, headers=auth(admin))) == [s.user_id for s in students]


def test_guests_are_searched_only_when_shown(client, db_session):
    admin = make_admin(db_session)
    guest = create_self_service_guest(db_session)

    hidden = ids(client.get("/admin/users", params={"q": "guest", "role": "student"}, headers=auth(admin)))
    shown = ids(
        client.get("/admin/users", params={"q": "guest", "role": "student", "include_guests": "true"}, headers=auth(admin))
    )

    assert guest.user_id not in hidden
    assert shown == [guest.user_id]


def test_bad_parameters_are_refused(client, db_session):
    admin = make_admin(db_session)

    assert client.get("/admin/users?role=admin", headers=auth(admin)).status_code == 422
    assert client.get("/admin/users?order=random", headers=auth(admin)).status_code == 422
    assert client.get("/admin/users", params={"q": "x" * 101}, headers=auth(admin)).status_code == 422


def test_a_new_account_is_found_at_once(client, db_session):
    """Created through the API, then searched: no cache or paging in between."""
    admin = make_admin(db_session)
    make_students(db_session, 60)

    created = client.post(
        "/admin/instructors",
        json={"email": f"bagong.guro{DOMAIN}", "first_name": "Bagong", "last_name": "Guro"},
        headers=auth(admin),
    )
    assert created.status_code == 200, created.text
    new_id = created.json()["user_id"]

    assert ids(client.get("/admin/users", params={"q": "bagong guro", "role": "instructor"}, headers=auth(admin))) == [new_id]
    newest_faculty = ids(client.get("/admin/users?role=instructor&order=newest&limit=50", headers=auth(admin)))
    assert newest_faculty[0] == new_id


def test_students_cannot_list_accounts(client, db_session):
    student = make_students(db_session, 1)[0]

    assert client.get("/admin/users", params={"q": "student"}, headers=auth(student)).status_code == 403
