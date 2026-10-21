"""
Reset the database to a realistic demo semester, keeping the admin accounts.

    cd backend
    DATABASE_URL='postgresql://...' python seed.py --reset

What it does:
1. Shows the target database (host, database and user, never the password),
   the admin accounts that will be kept and how many rows will be deleted,
   then asks you to type the database host to confirm.
2. Refuses unless the database is on the current Alembic revision: deploy
   the backend first so its migrations have run.
3. In ONE transaction, empties every application table except `users` (the
   admin rows are kept, password and all) and `system_settings`, then seeds
   a semester ten weeks in: faculty, students, classes, activities,
   submissions with evaluations and grades, practice progress,
   notifications and the audit trail. If anything fails, the transaction is
   rolled back and the database is left exactly as it was.
4. Writes the demo accounts and their shared password to --accounts-file
   (default ~/Documents/psu_demo_accounts.md, readable only by you). The
   password is DEMO_PASSWORD if set, otherwise random.

    python seed.py --self-check

checks that every activity's code variants behave as labelled (correct
output, structure miss, wrong output, error). It needs no database.

    python seed.py --reset --unattended

is for the local Docker stack (entrypoint.sh): no prompt, and no admin
needed. It runs only with PAMSU_ENVIRONMENT=development or test and
PAMSU_ALLOW_DATABASE_RESET=true, and prints the demo password.

Seeding sends no email: notifications are in-app only, and accounts are
inserted directly rather than through the provisioning endpoints.
"""

import argparse
import os
import random
import secrets
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import seed_content as content

BACKEND_DIR = Path(__file__).resolve().parent
UTC = timezone.utc
PHT = timezone(timedelta(hours=8))
EMAIL_DOMAIN = "@pampangastateu.edu.ph"
MAX_SCORE = 100.0
KEEP_TABLES = {"users", "system_settings"}
DEFAULT_ACCOUNTS_FILE = "~/Documents/psu_demo_accounts.md"


# ---------------------------------------------------------------- code runs


@dataclass(frozen=True)
class RunResult:
    status: str
    stdout: str
    stderr: str
    exit_code: int
    time_ms: int


_run_cache: dict[str, RunResult] = {}


def run_code(code: str) -> RunResult:
    """Run one of this file's own code templates, as the submit run would."""

    if code not in _run_cache:
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-c", code],
                input="",
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.path.expanduser("~"),
            )
            stderr = result.stderr.replace('File "<string>"', 'File "main.py"')
            if result.returncode == 0:
                status = "completed"
            elif "SyntaxError" in stderr or "IndentationError" in stderr:
                status = "syntax_error"
            else:
                status = "runtime_error"
            _run_cache[code] = RunResult(status, result.stdout, stderr, result.returncode, 0)
        except subprocess.TimeoutExpired:
            _run_cache[code] = RunResult("timed_out", "", "", -1, 5000)
    return _run_cache[code]


def fill(template: content.ActivityTemplate, variant: content.Variant, rng: random.Random,
         *, title: str, section: str, choice_index: int | None = None) -> str:
    code = variant.code.replace("@@HEADER@@", rng.choice(content.HEADER_CHOICES))
    code = code.replace("@@TITLE@@", title).replace("@@SECTION@@", section)
    for name, options in template.choices.items():
        pick = options[choice_index % len(options)] if choice_index is not None else rng.choice(options)
        code = code.replace(f"@@{name}@@", pick)
    return code


STYLES = ("main", "docstring", "author")


def apply_styles(code: str, styles: set[str], *, title: str, author: str) -> str:
    """Habits that change the code's structure but not its output."""

    if "main" in styles and '"""' not in code:
        header = []
        lines = code.splitlines()
        while lines and lines[0].startswith("#"):
            header.append(lines.pop(0))
        body = "\n".join(("    " + line) if line.strip() else "" for line in lines).rstrip()
        call = 'if __name__ == "__main__":\n    main()' if len(author) % 2 else "main()"
        code = "\n".join(header + ["def main():", body, "", "", call]) + "\n"
    if "author" in styles:
        code = f'AUTHOR = "{author}"\n' + code
    if "docstring" in styles:
        code = f'"""{title}."""\n' + code
    return code


def random_styles(rng: random.Random) -> set[str]:
    return {style for style, chance in zip(STYLES, (0.3, 0.3, 0.25)) if rng.random() < chance}


# ---------------------------------------------------------------- self-check


def self_check() -> int:
    from app.services.ast_evaluator import evaluate_ast_details

    failures = []
    for template in content.ACTIVITIES.values():
        for index, variant in enumerate(template.variants):
            for choice_index in range(3):
                code = fill(template, variant, random.Random(choice_index), title=template.title,
                            section="BSIT 1-A", choice_index=choice_index)
                run = run_code(code)
                passed = evaluate_ast_details(code, template.rules, "moderate").get("passed")
                label = f"{template.key} variant {index} ({variant.quality})"
                if variant.quality == "correct" and (run.stdout != template.expected_output or not passed):
                    failures.append(f"{label}: output match={run.stdout == template.expected_output}, structure={passed}")
                elif variant.quality == "structure" and (run.stdout != template.expected_output or passed):
                    failures.append(f"{label}: output match={run.stdout == template.expected_output}, structure={passed}")
                elif variant.quality == "wrong" and (run.exit_code != 0 or run.stdout == template.expected_output):
                    failures.append(f"{label}: exit={run.exit_code}, output matches anyway")
                elif variant.quality == "error" and run.exit_code == 0:
                    failures.append(f"{label}: ran without an error")
                if variant.quality in ("correct", "structure"):
                    for style in STYLES:
                        styled = apply_styles(code, {style}, title=template.title, author="J. Dela Cruz")
                        if run_code(styled).stdout != run.stdout:
                            failures.append(f"{label}: style '{style}' changes the output")

    for _, _, lessons in content.PRACTICE_MODULES:
        for lesson in lessons:
            if run_code(lesson.solution).stdout != lesson.expected_output:
                failures.append(f"practice '{lesson.title}': solution output differs")
            if not evaluate_ast_details(lesson.solution, lesson.expected_ast_patterns, "moderate").get("passed"):
                failures.append(f"practice '{lesson.title}': solution fails its structure check")
            mistake = run_code(lesson.mistake)
            mistake_passes = evaluate_ast_details(lesson.mistake, lesson.expected_ast_patterns, "moderate").get("passed")
            if mistake.exit_code == 0 and mistake.stdout == lesson.expected_output and mistake_passes:
                failures.append(f"practice '{lesson.title}': the mistake passes")

    for failure in failures:
        print("FAIL", failure)
    print(f"Self-check: {len(failures)} problem(s) in {len(content.ACTIVITIES)} activities "
          f"and {sum(len(m[2]) for m in content.PRACTICE_MODULES)} practice lessons.")
    return 1 if failures else 0


