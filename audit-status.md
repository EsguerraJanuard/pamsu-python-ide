# PAMS(U) IDE — Frontend Audit Status

_Last updated: 2026-10-16 · Branch: `dev` · Base commit: `b5f111f`_

## Overall progress

**Frontend: nearly production-ready.** The repository-wide frontend audit and hardening pass is complete. What remains is mostly backend work (see "Backend blockers").

- `npm run lint`: PASS (0 problems)
- `npm run build`: PASS. Pages are now loaded per route, which shrank the main bundle from 757 kB to 294 kB and removed the >500 kB warning.
- `git diff --check`: PASS
- Tested in the browser against the local backend with the seeded student, instructor and admin accounts, at desktop width and 375 px.

### Root cause of "Failed to load data"
The backend wasn't running. Once it was started, every student endpoint returned 200. The frontend turned every failure into one generic message, or into a misleading empty state. Pages now tell these apart:
- loading
- empty (no records)
- server unreachable
- timeout
- session expired (401 → back to sign-in with a notice)
- forbidden (403)
- not found (404)
- server error (5xx)

### Key fixes (P0: actions that silently did nothing)
- **Grading bench:** the workspace never found a submission, and grades never saved (it looked up `id` where the data has `student_id`). It also showed a grade suggestion calculated in the browser and a false "Perfect Structure" when no AST data existed. Rebuilt; it saves grades through `PUT` and shows real AST findings, indicators and submitted code.
- **Activity details:** adding a test case always failed with 422 (wrong field names). Delete called `/test-cases/undefined`. The paste toggle sent a field that doesn't exist.
- **Login:** admin accounts were sent to Access Denied. Guest sign-in called a path that doesn't exist (`/auth/guest`).
- **Notifications:** always empty (items were cleared right after loading). Wrong field names. "Mark as read" claimed success even when it failed.
- **Instructor settings:** password change used `POST`, which the backend rejects (405). Fields that were never saved (department, default course, alert toggles) have been removed.
- **Student gradebook modal:** always showed "no records".
- **Class details:** showed a made-up classroom ("Dr. Maria Santos") whenever loading failed.
- **Submission details:** links used the activity id instead of the submission id; every page showed a false "AST FAILED".
- **Submissions:** released grades were fetched but never shown.
- **Class roster:** removing a student took them off the list even when the API call failed. The submissions column was hard-coded to 0.
- **Activity editor:** "Publish immediately" was ignored.
- **Admin dashboard:** the Faculty tab was misplaced and there was no mobile navigation. Fake zero stats were shown when the API failed. Search would crash on a field the API doesn't send.
- **Workspace:** a WebSocket that never worked, Fibonacci placeholder code, no submit confirmation, and misleading sandbox messages.
- **Behaviour tracking hook:** called a route that returns 404 every 5 seconds.

### Native browser UI
`alert()` went from 4 to 0, `confirm()` from 2 to 0, and forms without `noValidate` from 4 to 0. All validation is now shown by the app next to each field, linked for screen readers.

### Theme
- The app is light-only with PSU branding. Tailwind's `dark:` classes followed the computer's dark-mode setting rather than the in-app toggle, so pages were half dark for some users.
- The code editor keeps its own light/dark switch.
- Colours are defined once in `frontend/src/index.css`, together with shared button, card, input and badge styles.

