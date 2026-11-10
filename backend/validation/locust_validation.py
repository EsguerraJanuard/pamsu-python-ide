"""
SOP 2.5: load test of the student IDE, one account per simulated student.

Why a new file: load_tests/locustfile.py signs every simulated user in to the
same account. POST /execution/requests/ allows 5 runs per 10 seconds per
account (limit_per_user("execution_request", limit=5, window_seconds=10) in
app/routers/execution.py), so with many users on one account most Run clicks
come back 429 "Too many requests". That measures the per-account limit, not
the server. Here every Locust user signs in to its own account.

How accounts are provisioned: POST /guest would create a verified student,
but it allows only 2 new guests per minute per IP address (limit_per_ip) and
100 per day (GUEST_DAILY_LIMIT), so it cannot give 50 load-test users one
account each. Instead, `--seed N` adds N load-test students to the LOCAL QA
database (qa/.qa-data/qa.db, see qa/QA_TESTING_GUIDE.md), enrolls them in the
Guest Sandbox Classroom with its published demo activity (created with the
production helpers in guest_service.py), and writes their sign-ins to
validation/output/loadtest_accounts.csv (git-ignored; random passwords that
only work on that local copy). Each Locust user takes one account from the
file; no two users ever share one. If you start more users than there are
accounts, the extra users stop and say so. To use other accounts, point
PAMSU_LOADTEST_ACCOUNTS at any CSV with `email,password` columns. No
credentials are written in this file.

Each simulated student, like load_tests/locustfile.py (same think time and
task weights):
  - on start: POST /login with its own account, then opens the dashboard
    (GET /classrooms/mine, GET /activities/) and picks its first activity;
  - 3x  GET /classrooms/mine                 (dashboard)
  - 1x  GET /activities/{id}                 (open the activity)
  - 2x  POST /execution/requests/ (Run), then polls
        GET /execution/requests/{id} on the same schedule as the IDE
        (frontend/src/utils/polling.js, up to 30 s). The whole Run, click to
        result, is also reported as "RUN  Run until result": success only if
        the run ends "completed" (the test program is valid and fast).
        This task is tagged "run" (see step 3).

RUN IT (PowerShell, from the backend folder)
--------------------------------------------
1. Local QA database, once (prints the QA logins):
       venv\\Scripts\\python.exe ..\\qa\\qa_setup.py
2. Load-test accounts (re-run any time; it resets their passwords):
       venv\\Scripts\\python.exe validation\\locust_validation.py --seed 50
3. A local backend on http://127.0.0.1:8010, in its own terminal. Either
   a) with Runs (recommended). First the mock Judge0 from this repository,
      in another terminal (it runs the test program on this computer):
          venv\\Scripts\\python.exe -m uvicorn main:app --app-dir ..\\mock_judge0 --host 127.0.0.1 --port 8001
      then the QA backend, sending Runs to it:
          venv\\Scripts\\python.exe validation\\locust_validation.py --serve
      There is no Redis locally, so --serve runs the Celery worker's own
      dispatch task (dispatch_to_partner) in a thread of the API process
      instead of queueing it; the mock Judge0 then calls back as Judge0 does.
   b) or the plain QA backend, without Runs:
          venv\\Scripts\\python.exe ..\\qa\\run_backend.py
      It has no Redis, Celery or Judge0, and each Run request waits about
      60 s for the missing queue before failing, so add --exclude-tags run
      to the Locust command in step 5.
4. Locust, once. It only adds packages to backend\\venv (nothing there is
   upgraded; any other venv works too, Locust needs none of the backend):
       venv\\Scripts\\python.exe -m pip install -r ..\\load_tests\\requirements.txt
5. Run 50 students for 3 minutes, 5 new users per second, results to CSV:
       venv\\Scripts\\locust.exe -f validation\\locust_validation.py --headless -u 50 -r 5 -t 3m --csv validation\\output\\locust_sop25
   or with the web UI at http://localhost:8089:
       venv\\Scripts\\locust.exe -f validation\\locust_validation.py

Read the results: 429 responses on POST /execution/requests/ are marked as
failures with an explanation; with one account per user there should be
none. The numbers measure this computer (SQLite, one API process, the mock
Judge0), not Render, Supabase or the real Judge0.

Target: the default host is the local QA backend. Only localhost,
127.0.0.1, ::1, *.localhost and *.test are accepted; anything else stops
the test before a single request is sent. Never load-test the production
site. To test an owner-approved staging copy, set
$env:PAMSU_LOADTEST_ALLOW_HOST = "<that hostname>" and pass --host.

Run Locust as one process (no --processes or distributed workers): each
process would read the same accounts file and users would share accounts.
"""

from __future__ import annotations

import argparse
import csv
import os
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