# ---------------------------------------------------------------- timeline


def pht(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), PHT).astimezone(UTC)


def at_evening(rng: random.Random, day: date) -> datetime:
    return pht(day, rng.choice((13, 15, 18, 19, 20, 21, 22)), rng.randrange(60))


def between(rng: random.Random, start: datetime, end: datetime, skew: float = 1.0) -> datetime:
    """A moment in [start, end]; skew > 1 leans towards the end (deadline rush)."""

    if end <= start:
        return start
    fraction = rng.betavariate(skew, 1.0) if skew != 1.0 else rng.random()
    return start + (end - start) * fraction


@dataclass
class TaskSchedule:
    published_at: datetime | None
    due_at: datetime
    scheduled_publish_at: datetime | None
    state: str  # released | reviewing | open | scheduled


def plan_schedule(rng: random.Random, plan: content.ClassPlan, now: datetime,
                  semester_start: datetime) -> list[TaskSchedule]:
    templates = [content.ACTIVITIES[key] for key in plan.activities]
    schedules: list[TaskSchedule] = []

    if plan.archived:
        # Last semester: everything was published, submitted and released.
        start = semester_start - timedelta(weeks=26)
        for index, template in enumerate(templates):
            published = start + timedelta(days=14 + 21 * index, hours=rng.randrange(2))
            window = 10 if template.activity_type == "homework" else 7
            due = pht((published + timedelta(days=window)).astimezone(PHT).date(), 23, 59)
            schedules.append(TaskSchedule(published, due, None, "released"))
        return schedules

    drafts = 1 if templates[-1].key == "library" else 0
    published_count = len(templates) - drafts
    today = now.astimezone(PHT).date()
    dues: list[date] = []
    due = today + timedelta(days=rng.choice((3, 4, 5)))  # the open activity
    for position in range(published_count):
        dues.append(due)
        due = due - timedelta(days=rng.choice((9, 10, 11)) if position == 0 else rng.choice((9, 10, 12)))
    dues.reverse()

    for index, template in enumerate(templates[:published_count]):
        window = 10 if template.activity_type == "homework" else 7
        due_at = pht(dues[index], 23, 59)
        published = pht(dues[index] - timedelta(days=window), rng.choice((8, 9, 10)), rng.randrange(60))
        published = max(published, semester_start + timedelta(days=2, hours=rng.randrange(3)))
        if due_at > now:
            state = "open"
        elif due_at > now - timedelta(days=8):
            state = "reviewing"
        else:
            state = "released"
        schedules.append(TaskSchedule(published, due_at, None, state))

    if drafts:
        publish_day = today + timedelta(days=rng.choice((3, 4)))
        scheduled = pht(publish_day, 8)
        schedules.append(TaskSchedule(None, pht(publish_day + timedelta(days=7), 23, 59), scheduled, "scheduled"))
    return schedules


# ---------------------------------------------------------------- people


@dataclass
class Person:
    name: str
    email: str
    school_id: str
    role: str
    created_at: datetime
    engagement: float = 0.8
    skill: float = 0.5
    styles: set = field(default_factory=set)  # coding habits, the same every week
    user: object = None
    class_keys: list[str] = field(default_factory=list)


def email_local(first: str, last: str) -> str:
    def clean(text: str) -> str:
        return "".join(ch for ch in text.lower() if ch.isalpha())
    return f"{clean(first)}.{clean(last)}"


def make_students(rng: random.Random, count: int, year_prefix: str, used_names: set,
                  used_locals: set, used_ids: set, created_at: datetime) -> list[Person]:
    people = []
    while len(people) < count:
        first = rng.choice(content.FIRST_NAMES)
        last = rng.choice(content.SURNAMES)
        if (first, last) in used_names:
            continue
        used_names.add((first, last))
        local = email_local(first, last)
        suffix = 2
        while local in used_locals:
            local = f"{email_local(first, last)}{suffix}"
            suffix += 1
        used_locals.add(local)
        school_id = f"{year_prefix}{rng.randrange(100000, 999999)}"
        while school_id in used_ids:
            school_id = f"{year_prefix}{rng.randrange(100000, 999999)}"
        used_ids.add(school_id)
        engagement = 0.35 if rng.random() < 0.05 else rng.betavariate(6, 1.4)
        people.append(Person(
            name=f"{first} {last}", email=f"{local}{EMAIL_DOMAIN}", school_id=school_id, role="student",
            created_at=created_at, engagement=engagement, skill=rng.betavariate(2.5, 1.6),
            styles=random_styles(rng),
        ))
    return people


# ---------------------------------------------------------------- reset


def describe_target(db) -> dict:
    url = db.get_bind().url
    return {"dialect": url.get_backend_name(), "host": url.host or "(local file)", "port": url.port,
            "database": url.database, "username": url.username}


def check_migrations(db, dialect: str) -> str | None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import inspect, text

    head = ScriptDirectory.from_config(Config(str(BACKEND_DIR / "alembic.ini"))).get_current_head()
    if not inspect(db.get_bind()).has_table("alembic_version"):
        if dialect == "postgresql":
            return f"No alembic_version table. Run the migrations first (expected revision {head})."
        return None  # a local SQLite database built with create_all
    current = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    if current != head:
        return (f"The database is at revision {current}, but this code expects {head}. "
                "Deploy the backend first (Render runs the migrations), then seed.")
    return None