## Files modified (tracked)
```
frontend/src/App.jsx
frontend/src/index.css
frontend/src/services/api.js
frontend/src/hooks/useBehaviorTracking.js
frontend/src/hooks/useEditorSettings.js
frontend/src/components/layout/InstructorSidebar.jsx
frontend/src/components/layout/Sidebar.jsx
frontend/src/components/layout/SignOutModal.jsx
frontend/src/components/layout/Statusbar.jsx
frontend/src/components/modals/AlertModal.jsx
frontend/src/components/modals/BulkEnrollModal.jsx
frontend/src/components/modals/ConfirmationModal.jsx
frontend/src/components/modals/CreateClassModal.jsx
frontend/src/components/modals/EditClassModal.jsx
frontend/src/components/modals/JoinClassModal.jsx
frontend/src/components/modals/StudentGradebookModal.jsx
frontend/src/components/ui/CustomSelect.jsx
frontend/src/features/admin/AdminDashboard.jsx
frontend/src/features/assignments/Assignments.jsx
frontend/src/features/auth/AuthContext.jsx
frontend/src/features/auth/ForgotPassword.jsx
frontend/src/features/auth/Login.jsx
frontend/src/features/auth/ProtectedRoute.jsx
frontend/src/features/auth/Register.jsx
frontend/src/features/auth/RoleRoute.jsx
frontend/src/features/classes/ClassDetails.jsx
frontend/src/features/classes/MyClasses.jsx
frontend/src/features/dashboard/Analytics.jsx
frontend/src/features/dashboard/ClassRosterView.jsx
frontend/src/features/dashboard/InstructorDashboard.jsx
frontend/src/features/dashboard/StudentDashboard.jsx
frontend/src/features/instructor/ActivityDetails.jsx
frontend/src/features/instructor/ActivityEditor.jsx
frontend/src/features/instructor/ClassManagement.jsx
frontend/src/features/instructor/LiveMonitoring.jsx
frontend/src/features/instructor/PracticeModuleManager.jsx
frontend/src/features/instructor/grading/GradingBenchRoot.jsx
frontend/src/features/instructor/grading/GradingClassView.jsx
frontend/src/features/instructor/grading/SplitPaneGradingWorkspace.jsx
frontend/src/features/practice/PracticeWorkspace.jsx
frontend/src/features/practice/SoloPractice.jsx
frontend/src/features/settings/EditorSettings.jsx
frontend/src/features/settings/InstructorSettings.jsx
frontend/src/features/settings/Settings.jsx
frontend/src/features/submissions/SubmissionDetails.jsx
frontend/src/features/submissions/Submissions.jsx
frontend/src/features/theme/ThemeContext.jsx
frontend/src/features/theme/ThemeToggle.jsx
frontend/src/features/workspace/Workspace.jsx
frontend/src/pages/AuditLogsPage.jsx
frontend/src/pages/NotFound.jsx
frontend/src/pages/NotificationsPage.jsx
frontend/src/pages/Unauthorized.jsx
```

## Files created
```
audit-status.md
frontend/src/components/ErrorBoundary.jsx
frontend/src/components/layout/AppSidebar.jsx
frontend/src/components/layout/PageShell.jsx
frontend/src/components/ui/Modal.jsx
frontend/src/components/ui/StateViews.jsx
frontend/src/features/settings/AccountSections.jsx
frontend/src/features/student/ActivityCard.jsx
frontend/src/features/student/studentData.js
frontend/src/features/submissions/submissionData.js
frontend/src/utils/format.js
```
`.claude/launch.json` (local dev-server config) was also created. It is **not** meant to be committed.

## Files deleted (unused; recoverable from git history)
```
frontend/src/App.css
frontend/src/assets/hero.png
frontend/src/assets/react.svg
frontend/src/assets/vite.svg
frontend/src/components/layout/InstructorLayout.jsx
frontend/src/components/layout/Navbar.jsx
```

## Pending tasks / next steps

### Backend blockers (not changed in this pass)
1. `backend/app/main.py` imports `admin` but never calls `app.include_router(admin.router)`, so every `/admin/*` endpoint returns 404. The admin dashboard shows "Administration service unavailable" until this is fixed.
2. `POST /guest` returns 500 with `ModuleNotFoundError: app.core.utils` (in `routers/auth.py`, `login_guest`).
3. `backend/app/routers/users.py` assigns `router` twice, so `PATCH /users/me/integrity` is never registered (404). The frontend no longer calls it.
4. There is no "allow retake" endpoint. The frontend retake buttons were removed rather than left broken.
5. The sign-in response doesn't include `ast_strictness_level`, so instructor settings can't show the saved level until the instructor saves one. A `GET /users/me` endpoint would fix this.
6. Locally, Redis isn't running. Every authenticated request takes 4–8 seconds, execution requests stay queued, and `POST /submissions/` blocks for more than 40 seconds even though the submission is recorded.