VALIDATION_DIR = Path(__file__).resolve().parent
BACKEND_DIR = VALIDATION_DIR.parent
REPO_DIR = BACKEND_DIR.parent
DEFAULT_ACCOUNTS_FILE = VALIDATION_DIR / "output" / "loadtest_accounts.csv"
ACCOUNTS_FILE = Path(os.getenv("PAMSU_LOADTEST_ACCOUNTS") or DEFAULT_ACCOUNTS_FILE)

LOCAL_QA_HOST = "http://127.0.0.1:8010"  # qa/run_backend.py and --serve
QA_BACKEND_PORT = 8010
MOCK_JUDGE0_PORT = 8001
ALLOW_HOST_ENV = "PAMSU_LOADTEST_ALLOW_HOST"
LOCAL_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}

EMAIL_TEMPLATE = "loadtest.student{:04d}@pampangastateu.edu.ph"
SCHOOL_ID_TEMPLATE = "LT{:08d}"  # school_id is at most 10 characters
MAX_SEED = 1000

# Same as frontend/src/features/workspace/Workspace.jsx.
POLL_MAX_WAIT_SECONDS = 30.0
TERMINAL_STATES = {
    "completed", "syntax_error", "runtime_error", "timed_out", "memory_limit",
    "output_limit", "process_limit", "cancelled", "failed",
}

# The Run program from load_tests/locustfile.py: valid, prints one line.
RUN_SOURCE = """
def find_primes(limit):
    primes = []
    for num in range(2, limit + 1):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
    return primes

print(f"Found {len(find_primes(10000))} primes up to 10,000!")
"""


def poll_delay(waited_seconds: float) -> float:
    """frontend/src/utils/polling.js: often at first, then every 1.5 s."""
    if waited_seconds < 3:
        return 0.5
    if waited_seconds < 6:
        return 0.75
    return 1.5


def host_allowed(host: str | None) -> bool:
    hostname = (urlparse(host or "").hostname or "").lower()
    if not hostname:
        return False
    if hostname in LOCAL_HOSTNAMES or hostname.endswith((".localhost", ".test")):
        return True
    approved = os.getenv(ALLOW_HOST_ENV, "").strip().lower()
    return bool(approved) and hostname == approved