def reset_database(db, dialect: str) -> None:
    from app.core.database import Base
    from sqlalchemy import text

    tables = [table.name for table in Base.metadata.sorted_tables if table.name not in KEEP_TABLES]
    if dialect == "postgresql":
        quoted = ", ".join(f'"{name}"' for name in tables)
        db.execute(text("SET LOCAL lock_timeout = '15s'"))
        db.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    else:
        for name in reversed(tables):
            db.execute(text(f'DELETE FROM "{name}"'))
    db.execute(text("DELETE FROM users WHERE role <> 'admin'"))


# ---------------------------------------------------------------- seeding


class Seeder:
    def __init__(self, db, rng: random.Random, now: datetime, password_hash: str, admin):
        from app.models import domain_models as models

        self.db = db
        self.m = models
        self.rng = rng
        self.now = now
        self.password_hash = password_hash
        self.admin = admin
        today = now.astimezone(PHT).date()
        start_day = today - timedelta(weeks=10)
        start_day -= timedelta(days=start_day.weekday())
        self.semester_start = pht(start_day, 7, 30)
        self.audit: list = []
        self.events: list = []
        self.notifications: list = []
        self.people: dict[str, Person] = {}
        self.students_by_class: dict[str, list[Person]] = {}
        self.dropped: dict[str, tuple[Person, datetime]] = {}

    # -- helpers

    def add_audit(self, *, key, actor, action, resource_type, resource_id, data, at, outcome="succeeded"):
        self.audit.append(self.m.AuditRecord(
            audit_key=key, actor_user_id=actor, action_type=action, resource_type=resource_type,
            resource_id=str(resource_id), outcome=outcome, audit_data=data, occurred_at=at, created_at=at,
        ))

    def add_event(self, *, key, event_type, actor, resource_type, resource_id, data, at, title, message, recipients):
        event = self.m.AcademicEvent(
            event_id=str(uuid4()), event_key=key, event_type=event_type, actor_user_id=actor,
            resource_type=resource_type, resource_id=str(resource_id), event_data=data, occurred_at=at, created_at=at,
        )
        self.events.append(event)
        for recipient in recipients:
            age = self.now - at
            read = self.rng.random() < (0.92 if age > timedelta(days=3) else 0.35)
            read_at = min(self.now, at + timedelta(hours=self.rng.uniform(0.5, 40))) if read else None
            self.notifications.append(self.m.Notification(
                notification_id=str(uuid4()), event_id=event.event_id, recipient_id=recipient, title=title,
                message=message, is_read=read, read_at=read_at, created_at=at, updated_at=read_at or at,
            ))

    # -- people

    def create_people(self) -> None:
        m, rng = self.m, self.rng
        for first, last, local, school_id, strictness, joined in content.INSTRUCTORS:
            joined_at = pht(date.fromisoformat(joined), 9)
            person = Person(f"{first} {last}", f"{local}{EMAIL_DOMAIN}", school_id, "instructor", joined_at)
            person.user = m.User(
                name=person.name, email=person.email, school_id=school_id, role="instructor",
                password_hash=self.password_hash, email_verified=True, is_active=True,
                ast_strictness_level=strictness, created_at=joined_at, updated_at=joined_at,
            )
            self.people[local] = person

        used_names, used_locals, used_ids = set(), set(), set()
        first_year_created = self.semester_start - timedelta(days=9)
        second_year_created = first_year_created - timedelta(weeks=52)
        for plan in content.CLASSES:
            if plan.archived:
                continue
            prefix = "2026" if plan.year_level == 1 else "2025"
            created = first_year_created if plan.year_level == 1 else second_year_created
            students = make_students(rng, plan.size, prefix, used_names, used_locals, used_ids, created)
            self.students_by_class[plan.key] = students
        # Last semester's BSCS 1-A is this semester's BSCS 2-A.
        self.students_by_class["cp2-cs-a-prev"] = list(self.students_by_class["dsa-cs-a"])

        for plan_key, students in self.students_by_class.items():
            for person in students:
                person.class_keys.append(plan_key)
                if person.user is None:
                    person.user = m.User(
                        name=person.name, email=person.email, school_id=person.school_id, role="student",
                        password_hash=self.password_hash, email_verified=True, is_active=True,
                        created_at=person.created_at, updated_at=person.created_at,
                    )
        all_users = [p.user for p in self.people.values()]
        all_users += list({id(p): p.user for s in self.students_by_class.values() for p in s}.values())
        self.db.add_all(all_users)
        self.db.flush()

        # MIS provisioning this school year, as the admin dashboard records it.
        if self.admin is None:
            return
        admin_id = self.admin.user_id
        for local in content.NEWLY_PROVISIONED_FACULTY:
            person = self.people[local]
            at = self.semester_start - timedelta(days=21)
            person.user.created_at = person.user.updated_at = at
            self.add_audit(key=f"audit:user_created:user:{person.user.user_id}:{uuid4()}", actor=admin_id,
                           action="user_created", resource_type="user", resource_id=person.user.user_id,
                           data={"role": "instructor", "source": "admin_instructor_form",
                                 "setup_email": "queued_after_commit"}, at=at)
        for plan in content.CLASSES:
            if plan.archived or plan.year_level != 1:
                continue
            import_id = str(uuid4())
            at = first_year_created + timedelta(minutes=rng.randrange(20, 300))
            students = self.students_by_class[plan.key]
            for row, person in enumerate(students, start=2):
                self.add_audit(key=f"audit:user_created:user:{person.user.user_id}:{uuid4()}", actor=admin_id,
                               action="user_created", resource_type="user", resource_id=person.user.user_id,
                               data={"role": "student", "source": "masterlist_import", "import_id": import_id,
                                     "row": row, "setup_email": "queued_after_commit"}, at=at)
            self.add_audit(key=f"audit:masterlist_imported:masterlist_import:{import_id}", actor=admin_id,
                           action="masterlist_imported", resource_type="masterlist_import", resource_id=import_id,
                           data={"file_type": "xlsx", "rows": len(students), "created": len(students), "skipped": 0,
                                 "failed": 0, "enrolled_from_pending": 0, "pending_left": 0}, at=at)

    # -- classes

    def create_classes(self) -> list[tuple]:
        m, rng = self.m, self.rng
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        used_codes = set()
        classes = []
        for plan in content.CLASSES:
            instructor = self.people[plan.instructor].user
            if plan.archived:
                created = self.semester_start - timedelta(weeks=27)
            else:
                created = self.semester_start - timedelta(days=rng.randrange(2, 6), hours=rng.randrange(6))
            code = "".join(rng.choice(alphabet) for _ in range(8))
            while code in used_codes:
                code = "".join(rng.choice(alphabet) for _ in range(8))
            used_codes.add(code)
            archived_at = (self.semester_start - timedelta(weeks=9)) if plan.archived else None
            classroom = m.Classroom(
                instructor_id=instructor.user_id, name=plan.name, subject_code=plan.subject_code,
                section=plan.section, class_code=code, is_active=not plan.archived, archived_at=archived_at,
                created_at=created, updated_at=archived_at or created,
            )
            classes.append((plan, classroom, instructor, created))
        self.db.add_all([c[1] for c in classes])
        self.db.flush()

        enrollments = []
        for plan, classroom, instructor, created in classes:
            self.add_audit(key=f"audit:classroom_created:classroom:{classroom.class_id}", actor=instructor.user_id,
                           action="classroom_created", resource_type="classroom", resource_id=classroom.class_id,
                           data={"subject_code": plan.subject_code, "section": plan.section, "is_active": True},
                           at=created)
            joined = created + timedelta(days=rng.randrange(1, 3), hours=rng.randrange(1, 5))
            students = self.students_by_class[plan.key]
            drop = None
            if plan.key in ("cp1-it-b", "ipt-it-b"):
                drop = students[rng.randrange(len(students))]
                drop_at = self.semester_start + timedelta(days=rng.randrange(18, 26), hours=10)
                self.dropped[plan.key] = (drop, drop_at)
            for person in students:
                removed = person is drop
                enrollment = m.Enrollment(
                    class_id=classroom.class_id, student_id=person.user.user_id,
                    status="removed" if removed else "active", joined_at=joined,
                    deactivated_at=self.dropped[plan.key][1] if removed else None,
                )
                enrollments.append((plan, classroom, instructor, person, enrollment, joined))
        self.db.add_all([e[4] for e in enrollments])
        self.db.flush()

        for plan, classroom, instructor, person, enrollment, joined in enrollments:
            self.add_audit(key=f"audit:student_enrolled:enrollment:{enrollment.enrollment_id}",
                           actor=instructor.user_id, action="student_enrolled", resource_type="enrollment",
                           resource_id=enrollment.enrollment_id,
                           data={"class_id": classroom.class_id, "student_id": person.user.user_id}, at=joined)
            if enrollment.status == "removed":
                self.add_audit(key=f"audit:enrollment_status_changed:enrollment:{enrollment.enrollment_id}:{uuid4()}",
                               actor=instructor.user_id, action="enrollment_status_changed",
                               resource_type="enrollment", resource_id=enrollment.enrollment_id,
                               data={"class_id": classroom.class_id, "student_id": person.user.user_id,
                                     "previous_status": "active", "new_status": "removed"},
                               at=enrollment.deactivated_at)

        for plan, classroom, instructor, created in classes:
            if plan.key in content.PENDING_ENROLLEES:
                first, last = content.PENDING_ENROLLEES[plan.key]
                self.db.add(m.PendingEnrollment(class_id=classroom.class_id,
                                                email=f"{email_local(first, last)}{EMAIL_DOMAIN}",
                                                created_at=created + timedelta(days=12)))
            if plan.archived:
                at = classroom.archived_at
                self.add_audit(key=f"audit:classroom_archived:classroom:{classroom.class_id}:{uuid4()}",
                               actor=instructor.user_id, action="classroom_archived", resource_type="classroom",
                               resource_id=classroom.class_id,
                               data={"changed_fields": ["is_active"], "previous_active": True, "new_active": False},
                               at=at)
                token = at.astimezone(UTC).isoformat(timespec="microseconds")
                self.add_event(key=f"classroom_archived:classroom:{classroom.class_id}:{token}",
                               event_type="classroom_archived", actor=instructor.user_id, resource_type="classroom",
                               resource_id=classroom.class_id,
                               data={"class_id": classroom.class_id, "archived_at": token}, at=at,
                               title="Classroom archived", message=f"{classroom.name} has been archived.",
                               recipients=[p.user.user_id for p in self.students_by_class[plan.key]])
        return classes

    # -- activities and student work

    def create_activities(self, classes: list[tuple]) -> None:
        m, rng = self.m, self.rng
        task_rows = []
        for plan, classroom, instructor, created in classes:
            for template, schedule in zip((content.ACTIVITIES[k] for k in plan.activities),
                                          plan_schedule(rng, plan, self.now, self.semester_start)):
                created_at = (schedule.published_at or schedule.scheduled_publish_at) - timedelta(
                    days=rng.randrange(1, 4), hours=rng.randrange(1, 6))
                task = m.Task(
                    class_id=classroom.class_id, instructor_id=instructor.user_id, title=template.title,
                    description=template.description, instructions=template.instructions,
                    scenario=template.scenario, solution_explanation=template.solution_explanation,
                    activity_type=template.activity_type, difficulty=template.difficulty,
                    required_ast_rules=template.rules, starter_code=template.starter_code,
                    paste_policy="disabled" if template.activity_type == "laboratory" and rng.random() < 0.4 else "internal_only",
                    is_graded=True, is_published=schedule.state != "scheduled", due_at=schedule.due_at,
                    published_at=schedule.published_at, scheduled_publish_at=schedule.scheduled_publish_at,
                    created_at=created_at, updated_at=schedule.published_at or created_at,
                )
                task_rows.append((plan, classroom, instructor, template, schedule, task))
        self.db.add_all([row[5] for row in task_rows])
        self.db.flush()

        test_cases = []
        for plan, classroom, instructor, template, schedule, task in task_rows:
            test_cases.append(m.TaskTestCase(task_id=task.task_id, name="Sample output", standard_input="",
                                             expected_output=template.expected_output, is_hidden=False,
                                             display_order=0, created_at=task.created_at))
            test_cases.append(m.TaskTestCase(task_id=task.task_id, name="Exact formatting", standard_input="",
                                             expected_output=template.expected_output, is_hidden=True,
                                             display_order=1, created_at=task.created_at))
            self.add_audit(key=f"audit:activity_created:task:{task.task_id}", actor=instructor.user_id,
                           action="activity_created", resource_type="task", resource_id=task.task_id,
                           data={"class_id": classroom.class_id, "activity_type": task.activity_type,
                                 "is_graded": True, "is_published": False, "paste_policy": task.paste_policy},
                           at=task.created_at)
            if schedule.published_at is None:
                continue
            self.add_audit(key=f"audit:activity_published:task:{task.task_id}:{uuid4()}", actor=instructor.user_id,
                           action="activity_published", resource_type="task", resource_id=task.task_id,
                           data={"class_id": classroom.class_id, "previous_state": "draft", "new_state": "published"},
                           at=schedule.published_at)
            token = schedule.published_at.astimezone(UTC).isoformat(timespec="microseconds")
            recipients = [p.user.user_id for p in self.students_by_class[plan.key]
                          if not self._dropped_before(plan.key, p, schedule.published_at)]
            self.add_event(key=f"activity_published:task:{task.task_id}:{token}", event_type="activity_published",
                           actor=instructor.user_id, resource_type="task", resource_id=task.task_id,
                           data={"task_id": task.task_id, "class_id": classroom.class_id,
                                 "activity_type": task.activity_type, "published_at": token},
                           at=schedule.published_at, title="New activity published",
                           message=f"{task.title} is now available in {classroom.name}.", recipients=recipients)
        self.db.add_all(test_cases)
        self._create_submissions(task_rows)

    def _dropped_before(self, plan_key: str, person: Person, moment: datetime) -> bool:
        dropped = self.dropped.get(plan_key)
        return bool(dropped and dropped[0] is person and dropped[1] <= moment)

    def _choose_variant(self, template, person: Person, *, retry: bool) -> content.Variant:
        weights = []
        for variant in template.variants:
            weight = variant.weight
            if variant.quality == "correct":
                weight *= (0.6 + person.skill) * (2.5 if retry else 1.0)
            elif variant.quality == "error":
                weight *= (1.4 - person.skill) * (0.2 if retry else 1.0)
            weights.append(max(weight, 0.01))
        return self.rng.choices(template.variants, weights=weights)[0]

    def _create_submissions(self, task_rows: list[tuple]) -> None:
        from app.services.ast_evaluator import evaluate_ast_details

        m, rng = self.m, self.rng
        attempts = []  # (task_row, person, variant, code, submitted_at, attempt_number)
        for row in task_rows:
            plan, classroom, instructor, template, schedule, task = row
            if schedule.state == "scheduled":
                continue
            window_end = min(schedule.due_at - timedelta(minutes=rng.randrange(1, 90)), self.now - timedelta(minutes=40))
            for person in self.students_by_class[plan.key]:
                if self._dropped_before(plan.key, person, schedule.published_at + timedelta(days=2)):
                    continue
                chance = person.engagement * (0.55 if schedule.state == "open" else 1.0)
                if rng.random() > chance:
                    continue
                first_at = between(rng, schedule.published_at + timedelta(hours=2), window_end, skew=2.2)
                variant = self._choose_variant(template, person, retry=False)
                code = apply_styles(fill(template, variant, rng, title=template.title, section=plan.section),
                                    person.styles, title=template.title, author=person.name)
                attempts.append((row, person, variant, code, first_at, 1))
                if variant.quality != "correct" and rng.random() < 0.6 * person.engagement and first_at < window_end:
                    second_at = between(rng, first_at + timedelta(minutes=20), window_end, skew=1.5)
                    if second_at > first_at:
                        retry_variant = self._choose_variant(template, person, retry=True)
                        retry_code = apply_styles(
                            fill(template, retry_variant, rng, title=template.title, section=plan.section),
                            person.styles, title=template.title, author=person.name)
                        attempts.append((row, person, retry_variant, retry_code, second_at, 2))

        last_attempt = {}
        for index, (row, person, *_rest, attempt_number) in enumerate(attempts):
            last_attempt[(row[5].task_id, person.user.user_id)] = index

        sessions, submissions = [], []
        for index, (row, person, variant, code, submitted_at, attempt_number) in enumerate(attempts):
            plan, classroom, instructor, template, schedule, task = row
            run_count = rng.randrange(1, 6) + (3 if variant.quality != "correct" else 0)
            heavy = rng.random() < 0.06
            session = m.CodingSession(
                session_id=str(uuid4()), student_id=person.user.user_id, task_id=task.task_id,
                started_at=submitted_at - timedelta(minutes=rng.randrange(9, 80)), ended_at=submitted_at,
                last_activity_at=submitted_at, tab_switch_count=rng.randrange(8, 22) if heavy else rng.randrange(0, 5),
                blocked_paste_count=rng.randrange(1, 4) if heavy or rng.random() < 0.08 else 0,
                mouseleave_count=rng.randrange(0, 9), run_attempt_count=run_count,
                idle_duration_seconds=rng.randrange(20, 600),
            )
            sessions.append(session)
            official = last_attempt[(task.task_id, person.user.user_id)] == index
            submissions.append(m.Submission(
                student_id=person.user.user_id, task_id=task.task_id, coding_session_id=session.session_id,
                attempt_number=attempt_number, raw_code=code, standard_input="", status="submitted",
                is_official=official, submitted_at=submitted_at, accepted_at=submitted_at,
            ))
        self.db.add_all(sessions)
        self.db.flush()
        self.db.add_all(submissions)
        self.db.flush()

        executions, logs, analyses = [], [], []
        by_task_official: dict[int, dict[int, str]] = defaultdict(dict)
        records = list(zip(attempts, sessions, submissions))
        for (row, person, variant, code, submitted_at, _), session, submission in records:
            plan, classroom, instructor, template, schedule, task = row
            result = run_code(code)
            started = submitted_at + timedelta(seconds=rng.randrange(1, 4))
            executions.append(m.ExecutionRequest(
                student_id=person.user.user_id, task_id=task.task_id, submission_id=submission.sub_id,
                coding_session_id=session.session_id, request_kind="submit", status=result.status,
                source_code=code, standard_input="", stdout=result.stdout, stderr=result.stderr,
                exit_code=result.exit_code, execution_time_ms=rng.randrange(18, 140), queued_at=submitted_at,
                started_at=started, completed_at=started + timedelta(milliseconds=rng.randrange(300, 2500)),
                last_partner_sequence=1,
            ))
            logs.append(m.BehavioralLog(
                sub_id=submission.sub_id, tab_switches_count=session.tab_switch_count,
                blocked_paste_count=session.blocked_paste_count, mouseleave_count=session.mouseleave_count,
                run_attempt_count=session.run_attempt_count, idle_duration_seconds=session.idle_duration_seconds,
                created_at=submitted_at, updated_at=submitted_at,
            ))
            details = evaluate_ast_details(code, task.required_ast_rules, instructor.ast_strictness_level)
            submission.ast_pass_fail = bool(details.get("passed", False))
            analyses.append(m.ASTAnalysis(submission_id=submission.sub_id, overall_pass=submission.ast_pass_fail,
                                          syntax_error=details.get("syntax_error"), details=details,
                                          created_at=submitted_at + timedelta(seconds=rng.randrange(4, 30))))
            if submission.is_official:
                by_task_official[task.task_id][submission.sub_id] = code

            self.add_audit(key=f"audit:submission_created:submission:{submission.sub_id}",
                           actor=person.user.user_id, action="submission_created", resource_type="submission",
                           resource_id=submission.sub_id,
                           data={"task_id": task.task_id, "class_id": classroom.class_id,
                                 "attempt_number": submission.attempt_number, "submission_status": "submitted",
                                 "is_official": True}, at=submitted_at)
            self.add_event(key=f"submission_created:submission:{submission.sub_id}", event_type="submission_created",
                           actor=person.user.user_id, resource_type="submission", resource_id=submission.sub_id,
                           data={"submission_id": submission.sub_id, "task_id": task.task_id,
                                 "class_id": classroom.class_id, "attempt_number": submission.attempt_number,
                                 "is_official": True},
                           at=submitted_at, title="Submission received",
                           message=f"{person.name} submitted {task.title}, attempt {submission.attempt_number}.",
                           recipients=[instructor.user_id])
        self.db.add_all(executions + logs + analyses)
        self._similarity(records, by_task_official)
        self._grades(records)

    def _similarity(self, records, by_task_official) -> None:
        from app.services.jaccard import find_highest_similarity

        # Like the live evaluation: compare with other students' official attempts only.
        owners = {submission.sub_id: submission.student_id for _attempt, _session, submission in records}
        results = []
        for _attempt, _session, submission in records:
            others = {sub_id: code for sub_id, code in by_task_official[submission.task_id].items()
                      if owners[sub_id] != submission.student_id}
            if not others:
                submission.jaccard_score = 0.0
                continue
            details = find_highest_similarity(target_code=submission.raw_code, comparison_submissions=others,
                                              shingle_size=3)
            score = float(details.get("highest_score") or 0.0)
            submission.jaccard_score = score
            match = details.get("highest_match_sub_id")
            if match is not None:
                results.append(self.m.SimilarityResult(
                    source_submission_id=submission.sub_id, compared_submission_id=match, score=score,
                    algorithm="jaccard", created_at=submission.submitted_at + timedelta(seconds=40),
                ))
        self.db.add_all(results)

    def _grades(self, records) -> None:
        m, rng = self.m, self.rng
        grades = []
        release_day: dict[int, datetime] = {}
        for (row, person, variant, code, submitted_at, _), _session, submission in records:
            plan, classroom, instructor, template, schedule, task = row
            if not submission.is_official or schedule.state in ("open", "scheduled"):
                continue
            if schedule.state == "reviewing" and rng.random() > 0.55:
                continue
            earliest = schedule.due_at + timedelta(hours=10)
            latest = min(schedule.due_at + timedelta(days=5), self.now - timedelta(hours=1))
            if earliest >= latest:
                continue
            graded_at = between(rng, earliest, latest)
            if variant.quality == "correct":
                low, high = (90, 100) if submission.ast_pass_fail else (78, 88)
            else:
                low, high = {"structure": (72, 85), "wrong": (62, 78), "error": (50, 65)}[variant.quality]
            released = schedule.state == "released"
            if released:
                release = release_day.setdefault(task.task_id, schedule.due_at + timedelta(
                    days=rng.randrange(5, 8), hours=rng.randrange(3)))
                release = min(max(release, graded_at + timedelta(minutes=5)), self.now - timedelta(minutes=30))
            grade = m.InstructorGrade(
                submission_id=submission.sub_id, instructor_id=instructor.user_id,
                score=float(rng.randrange(low, high + 1)), max_score=MAX_SCORE,
                feedback=rng.choice(content.GRADE_FEEDBACK[variant.quality]), is_released=released,
                created_at=graded_at, updated_at=release if released else graded_at,
            )
            submission.status = "graded" if released else "awaiting_review"
            grades.append((row, person, submission, grade, graded_at))
        self.db.add_all([g[3] for g in grades])
        self.db.flush()

        for row, person, submission, grade, graded_at in grades:
            plan, classroom, instructor, template, schedule, task = row
            base = {"submission_id": submission.sub_id, "task_id": task.task_id, "class_id": classroom.class_id,
                    "previous_release_state": "unreleased"}
            self.add_audit(key=f"audit:grade_created:grade:{grade.grade_id}", actor=instructor.user_id,
                           action="grade_created", resource_type="grade", resource_id=grade.grade_id,
                           data={**base, "new_release_state": "unreleased",
                                 "created_fields": ["feedback", "is_released", "max_score", "score"]}, at=graded_at)
            if not grade.is_released:
                continue
            release = grade.updated_at
            self.add_audit(key=f"audit:grade_released:grade:{grade.grade_id}:{uuid4()}", actor=instructor.user_id,
                           action="grade_released", resource_type="grade", resource_id=grade.grade_id,
                           data={**base, "new_release_state": "released"}, at=release)
            token = release.astimezone(UTC).isoformat(timespec="microseconds")
            self.add_event(key=f"grade_released:grade:{grade.grade_id}:{token}", event_type="grade_released",
                           actor=instructor.user_id, resource_type="grade", resource_id=grade.grade_id,
                           data={"grade_id": grade.grade_id, "submission_id": submission.sub_id,
                                 "task_id": task.task_id, "class_id": classroom.class_id, "released_at": token},
                           at=release, title="Grade released",
                           message=f"A manual grade for {task.title} is now available.",
                           recipients=[person.user.user_id])

    # -- practice

    def create_practice(self) -> None:
        m, rng = self.m, self.rng
        lessons = []
        for module_index, (title, description, module_lessons) in enumerate(content.PRACTICE_MODULES, start=1):
            module = m.PracticeModule(title=title, description=description, order_index=module_index)
            self.db.add(module)
            self.db.flush()
            for lesson_index, lesson in enumerate(module_lessons, start=1):
                task = m.PracticeTask(module_id=module.module_id, title=lesson.title, instructions=lesson.instructions,
                                      starter_code=lesson.starter_code, expected_output=lesson.expected_output,
                                      expected_ast_patterns=lesson.expected_ast_patterns, order_index=lesson_index)
                lessons.append((lesson, task))
        self.db.add_all([task for _, task in lessons])
        self.db.flush()

        students = {id(p): p for s in self.students_by_class.values() for p in s}.values()
        progress, attempts = [], []
        start = self.semester_start + timedelta(days=3)
        span = (self.now - timedelta(hours=3)) - start
        for person in students:
            reach = int(round(len(lessons) * min(1.0, person.engagement * rng.uniform(0.25, 1.15))))
            moment = start + span * rng.uniform(0.0, 0.3)
            for position, (lesson, task) in enumerate(lessons[: reach + 1]):
                finished = position < reach
                failures = rng.choices((0, 1, 2), weights=(6, 3, 1))[0] if finished else rng.randrange(1, 3)
                for _ in range(failures):
                    moment = min(moment + timedelta(minutes=rng.randrange(3, 25)), self.now - timedelta(hours=1))
                    attempts.append(m.PracticeAttempt(
                        student_id=person.user.user_id, task_id=task.task_id, submitted_code=lesson.mistake,
                        is_successful=False, execution_feedback=lesson.mistake_feedback, ast_feedback=[],
                        created_at=moment))
                if finished:
                    moment = min(moment + timedelta(minutes=rng.randrange(2, 20)), self.now - timedelta(hours=1))
                    attempts.append(m.PracticeAttempt(
                        student_id=person.user.user_id, task_id=task.task_id, submitted_code=lesson.solution,
                        is_successful=True, execution_feedback=None, ast_feedback=[], created_at=moment))
                if failures or finished:
                    progress.append(m.PracticeProgress(
                        student_id=person.user.user_id, task_id=task.task_id, is_completed=finished,
                        completed_at=moment if finished else None, attempts_count=failures + int(finished)))
                # The next lesson is usually on another day.
                moment = moment + timedelta(days=rng.uniform(0.5, 6))
                if moment > self.now - timedelta(hours=6):
                    break
        self.db.add_all(progress + attempts)

    # -- sign-ins

    def create_sign_ins(self) -> None:
        rng = self.rng
        weeks = int((self.now - self.semester_start).days / 7) + 1
        staff = [(p, 4) for p in self.people.values()]
        students = [(p, 2) for p in {id(p): p for s in self.students_by_class.values() for p in s}.values()]
        for person, per_week in staff + students:
            user = person.user
            for week in range(weeks):
                for _ in range(per_week):
                    if rng.random() > person.engagement:
                        continue
                    day = (self.semester_start + timedelta(weeks=week, days=rng.randrange(7))).astimezone(PHT).date()
                    at = at_evening(rng, day)
                    if at < user.created_at or at >= self.now:
                        continue
                    if rng.random() < 0.03:
                        self.add_audit(key=f"login_failed_{user.user_id}_{uuid4().hex[:8]}", actor=user.user_id,
                                       action="login_failed", resource_type="user", resource_id=user.user_id,
                                       data={"email": user.email}, at=at - timedelta(minutes=1), outcome="failed")
                    self.add_audit(key=f"login_{user.user_id}_{uuid4().hex[:8]}", actor=user.user_id,
                                   action="login_succeeded", resource_type="user", resource_id=user.user_id,
                                   data={"email": user.email}, at=at)
        admin = self.admin
        for week in range(weeks if admin is not None else 0):
            for _ in range(2):
                at = at_evening(rng, (self.semester_start + timedelta(weeks=week, days=rng.randrange(5))).astimezone(PHT).date())
                if at < self.now:
                    self.add_audit(key=f"login_{admin.user_id}_{uuid4().hex[:8]}", actor=admin.user_id,
                                   action="login_succeeded", resource_type="user", resource_id=admin.user_id,
                                   data={"email": admin.email}, at=at)
        for _ in range(4):
            at = at_evening(rng, (self.now - timedelta(days=rng.randrange(1, 60))).astimezone(PHT).date())
            if at < self.now:
                self.add_audit(key=f"login_failed_anon_{uuid4().hex[:8]}", actor=None, action="login_failed",
                               resource_type="user", resource_id="unrecognized", data={"identifier": "unrecognized"},
                               at=at, outcome="failed")

    def run(self) -> None:
        self.create_people()
        classes = self.create_classes()
        self.create_activities(classes)
        self.create_practice()
        self.create_sign_ins()
        self.db.add_all(self.events)
        self.db.flush()
        self.db.add_all(self.notifications + self.audit)
        self.db.flush()