### Frontend follow-ups
- Test real code execution, structure checks and grading in a staging environment with Redis and the execution worker running.
- Fully rebuild `PracticeModuleManager.jsx` and `ActivityEditor.jsx` on `PageShell` and the shared form styles; so far they were only patched.
- Remove the unused dependencies `xlsx` and `react-intersection-observer` from `package.json`. Removing them will change `package-lock.json`.
- Decide whether to restore dark mode for the whole app. It is now light-only by design.
- Optional: a toast system for short success messages. Inline alerts are used today.

### Local test data created during QA (seeded QA accounts only)
- Submission #3 for activity 7 by `qa.student`, graded 92 (not released) by `qa.instructor`.
- Two queued "run" execution requests for activity 7.

---

## Backend Remediation Results

_Date: 2026-10-17 · Branch: `dev` · HEAD: `1f2acc5` (the frontend audit above used base `b5f111f`) · Nothing committed or pushed._

### Summary
| # | Finding | Status |
|---|---------|--------|
| A | Admin router not registered | **Confirmed → fixed and verified** (plus a role defect that would still have blocked admins) |
| B | `POST /guest` 500 (`app.core.utils`) | **Confirmed → fixed and verified on a schema-consistent DB.** Still returns 500 on the **local PostgreSQL DB** because that database's schema has drifted (see "Remaining blockers") |
| C | `users.py` assigns `router` twice | **Confirmed → dead code removed.** The endpoint is deliberately **not** restored |
| D | Sign-in response missing `ast_strictness_level` | **Confirmed → fixed and verified** (no new endpoint) |
| E | Redis down: slow requests, stuck queue, 40 s+ submissions | **Confirmed: code defects plus missing local Redis.** Code defects fixed and verified with Redis down; behaviour with a real Redis and worker is **not verified here** |
| F | No retake endpoint | **Deferred: needs a product decision** |

Counts: 6 confirmed · 5 fixed (A, B, C, D, E-code) · 0 already resolved · 1 deferred (F). E's infrastructure part (running Redis and the worker) is still open.

### Repository-state note (read first)
`backend/app/routers/auth.py` had **uncommitted** changes (not in HEAD) that matched the output of old helper scripts from 2026-10-08 (`fix_guest.py`, `fix_auth_maintenance.py`, …). They are what introduced finding B. They also undid several committed security fixes:
- removed the IP and per-email login rate limits;
- stopped recording failed sign-ins in the audit log;
- read maintenance mode from an in-memory dict that resets on restart, instead of the database setting;
- could save a fallback name, "PamSU User", onto a real account;
- enrolled guests in the first **real** classroom.

The file was therefore rebuilt from HEAD and only the needed fixes were applied on top. **The uncommitted version is preserved, not discarded:**
- `git stash list` → `stash@{0}: preserved: uncommitted backend/app/routers/auth.py before backend remediation 2026-10-17`. It was created with `git stash create` + `git stash store`, which did not touch the working tree.
- `docs/remediation/auth.py.uncommitted-2026-10-16.diff` (the same diff as a file).

### A. Admin router registration
- **Reported:** `main.py` imports `admin` but never registers it, so every `/admin/*` endpoint returned 404.
- **Root cause (confirmed):** `app.include_router(admin.router)` was missing; pyflakes reported `admin` as an unused import. A second defect would still have blocked admins after registration. `get_current_user` (in `core/security.py`) only accepted the roles `student` and `instructor`. Both admin checks build on it: `get_current_admin = RequireRole(["admin"])` and `get_current_instructor = RequireRole(["instructor","admin"])`. So an admin token got 403 on every admin endpoint. Admin was never in that list (checked across history), even though login, `UserResponse` and the admin-role migration all treat admin as a valid role.
- **Change:** registered `admin.router` once in `main.py`, and added `"admin"` to the role list in `get_current_user`. Nothing else in authorization changed. The routes that use `get_current_user` directly were reviewed: they either only return the caller's own records (notifications, audit records, `/users/me`) or explicitly reject any role other than student or instructor (execution, evaluation). No admin can read another user's data through them.
- **Files:** `backend/app/main.py`, `backend/app/core/security.py`
- **Tests (runtime, real app + SQLite):**
  - The route table has 115 API routes and no duplicates; all 12 `/admin/*` routes appear exactly once.
  - As admin: `GET /admin/stats`, `/admin/users`, `/admin/settings` and `/admin/audit-logs` return 200. `POST /admin/instructors` returns 200, or 422 for a bad body. `PATCH /admin/settings` returns 200 and the setting is persisted.
  - As student or instructor: 403. With no token or an invalid token: 401. An admin on a student-only route gets 403.
  - The same checks against **local PostgreSQL**, inside a transaction that was rolled back, also pass.