def load_accounts(path: Path) -> list[tuple[str, str]]:
    """(email, password) pairs from a CSV with email and password columns."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    accounts = [
        ((row.get("email") or "").strip(), row.get("password") or "")
        for row in rows
    ]
    return [(email, password) for email, password in accounts if email and password]


# ---------------------------------------------------------------------------
# --seed: load-test students in the local QA database (runs in backend\venv)
# ---------------------------------------------------------------------------


def seed_accounts(count: int, accounts_file: Path) -> int:
    sys.path.insert(0, str(REPO_DIR / "qa"))
    import qa_env

    if not qa_env.DB_PATH.exists():
        print("No local QA database yet. Create it first:")
        print("  venv\\Scripts\\python.exe ..\\qa\\qa_setup.py")
        return 1

    # Local SQLite file, backend/.env not read, email/Redis/Judge0/AI blanked.
    qa_env.apply()

    from app.core.database import SessionLocal, engine

    # Never seed any database but the local QA file.
    database = engine.url.database or ""
    if engine.url.get_backend_name() != "sqlite" or Path(database).resolve() != qa_env.DB_PATH.resolve():
        print(f"Refusing to seed: the app is not using {qa_env.DB_PATH}.")
        return 1

    from app.core.security import get_password_hash
    from app.models.domain_models import Enrollment, User
    from app.services.guest_service import (ensure_sandbox_demo_activity,
                                            get_or_create_sandbox_classroom)

    db = SessionLocal()
    accounts: list[tuple[str, str]] = []
    try:
        sandbox = get_or_create_sandbox_classroom(db)
        if sandbox is None:
            print("The QA database has no active admin to own the sandbox classroom. Run qa_setup.py --reset.")
            return 1
        activity = ensure_sandbox_demo_activity(db, sandbox)

        now = datetime.now(timezone.utc)
        for number in range(1, count + 1):
            email = EMAIL_TEMPLATE.format(number)
            password = secrets.token_urlsafe(12)
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                user = User(
                    email=email,
                    name=f"Load Test Student {number}",
                    school_id=SCHOOL_ID_TEMPLATE.format(number),
                    role="student",
                )
                db.add(user)
            else:
                # A new password: tokens from an earlier seed stop working.
                user.password_version = (user.password_version or 1) + 1
            user.password_hash = get_password_hash(password)
            user.email_verified = True
            user.is_active = True
            db.flush()

            enrollment = (
                db.query(Enrollment)
                .filter(Enrollment.class_id == sandbox.class_id, Enrollment.student_id == user.user_id)
                .first()
            )
            if enrollment is None:
                db.add(Enrollment(class_id=sandbox.class_id, student_id=user.user_id, status="active", joined_at=now))
            else:
                enrollment.status = "active"
            accounts.append((email, password))
        db.commit()
        activity_id = activity.task_id
    finally:
        db.close()

    accounts_file.parent.mkdir(parents=True, exist_ok=True)
    with accounts_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["email", "password"])
        writer.writerows(accounts)

    print(f"{count} load-test students ready in {qa_env.DB_PATH}")
    print(f"Enrolled in the Guest Sandbox Classroom; activity id {activity_id}.")
    print(f"Sign-ins saved to {accounts_file} (local QA only, git-ignored).")
    return 0


def serve_backend(port: int, judge0_port: int) -> int:
    """The local QA backend, with Run requests sent to mock_judge0."""
    sys.path.insert(0, str(REPO_DIR / "qa"))
    import qa_env

    if not qa_env.DB_PATH.exists():
        print("No local QA database yet. Create it first:")
        print("  venv\\Scripts\\python.exe ..\\qa\\qa_setup.py")
        return 1

    qa_env.apply()
    os.environ["JUDGE0_API_URL"] = f"http://127.0.0.1:{judge0_port}"
    os.environ["WEBHOOK_BASE_URL"] = f"http://127.0.0.1:{port}"

    import threading

    import uvicorn
    from app.tasks import celery_worker

    dispatch = celery_worker.dispatch_to_partner
    # No Redis broker here: run the worker's own task in a thread instead of
    # queueing it (in production a Celery worker runs this same function).
    dispatch.delay = lambda *args: threading.Thread(target=dispatch.run, args=args, daemon=True).start()

    from app.main import app

    print(f"QA backend with mock Judge0 runs on http://127.0.0.1:{port} (Ctrl+C to stop).")
    print(f"Expects the mock Judge0 on http://127.0.0.1:{judge0_port}.")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "SOP 2.5 load test. Run it with Locust (see the top of this file). "
            "Run directly, this script seeds load-test accounts or serves the local QA backend."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--seed", type=int, metavar="N",
                      help=f"create or reset N load-test students in the local QA database (1-{MAX_SEED})")
    mode.add_argument("--serve", action="store_true",
                      help="start the local QA backend with Run requests sent to mock_judge0")
    parser.add_argument("--port", type=int, default=QA_BACKEND_PORT, help="--serve: backend port (default 8010)")
    parser.add_argument("--judge0-port", type=int, default=MOCK_JUDGE0_PORT,
                        help="--serve: port of the mock Judge0 (default 8001)")
    args = parser.parse_args(argv)
    if args.serve:
        return serve_backend(args.port, args.judge0_port)
    if not 1 <= args.seed <= MAX_SEED:
        parser.error(f"--seed must be between 1 and {MAX_SEED}")
    return seed_accounts(args.seed, ACCOUNTS_FILE)


# ---------------------------------------------------------------------------
# Locust users. --seed runs in backend\venv, which may not have Locust, so the
# Locust part is defined only when Locust is installed.
# ---------------------------------------------------------------------------

try:
    import gevent
    from locust import HttpUser, between, events, tag, task
    from locust.exception import StopUser
except ImportError:
    HttpUser = None


if HttpUser is not None:
    _free_accounts: list[tuple[str, str]] | None = None
    _warned: set[str] = set()

    def _warn_once(key: str, message: str) -> None:
        if key not in _warned:
            _warned.add(key)
            print(f"[locust_validation] {message}", file=sys.stderr)

    def _take_account() -> tuple[str, str] | None:
        # gevent switches only on I/O, so this check-and-pop cannot interleave.
        global _free_accounts
        if _free_accounts is None:
            _free_accounts = load_accounts(ACCOUNTS_FILE) if ACCOUNTS_FILE.exists() else []
        return _free_accounts.pop(0) if _free_accounts else None

    def _return_account(account: tuple[str, str]) -> None:
        if _free_accounts is not None:
            _free_accounts.append(account)

    class RunWithoutResult(Exception):
        pass

    @events.test_start.add_listener
    def _check_setup(environment, **_kwargs) -> None:
        host = environment.host or StudentUser.host
        problem = None
        if not host_allowed(host):
            problem = (
                f"Refusing to load-test {host!r}: only a local backend (default {LOCAL_QA_HOST}) "
                f"or the host named in {ALLOW_HOST_ENV} is allowed. Never the production site."
            )
        elif not ACCOUNTS_FILE.exists() or not load_accounts(ACCOUNTS_FILE):
            problem = (
                f"No accounts in {ACCOUNTS_FILE}. Seed them first: "
                "venv\\Scripts\\python.exe validation\\locust_validation.py --seed 50"
            )
        if problem:
            _warn_once("setup", problem)
            environment.process_exit_code = 2
            runner = environment.runner
            if runner is not None:
                # From a new greenlet: quitting inside test_start would stop
                # the listener itself.
                gevent.spawn(runner.quit)
            return

        users = getattr(environment.parsed_options, "num_users", None)
        accounts = len(load_accounts(ACCOUNTS_FILE))
        if users and users > accounts:
            _warn_once("few", f"{users} users but only {accounts} accounts: {users - accounts} users will stop. "
                              f"Seed more with --seed {users}.")

    class StudentUser(HttpUser):
        host = LOCAL_QA_HOST
        # Think time between student actions, as in load_tests/locustfile.py.
        wait_time = between(1, 5)

        account: tuple[str, str] | None = None
        signed_in = False
        task_id: int | None = None

        def on_start(self) -> None:
            # A user that cannot sign in stops at its first task
            # (_stop_unless_signed_in): Locust 2.24 prints a traceback for
            # StopUser raised here.
            if not host_allowed(self.host):
                return

            self.account = _take_account()
            if self.account is None:
                _warn_once("none", "A user found no free account and stopped (more users than accounts).")
                return

            token = self._log_in()
            if not token:
                _return_account(self.account)
                self.account = None
                return
            self.signed_in = True
            self.client.headers["Authorization"] = f"Bearer {token}"

            # The dashboard a student lands on after signing in.
            self.client.get("/classrooms/mine", name="/classrooms/mine")
            with self.client.get("/activities/", name="/activities/", catch_response=True) as response:
                if response.status_code == 200:
                    activities = response.json()
                    if activities:
                        self.task_id = activities[0]["task_id"]
                    else:
                        _warn_once("no_activity", "An account has no activity, so it skips Run. Re-run --seed.")

        def on_stop(self) -> None:
            if self.account is not None:
                _return_account(self.account)
                self.account = None

        def _log_in(self) -> str | None:
            email, password = self.account
            for attempt in range(3):
                with self.client.post(
                    "/login",
                    data={"username": email, "password": password},
                    name="POST /login",
                    catch_response=True,
                ) as response:
                    if response.status_code == 200:
                        return response.json().get("access_token")
                    if response.status_code in (401, 403):
                        response.failure(f"{response.status_code}: account cannot sign in here; re-run --seed")
                        return None
                    response.failure(f"{response.status_code}: {response.text[:200]}")
                gevent.sleep(2 * (attempt + 1))
            return None

        def _stop_unless_signed_in(self) -> None:
            if not self.signed_in:
                raise StopUser()

        @task(3)
        def open_dashboard(self) -> None:
            self._stop_unless_signed_in()
            self.client.get("/classrooms/mine", name="/classrooms/mine")

        @task(1)
        def open_activity(self) -> None:
            self._stop_unless_signed_in()
            if self.task_id is not None:
                self.client.get(f"/activities/{self.task_id}", name="/activities/{id}")

        @tag("run")
        @task(2)
        def run_code(self) -> None:
            self._stop_unless_signed_in()
            if self.task_id is None:
                return

            started = time.perf_counter()
            payload = {
                "request_kind": "run",
                "task_id": self.task_id,
                "source_code": RUN_SOURCE,
                "standard_input": "",
            }
            with self.client.post(
                "/execution/requests/",
                json=payload,
                name="POST /execution/requests/",
                catch_response=True,
            ) as response:
                if response.status_code == 429:
                    response.failure("429: per-account Run limit (5 per 10 s); should not happen with one account per user")
                    return
                if response.status_code != 201:
                    response.failure(f"{response.status_code}: {response.text[:200]}")
                    return
                execution_id = response.json()["execution_id"]

            # Poll like the IDE until the run reaches a final state.
            status = None
            waited = 0.0
            while waited < POLL_MAX_WAIT_SECONDS:
                pause = poll_delay(waited)
                gevent.sleep(pause)
                waited += pause
                with self.client.get(
                    f"/execution/requests/{execution_id}",
                    name="GET /execution/requests/{id}",
                    catch_response=True,
                ) as poll:
                    if poll.status_code != 200:
                        poll.failure(f"{poll.status_code}: {poll.text[:200]}")
                        break
                    status = poll.json().get("status")
                if status in TERMINAL_STATES:
                    break

            if status == "completed":
                problem = None
            elif status in TERMINAL_STATES:
                problem = RunWithoutResult(f"run ended {status!r}")
            else:
                problem = RunWithoutResult(f"no result within {POLL_MAX_WAIT_SECONDS:g} s (last status {status!r})")
            self.environment.events.request.fire(
                request_type="RUN",
                name="Run until result",
                response_time=(time.perf_counter() - started) * 1000,
                response_length=0,
                exception=problem,
                context={},
            )


if __name__ == "__main__":
    sys.exit(main())