# ---------------------------------------------------------------- accounts file


def write_accounts_file(path: Path, password: str, seeder: Seeder, generated_at: datetime) -> None:
    lines = [
        "# PSU Python IDE demo accounts",
        "",
        f"Seeded {generated_at.astimezone(PHT):%Y-%m-%d %H:%M} (PHT). Keep this file private.",
        "",
        f"**Password for every demo account below:** `{password}`",
        "",
        "Admin accounts were kept as they were, with their own passwords.",
        "",
        "## Faculty",
        "",
        "| Name | Email | Classes |",
        "|---|---|---|",
    ]
    class_names = {p.key: f"{p.subject_code} {p.section}" + (" (archived)" if p.archived else "") for p in content.CLASSES}
    for local, person in seeder.people.items():
        taught = [class_names[p.key] for p in content.CLASSES if p.instructor == local]
        lines.append(f"| {person.name} | {person.email} | {', '.join(taught)} |")
    for plan in content.CLASSES:
        if plan.archived:
            continue
        lines += ["", f"## {plan.subject_code} {plan.name}, {plan.section}", "", "| Name | Email | School ID |", "|---|---|---|"]
        for person in sorted(seeder.students_by_class[plan.key], key=lambda p: p.name.split()[-1]):
            lines.append(f"| {person.name} | {person.email} | {person.school_id} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    os.chmod(path, 0o600)


# ---------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="Empty the database (keeping admins) and seed the demo.")
    parser.add_argument("--self-check", action="store_true", help="Check the activity code variants; no database.")
    parser.add_argument("--confirm-host", help="Skip the prompt: the database host you are resetting.")
    parser.add_argument("--unattended", action="store_true",
                        help="Local Docker stack only (see above): no prompt, no admin needed.")
    parser.add_argument("--accounts-file", default=DEFAULT_ACCOUNTS_FILE, help=f"Default: {DEFAULT_ACCOUNTS_FILE}")
    parser.add_argument("--random-seed", type=int, default=20261022, help="Same seed, same people and classes.")
    args = parser.parse_args()

    if args.self_check:
        return self_check()
    if not args.reset:
        parser.print_help()
        return 2
    if args.unattended and not (
        os.getenv("PAMSU_ENVIRONMENT", "").strip().lower() in {"development", "test"}
        and os.getenv("PAMSU_ALLOW_DATABASE_RESET", "").strip().lower() == "true"
    ):
        print("--unattended needs PAMSU_ENVIRONMENT=development (or test) and PAMSU_ALLOW_DATABASE_RESET=true.")
        return 1

    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from sqlalchemy import func

    db = SessionLocal()
    try:
        target = describe_target(db)
        problem = check_migrations(db, target["dialect"])
        if problem:
            print(problem)
            return 1

        from app.models.domain_models import Classroom, Submission, User

        admins = db.query(User).filter(User.role == "admin").order_by(User.user_id).all()
        if not admins and not args.unattended:
            print("No admin account found; nothing would be kept. Create one with seed_admin.py first.")
            return 1
        others = db.query(func.count(User.user_id)).filter(User.role != "admin").scalar()
        classes = db.query(func.count(Classroom.class_id)).scalar()
        submissions = db.query(func.count(Submission.sub_id)).scalar()

        print("Target database:")
        for key in ("dialect", "host", "port", "database", "username"):
            print(f"  {key:9} {target[key]}")
        print(f"Admin accounts kept ({len(admins)}): " + ", ".join(a.email for a in admins))
        print(f"Will DELETE {others} other account(s), {classes} class(es), {submissions} submission(s) "
              "and everything else except system settings.")

        expected = target["host"]
        if not args.unattended:
            typed = args.confirm_host
            if typed is None:
                typed = input(f"Type the database host ({expected}) to confirm: ").strip()
            if typed != expected:
                print("Host does not match; nothing was changed.")
                return 1

        password = os.getenv("DEMO_PASSWORD") or f"Psu-{secrets.token_urlsafe(6)}-{secrets.randbelow(90) + 10}"
        password_hash = get_password_hash(password)
        now = datetime.now(UTC)
        db.rollback()  # end the read transaction; the reset runs in a fresh one

        print("Resetting and seeding in one transaction (this can take a minute or two)...")
        try:
            reset_database(db, target["dialect"])
            admin = db.query(User).filter(User.role == "admin").order_by(User.user_id).first()
            seeder = Seeder(db, random.Random(args.random_seed), now, password_hash, admin)
            seeder.run()
            db.commit()
        except BaseException:
            db.rollback()
            print("Seeding failed; the transaction was rolled back and the database is unchanged.")
            raise
    finally:
        db.close()

    accounts_path = Path(args.accounts_file).expanduser()
    write_accounts_file(accounts_path, password, seeder, now)
    student_count = len({id(p) for s in seeder.students_by_class.values() for p in s})
    print(f"Done: {len(seeder.people)} faculty, {student_count} students, {len(content.CLASSES)} classes, "
          f"{len(seeder.audit)} audit records, {len(seeder.notifications)} notifications.")
    print(f"Demo accounts and their password: {accounts_path}")
    if args.unattended:
        print(f"Demo password (local stack): {password}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