- **Limitations:** admins can also use instructor-only routes, because `get_current_instructor` was already written to include them; the instructor routes only show records owned by the caller, so an admin sees their own (empty) data. Please review the one-line role change; it is the only change to the authorization rules.

### B. Guest authentication
- **Reported:** `POST /guest` 500, `ModuleNotFoundError: app.core.utils`.
- **Root cause (confirmed):** `app.core.utils` has never existed in git history. The import came from the uncommitted script-generated `auth.py` described above. HEAD's version imports correctly, but it was broken in two other ways:
  - It did not set `email_verified`, which defaults to `False`. `get_current_user` therefore rejected every guest request with 403, so the guest token was useless.
  - Every guest account got the same, guessable password, `"guest"`.
- **Change (on top of HEAD):**
  - Guests are created with `email_verified=True`. Guests have no university mailbox, and admin-created guests (`POST /admin/guests`) already work this way.
  - Each guest gets a random password that is never shown, so guest accounts can't be opened through `/login`.
  - The existing student maintenance-mode rule now applies to `/guest` too, using the database setting.
  - Kept from HEAD: the 2-per-minute IP rate limit, the dedicated `SANDBOX01` classroom (real classrooms are untouched), and the `pwd_ver` value in the token.
  - Removed: the `app.core.utils` import, the "first real classroom" enrollment, and every other regression listed in the repository-state note.
- **Files:** `backend/app/routers/auth.py`
- **Tests (runtime, SQLite):**
  - `POST /guest` returns 200. The guest has role `student`, `email_verified` is true, and the response includes `ast_strictness_level`.
  - The guest token gets 200 on an authenticated route and 403 on admin and instructor routes. `/login` with `"guest"` as the password returns 401.
  - The guest is enrolled only in `SANDBOX01`.
  - During maintenance, `/guest` and student login return 503; instructor login still returns 200.
  - Login returns 200 for student, instructor and admin; 401 for a wrong password or a non-university email; 422 for a missing password. Logout returns 204.
- **Tests (local PostgreSQL, rolled back):** **`POST /guest` returns 500 with `NotNullViolation: null value in column "first_name"`.** This is caused by the database itself, not the code; see "Remaining blockers".
- **Limitations:** a guest calling `PATCH /users/me` gets a 500 (confirmed, and it was already the case before this pass). `UserResponse` only accepts school IDs of the form `^(\d{10}|\d{4}-\d{5})$`, so the guest ID `GST1234567` fails. The name change is saved before the error. This was not changed: decide whether guests may edit their profile, or whether guest IDs belong in that format.

### C. Duplicate `router` in `users.py`
- **Reported:** `router` is assigned twice, so `PATCH /users/me/integrity` is never registered.
- **Root cause (confirmed):** the first `APIRouter()` and its endpoint were replaced by the second assignment before `main.py` ever registered them. The endpoint did nothing ("Panel Requirement: Telemetry no longer deducts points"). Nothing calls it: not the frontend, not the backend, not the tests or docs.
- **Decision:** it is not part of the supported API, so it was **not restored**. The unreachable code, its schema and an unused import were removed, so the router is now assigned only once. This changes no runtime behaviour, because the endpoint was never reachable.
- **Files:** `backend/app/routers/users.py`
- **Tests:** the route table no longer has an integrity route, and `PATCH /users/me/integrity` returns 404. `PATCH /users/me` still works.

### D. AST strictness / current-user profile
- **Reported:** the sign-in response lacks `ast_strictness_level`.
- **Root cause (confirmed):** `ast_strictness_level` is stored in `users.ast_strictness_level` (String(20), NOT NULL, default `moderate`). `UserResponse`, which `PATCH /users/me` returns, already included it. Only the sign-in response schema used by `/login` and `/guest` (`AuthenticatedUserResponse`) left it out. The frontend saves that response's `user` object as-is and reads `user.ast_strictness_level` from it.
- **Change:** added `ast_strictness_level: str` to `AuthenticatedUserResponse`. **No `GET /users/me` was added**, because the existing sign-in response already serves this purpose and nothing else was needed.
- **Files:** `backend/app/routers/auth.py`
- **Tests:** login for all three roles and `/guest` return the stored value. An instructor's `PATCH /users/me` to `strict` returns `strict`, and the next login also returns `strict` (persisted; checked on SQLite and local PostgreSQL). A student setting it gets 403; a missing `name` gets 422.
- **Limitations:**
  - Sessions signed in before this change keep the old stored user object until the next sign-in.
  - The backend accepts any value up to 20 characters. The frontend offers `lax`, `moderate` and `strict`, but the evaluator only treats `"strict"` specially. Allowed values were not added, because that would be a new business rule.

### E. Redis, execution queue and submission latency
**What was measured, before the fix (Redis down on this Windows machine):**
- Connecting to a closed localhost port takes about 2.0 s per address. `localhost` resolves to both `::1` and `127.0.0.1`, so one `redis_client.get()` took **4.1 s**.
- Every authenticated request pays that once for the token-blacklist check. Rate-limited routes pay it again, which explains the reported 4–8 s.
- `celery_worker.py` defaulted to the Docker hostname `redis://redis:6379/0`, while the other Redis clients default to `localhost`.
- One `evaluate_submission_background_task.delay()` blocked for **70.6 s** and then raised `RuntimeError` (Celery's result store retries 20 times). In `POST /submissions/` that call came **after the commit and outside any try**, which is why the submission was saved but the request hung and then failed.
- The execution-request service called `dispatch_to_partner.delay()` the same way after committing. The request then stayed `queued` forever with nothing to process it.
- The `fastapi-limiter` startup used a hardcoded `redis://redis:6379/0` and ignored `REDIS_URL`. On Render, the rate-limited routes would have targeted a host that doesn't exist.

**Root cause:** partly infrastructure (no Redis or Celery worker locally; Docker and WSL are not installed on this machine) and partly code: no connect timeouts, unprotected enqueue calls after commits, and three different Redis host defaults.

**Changes:**
- `core/redis_client.py`, `core/redis_async.py`: `socket_connect_timeout` (default 1.0 s, can be changed with `REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS`). Only the connect step has a limit; read timeouts are unchanged.
- `core/security.py`: the blacklist check treats a Redis `TimeoutError` like the existing `ConnectionError`. This **keeps** the existing behaviour (when Redis is unreachable, tokens are still accepted). The timeout only makes the "unreachable" case arrive as a `TimeoutError` instead of a very long wait.
- `main.py`: `FastAPILimiter` now uses the shared `REDIS_URL` client. **Rate limiting is not disabled.** The rate-limited routes still refuse requests when Redis is down, as before.
- `tasks/celery_worker.py`:
  - The default `REDIS_URL` is now `localhost`, like the other clients. docker-compose and render.yaml always set it explicitly, so deployments are unaffected.
  - `task_ignore_result=True`: nothing reads task results anywhere.
  - Broker connect timeout of 2 s, and one retry when sending a task.
- `services/execution_service.py`: a new `_dispatch_execution_request` helper. If the job can't be queued, the request is marked `failed` with `stderr = "System Error: The execution queue is unavailable…"`. That is the same final state the worker already records when it can't reach Judge0, and `queued → failed` is an allowed transition.
- `routers/submissions.py`: the background-evaluation enqueue is wrapped in try/except with logging, the same pattern the execution enqueue below it already used. The saved submission now returns 201 instead of 500. An instructor can still run the evaluation with `POST /evaluation/submissions/{sub_id}`.
- Unchanged: the sandbox, Judge0 limits, the execution provider, and the fail-open/fail-closed behaviour of each Redis call.

**Tests (runtime, Redis really down, real app + SQLite):**
- An authenticated GET takes **2.0 s** (was ≥4.1 s).
- `POST /execution/requests/` returns 201 in **6.8 s** with `status: failed` and the system-error message (before: about 70 s, then a 500, with the request left `queued`).
- `POST /submissions/` returns 201 in **10.2 s**, and the submission is persisted (before: 40–70 s, then a 500).
- No execution request is left `queued`.

**Not verified:** a full run → worker → Judge0 → callback cycle. That needs Redis, a Celery worker and Judge0 (or `mock_judge0`), and none of them can run on this machine. Everything above was checked with Redis **down**; behaviour with Redis **up** has only been reviewed in code.

**Required local setup:**
- Run Redis (`docker compose up redis`, or Memurai/WSL on Windows) and set `REDIS_URL=redis://127.0.0.1:6379/0` in `backend/.env`. Using `127.0.0.1` avoids the second `::1` attempt.
- Run the worker: `celery -A app.tasks.celery_worker worker --pool=solo --loglevel=info`. Use `--pool=solo` on Windows.
- Set `JUDGE0_API_URL` (or run `mock_judge0`), and set `WEBHOOK_BASE_URL` to an address the worker and Judge0 can call back.

### F. Retake workflow
- **Reported:** there is no "allow retake" endpoint.
- **Findings:**
  - A retake workflow existed once (`95a46c8`, `26d5ea3`, `79eeee8`). It blocked **every** resubmission unless an instructor approved one, and it was reverted in `aa3ee02`.
  - The current `Submission` model has no retake fields. Migration `9ff2d118b666` still adds `retake_requested` and `retake_allowed` columns, and they exist in the local database, but no code reads them.
  - The current rule allows unlimited attempts before the deadline (or after it, when `allow_late_submissions` is on). The newest attempt becomes official and older attempts are kept.
- **Decision:** **deferred, nothing implemented.** Any retake endpoint would need a policy that doesn't exist yet. Decisions needed:
  1. Is resubmission limited (single attempt, or a maximum number)? Today it is unlimited, so a "retake" means nothing until a limit exists.
  2. Does a retake reopen an activity after the deadline, and for how long?
  3. Does a retake discard, keep or replace the released grade? What happens to grades already released?
  4. Who can grant one (owning instructor only, or also admin), and is the student's request part of the flow?
  5. Where is the decision recorded? The audit log is available.

  After that, the model can map the existing columns (no new migration), or a dedicated table can be designed.

### Test suite comparison
The full backend suite (`pytest`, 739 tests, in-memory SQLite) was run on a **frozen copy of the tree before the changes** and on the tree after them. Redis was unavailable in both runs. `REDIS_URL=redis://0.0.0.0:6379/0` was used so that connection attempts fail instantly; failure behaviour is the same as with Redis down, it only saves time.

| Run | Passed | Failed | Time |
|-----|--------|--------|------|
| Before changes | 682 | 57 | 17 min 34 s |
| After changes | **699** | **40** | 4 min 2 s |

- **New failures: 0.** **Fixed: 17.** These were execution-request idempotency (7), submission workflow (6), execution workflow (3), and `test_phase3_business_logic::test_guest_login_enrolls_into_sandbox`.
- **40 tests fail before and after the changes, for reasons unrelated to this pass:**
  - **6 need a running Redis:** the `fastapi-limiter` routes refuse requests without it (`test_evaluation_workflow` ×5, `test_api_workflow` ×1).
  - **6 need a running broker:**
    - Five `test_execution_workflow` tests expect `queued` and later worker updates. With no broker the request is now `failed` (E); before the changes these requests returned 500.
    - `test_coding_session_workflow::test_execution_requests_increment_backend_session_counter` expects 3 and gets 4. The cause is code that was already in HEAD: `POST /submissions/` automatically creates its own `submit` execution request, which contradicts the endpoint's docstring. Before the changes the test failed earlier, on the 500.
  - **15 partner-auth / readiness tests** (`test_partner_auth` ×4, `test_partner_execution_router` ×9, `test_system_health` ×2) get 401 or 200 where they expect specific results. This is about how the tests set up the environment and settings, not about this pass.
  - **2 still use the old `first_name`/`last_name` fields** (`test_review_queue_workflow`, `test_schemas::test_valid_user_registration_input`). They were left as they are on purpose, to keep the unified `name` field.
  - **8 expect older field lists** (`test_session_privacy_contracts` ×5, `test_openapi_contracts` ×2, `test_task_openapi_contracts` ×1).
  - **`test_openapi_contracts::test_public_and_protected_route_boundaries`:** its list of public routes is out of date (it doesn't include `/guest` or the password-reset routes). A check confirmed that the **same 13 operations need no authentication before and after** the changes. All 11 newly registered admin paths require authentication.
  - `test_schemas::test_partner_result_completed_status_rejects_nonzero_exit_code` and `test_alembic_migrations` (the tables created by the migrations differ from the models).

**Other checks:**
- **Runtime script** with the real app and SQLite, Redis really down: **50/50 pass.** It covers every result listed under A–E above.
- **Local PostgreSQL**, inside one transaction rolled back at the end: **14/15 pass.** The one failure is `/guest`, with a 500 caused by the schema drift. Row counts for users, classrooms, enrollments and audit records were unchanged afterwards.
- **Route table:** 115 routes, no duplicates.
- **`pyflakes app/`:** 10 warnings before, 9 after. The one that disappeared is "`admin` imported but unused".
- **`git diff --check`:** clean.
- **Not run:** a live server with a real Redis, Celery worker and Judge0. They aren't available on this machine.

### Remaining blockers
1. **Local PostgreSQL schema drift (needs a migration; not done here).** The local database is at Alembic head `7a1b8c2d3e4f`, but `users` still has `first_name` and `last_name` as **required** columns, plus `middle_name`. `name` is optional there, although every existing row has a value. None of the current migrations create `first_name`, and `c5d2f62cc22e` is empty, so an earlier, since-reverted migration or script must have changed this database. Because of it, **new-user inserts fail** on this database. This was confirmed for `POST /guest` and `POST /admin/instructors` (both 500 `NotNullViolation`, in a transaction that was rolled back). The other code paths that create users (`/admin/students`, `/admin/guests`, bulk registration) build `User(name=…)` the same way and are expected to fail too, but were not run. Required fix, after checking the production schema: a migration that makes `first_name`/`last_name`/`middle_name` optional or drops them, and makes `name` required, keeping the unified `name` field. Risks: dropping columns loses the old split names, and the production database may or may not have the same drift. **Check production `users` columns before deploying.**
2. **Redis, Celery worker and Judge0 are not running locally.** End-to-end execution, background evaluation and the live behaviour of the rate limiters and token blacklist are still unverified.
3. **Pre-existing behaviour when Redis is down, kept as-is and listed for a decision:**
   - The token blacklist accepts tokens (so revoked tokens still work while Redis is down).
   - `POST /evaluation/submissions/{id}` and practice submissions refuse requests (500).
   - Practice AI hints return 500.
4. `ws_execution.router` is imported but not registered (the frontend no longer uses the WebSocket).
5. Guest `PATCH /users/me` returns 500 (see B).
6. **For security review (already the case before this pass):**
   - `PUT /execution/internal/judge0-callback` and `POST /execution/lint` need no authentication.
   - The callback only checks the `execution_id` and `correlation_id` given in the URL.
7. **Needs a product decision (already the case before this pass):** `POST /submissions/` automatically creates a `submit` execution request, although its docstring says it does not run code. This also counts toward the coding-session run total (see the coding-session test above).

### Frontend integration implications (for a separate pass; nothing changed in `frontend/`)
- `/login` and `/guest` responses now include `user.ast_strictness_level`. `InstructorSettings.jsx` works without changes once the user signs in again. Its comment saying the sign-in payload lacks the field is now out of date.
- The admin dashboard can now reach `/admin/*` with an admin token.
- `/guest` can now return **503** (maintenance mode) and **429** (more than 2 per minute per IP; HEAD's limit, which the uncommitted file had removed).
- `POST /execution/requests/` can return 201 with **`status: "failed"`** right away and a `stderr` message when the queue is down. The UI should show it instead of polling.
- `PATCH /users/me/integrity` does not exist. Retake controls should stay hidden until F is decided.

### Production-readiness assessment
**Blocked by infrastructure and product decisions.** The code fixes for A–E are ready for **staging validation**. Before production:
- check and fix the `users` schema drift (blocker 1);
- validate execution and evaluation with Redis, the worker and Judge0 actually running (blocker 2);
- make the retake decisions (F).

Passing imports and unit tests alone do not make this production-ready.

---

## Session wrap-up (2026-10-17)

### Overall progress
- **Frontend:** nearly production-ready (unchanged in this session; see the frontend audit at the top).
- **Backend:** the six blockers from the frontend audit are resolved in code, except retakes (F), which wait on a product decision. Verified with Redis down: 50/50 runtime checks pass, and the full suite went from 682 to **699 passing**, with no new failures.
- **Still blocking production:**
  1. The local database's `users` table has drifted from the code, so new users can't be created there (including guests).
  2. Code execution has not been tested with Redis, the Celery worker and Judge0 running.
  3. The retake policy is undecided.

### Files modified (tracked)
```
audit-status.md
backend/app/core/redis_async.py
backend/app/core/redis_client.py
backend/app/core/security.py
backend/app/main.py
backend/app/routers/auth.py
backend/app/routers/submissions.py
backend/app/routers/users.py
backend/app/services/execution_service.py
backend/app/tasks/celery_worker.py
```

### Files created
```
docs/remediation/auth.py.uncommitted-2026-10-16.diff
```
This is a copy of the uncommitted `auth.py` changes that were replaced. It is **untracked** and is not staged by `git add -u`. The same changes are also kept in git as `stash@{0}`. Delete both once you've confirmed that version is no longer needed.

### Pending tasks / next steps
1. **Users schema drift (highest priority).** A separate session ("Draft migration for users first_name/last_name drift") is drafting a migration for review; it does not apply it. Next:
   - Check the production `users` columns with a read-only query.
   - Review the draft, then apply it to the local database.
   - Run `POST /guest` and `POST /admin/instructors` again on PostgreSQL.
2. **Run the full execution stack locally or in staging:**
   - Redis, with `REDIS_URL=redis://127.0.0.1:6379/0`.
   - The worker: `celery -A app.tasks.celery_worker worker --pool=solo`.
   - Judge0 or `mock_judge0`, with `JUDGE0_API_URL` and `WEBHOOK_BASE_URL` set.

   Then test a full run and check cycle, a submission followed by background evaluation, the rate limiters, and logout with the token blacklist.
3. **Retake policy (F):** answer the five questions in section F, then implement against the existing `retake_*` columns.
4. **Review the one authorization change:** `admin` is now accepted by `get_current_user`.
5. **Smaller backend items that predate this session:**
   - A guest editing their profile (`PATCH /users/me`) gets a 500: guest IDs (`GST…`) don't match the school-ID format the response requires.
   - `PUT /execution/internal/judge0-callback` and `POST /execution/lint` need no authentication; they need a security review.
   - `POST /submissions/` automatically creates its own `submit` execution request; decide whether it should.
   - `ast_strictness_level` accepts any text; decide the allowed values.
   - `ws_execution` is imported but not registered.
6. **Out-of-date tests:** update the 40 tests that fail for reasons unrelated to this work (the old `first_name`/`last_name` fields, older field lists, the public-route list, partner-auth setup). Also make the tests replace Celery `.delay()` with a stub, so the suite doesn't need a broker.
7. **Frontend follow-ups:**
   - Handle an execution request that comes back `failed` immediately.
   - Handle 503 and 429 from `/guest`.
   - Remove the out-of-date comment about the strictness field in `InstructorSettings.jsx`.
   - Keep retake controls hidden.
8. **Housekeeping:**
   - Rotate the SMTP key; its value appeared in session output.
   - Clean up the ad-hoc `fix_*.py` / `check_*.py` scripts in the repository root. These kinds of scripts produced the uncommitted `auth.py` regressions.
