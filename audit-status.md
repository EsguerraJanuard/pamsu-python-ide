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
- Student dark mode was restored in Phase 1 (see "Student Theme Restoration — Phase 1"). Instructor dark mode was restored in Phase 2 (see "Instructor Theme Restoration — Phase 2"). Admin dark mode is NOT restored and remains light-only.
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

---

## Users-table migration: verification and local apply (2026-10-17)

_Branch: `dev` · Migration commits `7901146` + `5ae15c4` (already pushed) · Local database only; staging and production were not touched._

### Overall progress
- **Blocker 1 (users schema drift) is resolved on the local database.** Migration `c25114413200` (`backend/alembic/versions/c25114413200_reconcile_users_unified_name.py`) was verified and then applied to the local `pamsu_ide_db`. The risk note is `docs/remediation/users-name-schema-drift.md`.
- **Integration check:**
  - The branch was rebased onto `190837b`, the backend remediation commit.
  - There is a single Alembic head, `c25114413200`.
  - Offline mode (`--sql`) now stops with a clear error. Migrations up to `7a1b8c2d3e4f` still generate offline SQL (778 lines).
  - The real Alembic command was run against throwaway PostgreSQL 18 databases: 124/126 checks passed, and the 2 misses were false alarms in the test harness. Covered starting states: a clean database, the exact local drift, names longer than 150 characters, the "no `name` column" state, rollback cases, and blank names. App checks for guest, admin provisioning, registration and login also passed.
- **Backup:** `C:\Users\ACER\Downloads\pamsu_ide_db_backup_2026-10-17.backup` (114,450 bytes, custom format, sha256 `c5ad87dc…2528`).
  - `pg_restore --list` works.
  - **A restore test was actually performed** into a throwaway cluster. It completed with no errors, and all 27 tables' row counts and the user fingerprints matched the live database. Role ownership and grants were not tested (`--no-owner --no-privileges`).
- **Local apply:** `pamsu_ide_db` on `localhost:5432` went from `7a1b8c2d3e4f` to **`c25114413200`**.
  - It was rehearsed first on the restored copy.
  - The live run made the five expected changes: `first_name` and `last_name` became optional; `name` needed filling on 0 rows; `name` changed from `varchar(255)` to `varchar(150)`; `name` became NOT NULL.
- **After the migration:**
  - All 21 users are present, with no NULL or blank names and nothing truncated.
  - Every user's name and identity/login fields are byte-identical to before, including password hashes and versions.
  - The legacy name columns are kept and are now optional.
  - All 27 tables have the same row counts (88 rows).
- **App checks on the live database (13/13):** run inside a transaction that was rolled back, with email sending disabled. They covered reading users through the ORM, creating users through the ORM (previously `NotNullViolation`), login, `/guest`, admin creation of instructors and students, profile rename, and a wrong password getting 401. **No test rows remain.** Some ID sequences advanced, because PostgreSQL doesn't roll sequences back.
- **Tests:** 9 migration and authentication suites ran: 131 passed, and 4 failed. All four were already known (the alembic test's table list, the old `first_name` test, the partner-result schema test, and an evaluation test that needs Redis).
- **Cleanup:** the leftover empty test database `pamsu_ide_alembic_pytest_72e89d699c9b`, left by an earlier run of the alembic test, was dropped with approval. `pamsu_ide_db` was checked again afterwards and is unchanged.

### Files modified or created in this phase
```
audit-status.md                                                    (modified: this section)
backend/alembic/versions/c25114413200_reconcile_users_unified_name.py  (created; committed in 7901146/5ae15c4)
docs/remediation/users-name-schema-drift.md                        (created; committed in 7901146/5ae15c4)
```
No application code was changed. The test scripts, logs and throwaway clusters lived only in the session's temporary folder, and the clusters have been deleted.

### Pending tasks / next steps
1. **Before staging or production:**
   - Run the read-only check in `docs/remediation/users-name-schema-drift.md` against each database.
   - `origin/main` still contains the old split-name version of `c5d2f62cc22e`. A database built from `main` probably has **no `name` column**, which the migration supports.
   - Back up, apply on staging first, then confirm `POST /guest` and `POST /admin/instructors` work.
2. **Decisions:**
   - Drop the legacy `first_name`/`middle_name`/`last_name` columns? That needs a separate, reviewed migration plus a backup.
   - Remove the tracked `backend/write_migration.py` and `backend/update_model.py`? Running either again would recreate the drift.
   - How does `main` get the emptied `c5d2f62cc22e`?
3. **Full backend audit, in priority order:**
   - **P0, security:**
     - Bulk-registered students all get the same hardcoded password, `PamsU@2026`, which is also emailed (`admin.py` lines 275/281). Instructor provisioning emails the plaintext password.
     - `PUT /execution/internal/judge0-callback` needs no login and trusts identifiers in the URL. 15 partner-auth tests get 401.
     - Revoked tokens are still accepted while Redis is down. Maintenance mode only blocks new logins, not existing tokens.
     - CORS accepts any `*.vercel.app` origin with credentials. Redis TLS skips certificate checks.
   - **P1, integrity:**
     - The alembic test's expected tables differ from the real ones (`system_settings`, `practice_test_cases`). The `retake_*` columns exist but aren't used.
     - Admins pass the instructor checks. A guest editing their profile gets a 500.
     - `POST /submissions/` creates an execution request automatically. The strictness setting accepts any text.
     - Code execution has not been tested end to end with Redis, a Celery worker and Judge0 running.
   - **P2, contracts and coverage:**
     - The OpenAPI and contract tests are out of date. The `ws_execution` router is not registered.
     - Check what the audit log covers.
     - Fix or retire the 40 known test failures, stub out Celery and Redis in tests, add PostgreSQL integration tests for user creation, and make the alembic test always clean up after itself.
4. Items 2–8 of the previous wrap-up's pending list remain open (Redis/worker/Judge0 run, retake policy, admin-role review, smaller backend items, test cleanup, frontend follow-ups, rotating the SMTP key, removing ad-hoc scripts).

---

## MIS account creation and pending enrollment (2026-10-17)

_Branch: `dev` · Base commit: `bb242b8` · Nothing committed or pushed. No schema change, no migration, and no real database was touched._

### Overall progress
- **Pending class enrollments are now completed when MIS creates the student account.** An instructor can bulk-enroll an address that has no account yet. When MIS creates a student account with the same university email, the student is enrolled in that class in the same transaction.
- **Root cause:** `pending_enrollments` rows were only used by `verify_registration_otp`, which is part of the retired self-registration flow. The MIS endpoints (`POST /admin/students` and `POST /admin/students/bulk-register/file`) never read them, so with registration disabled, pending enrollments were never completed. The old OTP code also enrolled students in archived classes, enrolled instructors from the allowlist as students, and wrote no audit record.
- **Other defects found and fixed in the same workflow:**
  - A non-owner or a missing class got an unhandled exception (500) from both bulk-enroll routes. Now they get 403 and 404.
  - Archived classes accepted bulk enrollment. Now they return 409, the same rule as joining by class code.
  - Existing accounts were looked up case-sensitively, unlike login, so a mixed-case account was queued as pending instead of enrolled.
  - Faculty and admin addresses were queued as pending and stayed there forever. They are now reported as "not a student account".
  - "Already enrolled" was counted nowhere.
  - A failure partway through rolled nothing back explicitly.
- **No schema change was needed.** The `pending_enrollments` table (`2cd5c3a3ee9a`) already exists. The single Alembic head is still `c25114413200`.

### Verified behaviour
| Situation | Behaviour now |
|---|---|
| Bulk enroll, the account already exists | Enrolled straight away and audited. Any stale pending row for that class is removed. A record that already exists (including `removed` or `disabled`) is left as the instructor set it and counted as `already_enrolled`. |
| Bulk enroll, no account yet | One pending row per class and email, deduplicated. Counted as `queued`. |
| Bulk enroll, faculty or admin address | Not enrolled and not queued. Counted as `ineligible`. |
| Bulk enroll into an archived class | 409. Nothing is stored. |
| MIS creates the account | `apply_pending_enrollments` runs inside the account's transaction. Each class has its own savepoint. Each enrollment is audited as `student_enrolled` with MIS as the actor and `source: pending_enrollment`. The response includes `pending_enrollments: {enrolled_class_ids, already_enrolled_class_ids, skipped[]}`. |
| One class can't be completed (archived, audit failure, or a concurrent conflict) | Only that class's savepoint is rolled back, and its row stays pending with a reason. The account and the other enrollments are still committed. |
| Processed again | Idempotent. A completed row is consumed in the same savepoint that creates the enrollment, and `uq_enrollment_class_student` is a second guard. On PostgreSQL the pending rows are locked with `FOR UPDATE`. |
| Retry | New admin-only `POST /admin/students/{user_id}/pending-enrollments/apply`. It covers students that MIS created before this fix, and classes that were reactivated later. A non-student or deactivated account gets 409; an unknown user gets 404. |

Matching uses **only the exact university email**, compared case-insensitively as at login. A pending row stores nothing else; names are never used. The test suite proves that a different email with the same name does not match.

### Files modified (tracked)
```
backend/app/routers/admin.py                 (MIS create/bulk-register apply pending enrollments; new retry endpoint; StudentCreateResponse)
backend/app/routers/classrooms.py            (bulk-enroll routes map service errors to 403/404/409/503)
backend/app/schemas/enrollment_schema.py     (BulkEnrollmentResponse.already_enrolled/ineligible; PendingEnrollmentResult)
backend/app/services/classroom_service.py    (bulk_enroll_students hardened; new apply_pending_enrollments)
backend/app/services/otp_service.py          (retired OTP path reuses apply_pending_enrollments; students only)
frontend/src/components/modals/BulkEnrollModal.jsx  (accurate pending/MIS copy; already-enrolled and not-a-student counts)
frontend/src/features/admin/AdminDashboard.jsx      (shows classes joined / still pending after account creation and bulk registration)
audit-status.md                              (this section)
```

### Files created
```
backend/tests/test_pending_enrollment_workflow.py   (16 regression tests; untracked until explicitly added)
```

### Test evidence
- **New suite `test_pending_enrollment_workflow.py`: 16/16 pass.** It covers:
  - existing students, with mixed-case email;
  - pending enrollment, then MIS creation through a single account and through bulk registration;
  - a non-matching email with the same name;
  - retry and duplicate processing, at both the API and the service level;
  - several pending classes for one student;
  - archived classes;
  - authorization: another instructor's class, an unknown class, a student caller, no token, the file route, and the admin-only endpoints;
  - a non-student or deactivated account on the retry endpoint;
  - one class failing while the account and the other classes commit, then the retry;
  - a failed bulk enroll rolling back completely;
  - preservation of `removed` enrollments, submissions and the student's identity.
- **Related suites** (classroom workflow, classroom release candidate, classroom OpenAPI, OTP registration and service, OpenAPI contracts, schemas, audit, alembic): **153 passed, 6 failed.** The same 6 fail on a clean `git archive HEAD` copy, so they are not caused by this work. They are `test_openapi_contracts` ×3, `test_schemas` ×2 and `test_alembic_migrations` (the known model/migration table drift).
- **Full backend suite (755 tests, in-memory SQLite, Redis down): 715 passed, 40 failed (25 min 20 s).** The previous baseline was 699 passed / 40 failed out of 739; adding the 16 new tests gives exactly 715 / 40. The 40 failures are the same known set, file by file: Redis ×6, broker ×6, partner-auth/health ×15, old name fields ×2, older field lists ×8, the public-route list, the partner-result schema and the alembic table drift. **New failures: 0.**
- `npm run lint`: PASS. `npm run build`: PASS. `git diff --check`: clean.
- **End-to-end in the browser:**
  - Setup: the real frontend and backend, against a throwaway SQLite database in the session's temporary folder, with throwaway accounts.
  - As an instructor, a bulk enroll showed 1 enrolled, 1 pending, 0 invalid and 1 not a student account, with the new copy and the PSU theme intact.
  - As MIS, creating the pending student showed "Added to 1 class that had queued this email."
  - The database afterwards had the enrollment `active`, no pending row left, and an audit row with the MIS actor and `source: pending_enrollment`.
  - The temporary `.claude/launch.json` entry used for this was removed again.

### Pending tasks / next steps
1. **Product decisions (documented; not invented in code):**
   - **Inactive (suspended) students in bulk enroll:** they are still enrolled directly, as before this change. The retry endpoint refuses them. Should bulk enroll refuse them too?
   - **Pending rows for archived classes:** they are kept, so they can be applied after reactivation. Should archiving a class discard its pending rows, or should they expire?
   - **Class capacity:** there is no capacity field in the data model, so none is enforced. Is a seat limit needed? That would need a migration.
   - **Guests (`POST /admin/guests`)** don't complete pending enrollments, because guests aren't MIS-provisioned students. Confirm this.
   - **Visibility:** instructors can't list their class's pending addresses, and nothing notifies them when a pending student is enrolled. Is either needed?
   - **School ID matching:** bulk enroll only collects emails. Matching on school ID as well would need a pending-row column (a migration) and an instructor input.
2. **Pre-existing issues found while tracing (not changed):**
   - Bulk registration (`/admin/students/bulk-register/file`) gives every student a **random, made-up `school_id`** and the hardcoded password `PamsU@2026`. A random ID collision fails the whole batch with a 500.
   - `POST /admin/students` checks for an existing email case-sensitively and doesn't lowercase the email it stores.
   - `Classroom.section` and `subject_code` can be null in the model, but `ClassroomResponse` requires `section`. A classroom created outside the API makes `GET /classrooms/mine` return 500.
   - `DELETE /admin/users/{id}` on a student with enrollments hits a `RESTRICT` foreign key.
3. **Frontend:** there's no admin UI for the retry endpoint yet. Add a "Re-apply pending enrollments" action on the student row if MIS needs it.
4. **Deploy note:** students that MIS created before this change may have pending rows that were never applied. After deploying, call the retry endpoint for them. You can find them with a read-only query that joins `pending_enrollments.email` to `lower(users.email)` where `role = 'student'`.

---

## Bulk registration security fix and migration test diagnosis (2026-10-17)

_Branch: `dev` · Base commit: `9d5b732` (pending-enrollment work, already pushed) · Nothing committed or pushed. No real database was altered; the only real-database access was one read-only check of the local schema._

### Summary
| # | Finding | Status |
|---|---------|--------|
| P0 | Bulk registration made up school IDs and names, and gave every account the shared password `PamsU@2026`, which was emailed in plaintext | **Fixed and verified** (tests, PostgreSQL, browser) |
| P1 | `test_alembic_migrations` failed | **Diagnosed.** Two causes fixed (a stale test list and ORM drift). A third, a defect in the downgrade of an applied revision, **needs your approval** to fix; the test still fails at that step |
| — | Five enrollment product decisions | **Recorded as PROPOSED — AWAITING APPROVAL.** None implemented |
| — | Test runs could send real email | **Fixed** (SMTP blocked in all tests). See the incident note |

### P0. Bulk registration (`POST /admin/students/bulk-register/file`)
**Root cause:** the endpoint pulled only an email address out of each line of the file. Then:
- the **name** was made up from the email (`"Juan Delacruz Student"`);
- the **school ID** was `random.randint(1000000000, 9999999999)`, so it was not the student's real ID and a collision failed the whole batch with a 500;
- every account got the **same password**, `PamsU@2026`, which was emailed in plaintext;
- existing accounts were skipped silently and never counted;
- `.xlsx` and `.xls` uploads, which the UI allowed, crashed with `UnicodeDecodeError` (500).

**Fix:** the logic moved into the new `backend/app/services/student_provisioning_service.py`. The router now only calls it.
- **Input:** a CSV or `.xlsx` file with a header row containing `email`, `school_id` and either `name` or `first_name` + `last_name` (`middle_name` is optional). Headers are not case-sensitive. A file without these columns, an empty file, an old `.xls` file, a file that isn't UTF-8 or a file with more than 500 rows is rejected as a whole with a 400. Nothing is created in that case. The 500-row ceiling is the same as instructor bulk enrollment.
- **Each row is checked with the existing `UserBase` rules**: a university email, a school ID of 10 digits or `####-#####`, and a name of at most 150 characters. A failing row is reported with its spreadsheet row number and the reason. **Nothing is derived or generated.** Excel numeric IDs that lost a leading zero are rejected, with a hint to format the column as text.
- **Duplicates and conflicts:**
  - The same email or school ID on several rows of the file: every copy fails, because there is no way to tell which row is correct.
  - The same email and school ID as an existing account: the row is **skipped**, and the account is not changed.
  - An email that already exists with a different school ID, or the reverse: the row **fails**.
  - Emails are compared case-insensitively, as at login.
- **Transactions:** the existing all-or-nothing behaviour for database writes is kept, because it was safe. Valid rows are created in one transaction. Pending enrollments are still applied per class inside savepoints. If the database rejects the batch (for example, a concurrent import used the same school ID), everything is rolled back and the endpoint returns **409** "No accounts were created". A row is reported as `created` only after the commit succeeds. The response is `{created, skipped, failed, enrolled_from_pending, pending_left, rows: [{row, email, status, reason}]}`.
- **Credentials:** there is **no shared password and no emailed password.** Each account's password hash comes from its own random 32-byte secret, which is never stored, logged or returned, so nobody can sign in to the account. The student sets their own password through the **existing** password-reset OTP flow ("Forgot password?" calls `/users/password-reset/start|complete`, and the code goes only to the university mailbox). This adds no new authentication method. The provisioning email sent after the commit now says how to set a password and contains no credential. `send_provisioning_email` accepts `temp_password=None` for this; instructor provisioning is unchanged.
- **Unchanged:** password hashing (bcrypt), login, role checks (`get_current_admin`), `email_verified=True` for accounts MIS creates (same as `POST /admin/students`), and the pending-enrollment integration.
- **Admin UI** (`AdminDashboard.jsx`, bulk upload card only): it lists the required columns, accepts `.csv,.xlsx`, reports "N created, N already existed, N failed" with each failed row and its reason, and tells MIS that students set their own password with "Forgot password?".

### P1. Migration test (`test_alembic_upgrade_downgrade_and_reupgrade`)
Reproduced on disposable PostgreSQL. **Diagnosis, in the order the causes appear:**
1. **A stale expected table list in the test (fixed).**
   - The test expected `practice_test_cases`, which no model, migration or code defines. Commit `d5f6e21` removed it as a "model hallucination", and the revert `7748c49` ("restore main to exactly 65d1e05") brought it back.
   - The test was missing `system_settings`, which `7a1b8c2d3e4f` creates and the `SystemSetting` model uses.
   - The tables at head equal the ORM tables exactly (26, with nothing extra on either side). Only the test's list was wrong, so the list was corrected. The explicit-list assertion is kept, not weakened.
2. **ORM drift from applied migrations (fixed in the ORM; no migration).** With the table list corrected, `alembic check` (the column, default and constraint comparison) found exactly 3 differences:
   - `submissions.retake_requested` and `submissions.retake_allowed`: created by `9ff2d118b666` (BOOLEAN NOT NULL DEFAULT false), but not mapped in the model.
   - `users.academic_integrity_score`: the migration (`06d1a312becc`) sets a server default of `100.0`, but the model had only a Python default.
   - A **read-only** check of the local `pamsu_ide_db` (at revision `c25114413200`) confirmed that it has exactly these definitions. The migrations are what was really applied, so the **models were changed to declare them**. Dropping the columns would lose data and would also decide the open retake policy. The retake columns are mapped only; no workflow reads them.
   - Result: **0 differences**, and `alembic check` is clean.
3. **A downgrade defect in applied revision `2cd5c3a3ee9a` (NOT fixed; needs approval).** Its `downgrade()` runs `op.drop_constraint(None, 'practice_modules', type_='foreignkey')`. The upgrade created that foreign key without a name (PostgreSQL named it `practice_modules_instructor_id_fkey`), so Alembic cannot emit the DROP, and `downgrade base` fails at that revision. Upgrades are not affected.
   - **Evidence:** with only that one line changed, in a **scratch copy** of the migrations (the repository was not touched), the full test sequence passes on disposable PostgreSQL: upgrade, check, downgrade to base, re-upgrade, check. This is the only unnamed drop in the chain.
   - **Options:**
     - (a) Change only `downgrade()` of `2cd5c3a3ee9a` to drop `'practice_modules_instructor_id_fkey'`. The upgrade path, the revision ID and every applied schema stay the same, but it edits the file of an applied revision.
     - (b) Leave it, and accept that you can't downgrade below `2cd5c3a3ee9a`. The test then can't pass without being weakened, and that option is not acceptable.
   - **Recommendation:** (a), after you approve it. A forward-only migration can't fix this, because the defect is in the older revision's own downgrade.
   - **Also noted:** a downgrade below `7a1b8c2d3e4f` fails on a database that has `admin` users, because the older `ck_users_role` allows only student and instructor. This is expected for a role-removing downgrade, and the test downgrades an empty database.

**Other ORM checks on a fresh PostgreSQL database built from migrations (16/16 PASS):**
- tables equal the ORM;
- `users.name` is NOT NULL varchar(150), with no legacy split-name columns;
- bulk enroll creates a pending row;
- a masterlist import creates 1 row and fails 1 row, and completes the pending enrollment through a savepoint;
- the student is saved with the identity from the masterlist;
- re-importing the same file skips the row instead of duplicating it;
- `system_settings` can be read and written.

**Uncertainty:**
- The project targets **PostgreSQL 15** (`postgres:15-alpine` in docker-compose), but only PostgreSQL **18.4** is installed here, and there is no Docker. All checks ran on 18.4.
- The **staging and production schemas were not inspected.** Before deploying, compare their `submissions` retake columns and the `users.academic_integrity_score` default with the migrations, using a read-only query.
- A database named `pamsu_ide_alembic_test` exists on the local server. It wasn't created in this session and was left alone.

### Incident note: real email from test runs
`backend/.env` holds working SMTP credentials, and the test suite didn't stub email. The bulk-registration test added in the previous session (`test_mis_bulk_registration_completes_pending_enrollments`) therefore probably tried to send a real provisioning email each time it ran (about 3 runs). The email went to the made-up address `from.masterlist@pampangastateu.edu.ph` and contained the old shared password `PamsU@2026`. **Whether the relay accepted it can't be confirmed from the logs**; check the SMTP provider's sent log. Fix: `tests/conftest.py` now has an autouse fixture that blanks the SMTP configuration for every test. The verification server used in the browser also had SMTP blanked, and its log shows "Mock email" only. Together with the earlier note that the SMTP key appeared in session output, this is another reason to rotate the key.

### Files modified (tracked)
```
backend/app/routers/admin.py                       (bulk-register endpoint delegates to the provisioning service; removed shared password, random IDs, unused `re`)
backend/app/services/email_service.py              (send_provisioning_email accepts temp_password=None: credential-free setup notice)
backend/app/models/domain_models.py                (map submissions.retake_requested/retake_allowed; users.academic_integrity_score server_default — match applied migrations)
backend/tests/conftest.py                          (autouse fixture: never send real SMTP mail in tests)
backend/tests/test_alembic_migrations.py           (expected table list: drop practice_test_cases, add system_settings)
backend/tests/test_pending_enrollment_workflow.py  (bulk-registration test uses the new masterlist format)
frontend/src/features/admin/AdminDashboard.jsx     (bulk upload card only: required columns, row-level results)
audit-status.md                                    (this section)
```

### Files created
```
backend/app/services/student_provisioning_service.py   (masterlist parsing, validation, all-or-nothing creation)
backend/tests/test_masterlist_import.py                (23 tests)
```
No migration was added or edited. No other frontend component was changed. No database table was added or changed: the model changes only declare columns and a default that the applied migrations already create.

### Test results
| Test / check | Result |
|---|---|
| `test_masterlist_import.py` (23): student number and email kept separate and never inferred from each other; missing, invalid or blank school ID / name / email rejected with a row number; duplicates inside the file; existing accounts skipped or rejected, never overwritten; no shared or emailed password; the email has no credential; a password set through the reset OTP flow lets the student sign in; a database failure creates nothing and reports nothing as created; `.xlsx` support and leading-zero rejection; unreadable files; the row limit; admin-only access | **PASS** 23/23 |
| `test_pending_enrollment_workflow.py` (16) | **PASS** 16/16 |
| Disposable-PostgreSQL ORM and migration checks (scratch script) | **PASS** 16/16 |
| Downgrade proof with the one-line patch in a scratch copy | **PASS** (upgrade, check, downgrade base, re-upgrade, check) |
| `test_alembic_migrations.py` (repository as it is) | 2 PASS, 1 **FAIL**. Now fails only at the `2cd5c3a3ee9a` downgrade, which needs your approval (option a) |
| Full backend suite (777 tests, in-memory SQLite, Redis fast-fail `REDIS_URL=redis://0.0.0.0:6379/0`) | 737 **PASS**, 40 **FAIL** (4 min 45 s). The previous run had 715 + 22 new tests. The 40 failing test IDs are **identical** to the previous full run: 0 new failures. All 40 are known environment or stale-test failures (Redis ×6 **BLOCKED**, broker ×6 **BLOCKED**, partner-auth/health ×15, stale contracts and name fields ×11, partner-result schema ×1), plus the alembic downgrade above |
| `pyflakes app/` | 9 warnings, the same count as before; none in changed files. `tests/conftest.py` keeps its existing `noqa` import warning |
| `npm run lint` / `npm run build` | **PASS** / **PASS** |
| `git diff --check` | **PASS** |
| Browser (throwaway SQLite backend, SMTP blanked): masterlist upload as MIS | **PASS**: "1 account created, 1 already existed, 1 row failed" plus "Row 4 …: Missing school ID". The database had exactly one new student with the masterlist's school ID; the existing account was unchanged |

### Enrollment product decisions: PROPOSED — AWAITING APPROVAL
These are recommendations. **None was implemented in this session.**

| # | Decision | Proposed default | What the code does today | Change needed if approved |
|---|---|---|---|---|
| 1 | Suspended (inactive) students | Refuse enrollment and report the reason | Instructor bulk enroll **still enrolls** inactive students directly. The pending-enrollment retry endpoint refuses them (409) | Bulk enroll: count inactive students under a reported reason instead of enrolling them |
| 2 | Pending enrollments for archived classes | Keep the records for audit, but block fulfilment | **Already the case:** rows are kept and skipped as `classroom_inactive`, and bulk enroll into an archived class returns 409 | None (confirm only). Fulfilment resumes if the class is reactivated and the retry endpoint is called; confirm that this is intended |
| 3 | Class capacity | Defer until institutional requirements justify a schema change | No capacity field and no limit | None now. A migration would be needed later |
| 4 | Guest accounts created by an admin | Don't complete pending enrollments until the account has a verified regular-student identity | `POST /admin/guests` doesn't apply pending enrollments. **Gaps:** guests have role `student`, so the retry endpoint would apply pending rows to a guest whose email matches; and if an admin creates a guest with a university email, instructor bulk enroll would enroll it directly | Exclude guest accounts in `apply_pending_enrollments` and in bulk enroll. That needs a reliable guest marker (today only the `GST` school-ID prefix or the `guest_` email prefix) |
| 5 | Instructor access to pending email addresses | Keep raw addresses visible only to authorized MIS/admin staff; show instructors only the status they need | No endpoint lists pending addresses to anyone. Instructors see only the counts from their own submission | If approved: an admin-only pending list, plus a count-only status for instructors |

### Pending tasks / next steps
1. **`2cd5c3a3ee9a` downgrade: FIX B APPLIED (owner approved, 2026-10-17; not committed).** It was deferred earlier, then approved after the review in "Fix B: pre-approval review". The outcome is in "Fix B: applied and verified" at the end of this file. Until it's fixed, `test_alembic_upgrade_downgrade_and_reupgrade` keeps failing at the downgrade step, and `alembic downgrade` can't go below `2cd5c3a3ee9a`. Upgrades are not affected. The evidence for the approval decision is in "Downgrade of 2cd5c3a3ee9a: investigation" below.
2. **Approve the five product decisions above** (items 1 and 4 need code changes).
3. **Before deploying:**
   - Compare the staging and production `submissions` and `users` columns with the migrations, using a read-only query.
   - Validate against PostgreSQL 15.
   - Check the SMTP provider's sent log for the test emails described above, and rotate the SMTP key.
   - Tell MIS about the new masterlist format, and that students set their password with "Forgot password?".
4. **Outside this task, still open:**
   - Instructor provisioning (`POST /admin/instructors`) still makes up a random `school_id` and emails a plaintext temporary password.
   - `POST /admin/students` still has MIS choose a temporary password that is shown on screen.
   - `/users/password-reset/start` (service level) reports "No account found", although the router hides this from callers.
   - Items 2–4 of the previous section.

### Masterlist column mapping: confirmation (2026-10-17)
- `school_id` means the official student number the university issues, as listed in the MIS masterlist (example format: `2023304120`). `email` is the university address (for example `2023304120@pampangastateu.edu.ph`). **They are separate fields.** Each is read only from its own column (`email`, and `school_id` or `School ID`), validated separately, and stored exactly as given.
- **Nothing is inferred.** A missing school ID is not taken from a numeric email, and a missing email is not built from the student number. Both rows fail with a row-level reason. There are no random or generated IDs.
- **Duplicate student numbers:** every row that repeats a number in the file fails, and so does a number that already belongs to another account. The database's unique `users.school_id` constraint is the final guard: a concurrent import gets 409 and nothing is created.
- **Credentials:** no shared password. Students set their own password through the existing "Forgot password?" OTP flow on their university mailbox.
- New regression test: `test_student_number_and_email_are_separate_and_never_inferred`, using made-up student numbers. `test_masterlist_import.py` now passes 23/23.
- **Needs the real masterlist header (open):** the actual MIS file's column names haven't been seen. A file whose headers differ (for example "Student Number") is **rejected whole** with the list of required columns. It is never guessed or mapped by position. To add an alias such as `student_number` → `school_id`, share the header row only, with no student data.
- **Possible check (not implemented; needs approval):** require the email's local part to equal the student number when the local part is numeric. Only add this if MIS confirms that every student email follows `<student number>@pampangastateu.edu.ph`. Older or name-based addresses (for example `juan.delacruz@…`) would otherwise be rejected.

### Downgrade of 2cd5c3a3ee9a: investigation (2026-10-17, nothing modified)
- **Failing line:** `backend/alembic/versions/2cd5c3a3ee9a_add_pendingenrollment_and_practicemodule_instructor_id.py:45`, `op.drop_constraint(None, 'practice_modules', type_='foreignkey')`.
- **Root cause:**
  - The upgrade (line 38) creates the foreign key with `op.create_foreign_key(None, …)`. This is unedited autogenerate output.
  - No `naming_convention` is set on `Base.metadata`.
  - PostgreSQL therefore names the key itself (`practice_modules_instructor_id_fkey`).
  - Alembic can't emit `DROP CONSTRAINT` for a constraint whose name is `None`, and raises `CompileError` before any SQL runs. The rest of the downgrade (lines 46–47 and the `pending_enrollments` drops) is never reached.
- **History:**
  - **Committed and shared.** It was added by `65d1e05` ("Release Practice Modules, Bulk Enrollment, and AST Integrations (#29)", 2026-09-23, from a teammate's PR). It is on `origin/main` and `origin/dev`.
  - The file content has never changed since (`2e26d8e` emptied it and `1bf8b43` restored it byte for byte).
- **Applied:**
  - **Local:** yes. `pamsu_ide_db` is at `c25114413200`, which comes after this revision. The key there is `practice_modules_instructor_id_fkey` (checked read-only). The table has 6 rows, none with an instructor.
  - **Production:** very likely, but **not confirmed.** `render.yaml` starts the service with `bash start.sh`, and `start.sh` runs `alembic upgrade head` on every start. Any deploy of `main` since 2026-09-23 would therefore have applied it. Confirming needs a read-only `SELECT version_num FROM alembic_version` and a check of the key name on the production database.
  - **Staging:** none is defined in the repository.
- **Can't be fixed forward-only.** Alembic always runs this revision's own `downgrade()` when stepping below it, so a new revision can't replace that line. Any fix to the automated downgrade must edit this function. The alternative is a manual runbook: drop the key by hand, then `alembic stamp 9ee0a4c7ee5e`. That leaves the automated downgrade and the migration test broken.
- **Why changing only `downgrade()` is safe for history:**
  - Alembic stores only `version_num` in each database. It keeps no file checksums.
  - The revision ID, `down_revision` and `upgrade()` all stay the same, so no database's state or upgrade path changes.
  - Teammates' copies keep the old downgrade until they pull, which is harmless.
  - A real downgrade across this revision still destroys data (`practice_modules.instructor_id` and the `pending_enrollments` table) whichever fix is used. Take a backup first.
- **Candidates tested on disposable PostgreSQL 18.4** (`scratchpad/evaluate_downgrade_fixes.py`; each candidate used its own scratch copy, and the repository was not touched; every temporary database was dropped):

  | Check | A: hard-code `'practice_modules_instructor_id_fkey'` | B: look up the key name with `sa.inspect(op.get_bind())` | C: delete the line; `DROP COLUMN` drops the key |
  |---|---|---|---|
  | `upgrade()` AST-identical; all other revision files byte-identical | PASS | PASS | PASS |
  | Migration-test sequence (upgrade, check, downgrade base, re-upgrade, check) | PASS | PASS | PASS |
  | `2cd5c3a3ee9a → 9ee0a4c7ee5e` with rows present: column and key removed, rows kept, re-upgrade recreates the key | PASS | PASS | PASS |
  | Key has a non-default name (another DB's history) | **FAIL** (`UndefinedObject`) | PASS | PASS |

  The unchanged repository revision fails the downgrade with the reported `CompileError`.
- **Recommendation: B.** It is explicit about dropping the key and works whatever name a given database assigned. A depends on the name PostgreSQL happened to assign. C depends on an implicit PostgreSQL behaviour (DROP COLUMN cascading to constraints on that column) that a later reader could easily miss.
- **Limitation of B:** it can't run in offline `--sql` mode, because it needs a live connection. Offline downgrade from head is already refused by `c25114413200`, so this changes nothing in practice.
- **Proposed change for approval (B), replacing line 45 only:**
  ```python
  # The upgrade created this foreign key without a name; look up the
  # name the database assigned instead of assuming it.
  for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys('practice_modules'):
      if foreign_key['constrained_columns'] == ['instructor_id'] and foreign_key['name']:
          op.drop_constraint(foreign_key['name'], 'practice_modules', type_='foreignkey')
  ```
  After approval: apply it, run `pytest tests/test_alembic_migrations.py` on a disposable database, and also check against PostgreSQL 15 (the project's target; only 18.4 is available here).

### Fix B: pre-approval review (2026-10-17, nothing modified; still DEFERRED)
**Exact diff.** The repository file uses LF line endings, and the change must keep them.
```diff
@@ -42,7 +42,11 @@ def upgrade() -> None:
 def downgrade() -> None:
     """Downgrade schema."""
     # ### commands auto generated by Alembic - please adjust! ###
-    op.drop_constraint(None, 'practice_modules', type_='foreignkey')
+    # The upgrade created this foreign key without a name; look up the
+    # name the database assigned instead of assuming it.
+    for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys('practice_modules'):
+        if foreign_key['constrained_columns'] == ['instructor_id'] and foreign_key['name']:
+            op.drop_constraint(foreign_key['name'], 'practice_modules', type_='foreignkey')
     op.drop_index(op.f('ix_practice_modules_instructor_id'), table_name='practice_modules')
     op.drop_column('practice_modules', 'instructor_id')
```
`sa` is already imported. Nothing else changes: not `upgrade()`, the revision ID, `down_revision`, or any other file.

**Why B is safer than A and C:**
- **A (hard-coded name)** assumes every database got PostgreSQL's default name. It failed the test where the key has another name, with `UndefinedObject`, which aborts the downgrade partway. A database whose history differs (restored, hand-repaired, or created with `create_all` under a naming convention) would hit this.
- **C (delete the line)** works because PostgreSQL's `DROP COLUMN` removes constraints on that column. That's implicit: a reader sees an FK created in `upgrade()` and never dropped in `downgrade()`, and it depends on database-specific behaviour.
- **B** drops the key explicitly by its real name and matches only a key on `instructor_id`. If no such key exists, it skips the drop, and `DROP COLUMN` still succeeds. It passed every scenario, including the non-default name.

**Committed, pushed, applied (read-only checks; `git fetch --prune` only refreshed local remote-tracking refs):**
- **Committed and pushed:** yes. It was introduced by `65d1e05` (PR #29, by Errol, 2026-09-23). It's on `origin/main` and `origin/dev`, and the file is byte-identical on both (blob `c6c2a6e`). No tag contains it.
- **Local `pamsu_ide_db`:** applied. A read-only session shows `alembic_version` = `c25114413200` (the code head), and the key is `practice_modules_instructor_id_fkey`.
- **Production:** **very probably applied, not verified directly.** No production credentials are available here; `render.yaml` has `DATABASE_URL: sync: false`. The evidence:
  - `start.sh` runs `alembic upgrade head` on every start.
  - Teammate commit `968e574` (2026-10-13, "add bridge migration for 333fed79e9f7 to unblock production upgrade") shows that a production database recorded `333fed79e9f7`, which comes after the merge of `2cd5c3a3ee9a`.
  - The production URL was **deliberately not requested**. On Render's free plan a request can wake the service, and its `start.sh` would run `alembic upgrade head` against the production database.
- **Staging:** none is defined in the repository.
- **To verify production without changing it:** connect with a read-only role and run:
  ```sql
  SET default_transaction_read_only = on;
  SELECT version_num FROM alembic_version;
  SELECT conname FROM pg_constraint WHERE conrelid = 'practice_modules'::regclass AND contype = 'f';
  ```

**Disposable-PostgreSQL results for B (18.4; the repository was not touched; every temporary database was dropped). 8/8 PASS:**
- A database built **and populated** with the current repository migrations:
  - `upgrade head` with fix B is a no-op; the revision and the schema-plus-data fingerprint are unchanged;
  - `alembic check` is clean;
  - downgrade to base works, then the repository's own upgrade to head works, and `check` is clean again.
- Fresh upgrade to head with and without fix B: identical schema (tables, columns, types, defaults, key names). Fresh databases are compared ignoring timestamp columns, because seeded `system_settings.updated_at` uses `CURRENT_TIMESTAMP`. A table-by-table control diff showed no differences.
- Stepping across the revision with data present (`2cd5c3a3ee9a → 9ee0a4c7ee5e`) removes only what that revision added (`practice_modules.instructor_id`, its key and index, and `pending_enrollments`). Other rows are kept, and the repository upgrade back to head works.
- The earlier candidate run also passed for B: the migration-test sequence, and the non-default key name.

**Recommendation:** approve B, when you choose to. It changes only downgrade behaviour. The upgrade path and every applied database are untouched, and databases at head need no action.

**Remaining risks:**
1. **It edits a revision file that is already applied and shared.** Teammates' copies keep the old downgrade until they pull (harmless). There is precedent: `968e574` changed `9ff2d118b666`'s `upgrade()`, and `c5d2f62cc22e` was emptied. B is narrower than either, because it touches only `downgrade()`.
2. **Any real downgrade across this revision still destroys data**: `practice_modules.instructor_id` and every pending enrollment. B makes the downgrade possible; it doesn't make it harmless. Take a backup first.
3. **Downgrades below `7a1b8c2d3e4f` still fail on a database that has `admin` users**, because of the older two-role `ck_users_role`. B doesn't change this.
4. **Not run in offline `--sql` mode** (it needs a connection). Offline mode is already refused at head.
5. **Tested on PostgreSQL 18.4 only**; the target is 15. `get_foreign_keys` and `DROP CONSTRAINT` behave the same on 15, but this wasn't run.
6. **Production's real key name and revision aren't verified** (use the read-only SQL above). B doesn't depend on the name, which is why it's preferred.

**Separate deployment finding (outside fix B; needs attention):**
- `origin/main` is missing three migration files that `dev` has: `333fed79e9f7_bridge_migration.py`, `7a1b8c2d3e4f_phase3_business_logic_and_settings.py` and `c25114413200_reconcile_users_unified_name.py`.
- On `main`, `9ff2d118b666` names `333fed79e9f7` as its parent, but that file doesn't exist there. Alembic can't load the revision map (`KeyError: '333fed79e9f7'`).
- Because `start.sh` uses `set -e`, a production deploy of `main`'s current tip (`e271aa9`) would stop at `alembic upgrade head` before the API starts.
- The fix is to merge `dev`'s migrations into `main` (or deploy from a branch that has them) **after** the read-only production check above. Nothing was changed for this.

### Fix B: applied and verified (2026-10-17, not committed)
- **Change:** `backend/alembic/versions/2cd5c3a3ee9a_add_pendingenrollment_and_practicemodule_instructor_id.py`, `downgrade()` only. Line 45 was replaced by the 5-line foreign-key lookup shown in the pre-approval review (+5 / −1). The file is still LF-only. Its blob is `da0bc31`, the same as the scratch copy tested before approval.
- **Unchanged (verified):**
  - `upgrade()` is AST-identical to `HEAD`.
  - Module-level code is identical (revision `2cd5c3a3ee9a`, `down_revision` `9ee0a4c7ee5e`, imports).
  - `alembic heads` is still `c25114413200` alone.
  - No other file under `backend/alembic/` changed.
- **Tests on disposable PostgreSQL 18.4** (every temporary database was dropped):

  | Test | Result |
  |---|---|
  | `pytest tests/test_alembic_migrations.py` | **PASS 3/3**, including `test_alembic_upgrade_downgrade_and_reupgrade` (upgrade, check, downgrade base, re-upgrade, check). This test was failing before the change |
  | Fresh upgrade to head, repository vs a copy holding the original file | **PASS**: identical schema (tables, columns, types, defaults, key names) |
  | Downgrade scenarios (`verify_fix_b.py`) | **PASS 8/8**: on a database migrated with the original chain and holding data, `upgrade head` is a no-op; downgrade to base and re-upgrade work and `check` is clean; stepping `2cd5c3a3ee9a → 9ee0a4c7ee5e` with rows removes only what that revision added and keeps other rows |

- **Real databases:** none migrated. `pamsu_ide_db` was only read through a read-only session and is still at `c25114413200`. Production was not contacted.
- **Remaining risks:** unchanged from the pre-approval review, items 2–6:
  - a real downgrade across this revision still destroys `practice_modules.instructor_id` and all pending enrollments, so back up first;
  - downgrades below `7a1b8c2d3e4f` fail when admin users exist;
  - offline `--sql` downgrade isn't supported;
  - only PostgreSQL 18.4 was tested, not 15;
  - production's revision and key name are unverified.
- Teammates get the corrected downgrade when this commit is pulled. The `main` branch problem (missing migration files) is separate and still open.

---

## Full backend audit (2026-10-17)

_Branch: `dev` · Base commit: `0eb9c17` · Nothing committed or pushed. No real database, Redis, SMTP relay or Judge0 was contacted._

### Production blocker found first
`HEAD` (also pushed to `origin/dev`) **could not start**: `app/routers/admin.py` imports `app.services.student_provisioning_service`, which commit `c285f54` describes but never added. `test_masterlist_import.py` was missing too. Both were re-created from the behaviour recorded in that commit and the "Bulk registration security fix" section above.

### Fixed
| Pri | Finding | Fix |
|---|---|---|
| P0 | Backend fails to import (missing provisioning module) | Re-created `services/student_provisioning_service.py`; accounts get an unusable password marker (no bcrypt cost, no shared password) |
| P1 | `routers/ws_execution.py` ran student code with `exec` in a subprocess on the API host (unregistered, one line from live) | Deleted |
| P1 | `POST /execution/lint` unauthenticated, unbounded, CPU work on the event loop | Auth + per-user limit + size limit + threadpool |
| P1 | AST endpoints crashed (MemoryError/RecursionError) or ran 7.5 s on 100 kB inputs | `services/ast_safety.py` bounded parser used by every analyzer; input size limits |
| P1 | Password reset: unlimited new challenges (OTP brute force, email bombing); enumeration through response message/values; SMTP sent inside the request (Cloudflare drops >3 s); case-sensitive email match | Per-email and per-IP limits; a new request expires the old code; identical behaviour for unknown emails; delivery in a background task; SMTP timeouts |
| P1 | Rate limits keyed by IP (all users share the Render proxy IP) and `fastapi-limiter` routes returned 500 when Redis was down | `core/rate_limit.py`: per-user for authenticated routes, fail-open with a warning; `fastapi-limiter` removed |
| P1 | `seed.py` runs `TRUNCATE users CASCADE` (whole DB) and `entrypoint.sh` runs it on every container start | Refuses unless `PAMSU_ENVIRONMENT` is development/test and `PAMSU_ALLOW_DATABASE_RESET=true` (set only in docker-compose) |
| P1 | Students' existing tokens kept working during maintenance mode | `get_current_student` returns 503 during maintenance |
| P1 | Gradebook `.xlsx` turned student-entered names starting with `=` into formulas | Same sanitizer as the CSV export |
| P1 | Judge0 callback mapped missing/queued/malformed status to `completed` | Only status 3 is `completed`; everything unknown is `failed` |
| P2 | `create_task` silently dropped `difficulty` and `scheduled_publish_at`; scheduled publishing never happened | Fields saved; due schedules publish (with audit record) when students open activities; publishing clears the schedule |
| P2 | Admin create endpoints had no validation (any email/password), case-sensitive duplicate check, random-ID collision 500, delete → 500, unbounded `limit` | Validated schemas, lowercase emails, `GST`/`FAC` placeholder IDs, 409 on delete with records, bounded paging |
| P2 | `PATCH /users/me` returned 500 for guests (and new instructors) | Response schema no longer applies the input pattern |
| P2 | Instructor growth analytics always 403 (`status == "enrolled"`); review-queue CSV export always 500 | Fixed |
| P2 | Partner auth advertised env var `PARTNER_EXECUTION_TOKEN`; settings read `PAMSU_PARTNER_EXECUTION_TOKEN` | One name (`PAMSU_…`) |
| P2 | Tests read the developer's `.env` (real DATABASE_URL, SMTP) and waited on Redis/broker timeouts (20 min) | `conftest.py` forces SQLite/unreachable Redis, stubs Celery `.delay` |
| P2 | Student-visible error text leaked Judge0/AI exception strings; AI tutor fell back to models other than `gemini-3.8-flash` | Generic messages, server-side logging; single model |
| P3 | CORS regex trusted every `*.vercel.app` site | Only `pamsu-python-ide[-…].vercel.app` |
| P3 | bcrypt default 12 rounds (AGENTS.md caps at 8 for Render) | `BCRYPT_ROUNDS = 8`; old hashes still verify |
| P3 | `seed_admin.py` used non-existent fields and a hardcoded password | Takes identity and password from env vars |

### Tests
- Before: 716 passed, 39 failed, 5 errors (≈20 min). After: **811 passed, 5 skipped, 0 failed (≈70 s)**.
- New: `test_masterlist_import.py` (26), `test_backend_audit_regressions.py` (35).
- Updated stale tests to the current, intentional contracts (unified `name`, `mouseleave_*`, `difficulty`, public routes, auto-queued submit request, completed-with-non-zero-exit).
- Skipped: the 5 PostgreSQL-only suites (migrations, concurrency). Run them with `PAMSU_TEST_DATABASE_URL=postgresql://…` (they create and drop their own temporary database).

### Still open (not changed)
1. PostgreSQL migration chain and concurrency tests not run here (no PostgreSQL). Single head `c25114413200`; migrations do not run on SQLite.
2. Admin actions (deactivate, delete, password reset, settings) write no audit record: `audit_records.action_type` has a DB CHECK constraint, so this needs a migration.
3. Token revocation and rate limits fail open while Redis is down (documented choice).
4. Guest accounts: unlimited creation behind one shared proxy IP, never cleaned up, can join any class whose code they know, sandbox class is owned by whichever instructor row comes first.
5. `POST /practice/tasks/{id}/submit` waits on Judge0 synchronously (up to 15 s), against the AGENTS.md 3-second rule.
6. AI tutor: `google-generativeai` is not in `requirements.txt` and the frontend never calls `/practice/attempts/{id}/ai-hint` (no `attempt_id` returned).
7. Legacy `POST /execution/submissions/` creates submissions without the audit record/notification of `POST /submissions/`.
8. Admin `default_ast_strictness` setting is stored but never applied.
9. Retake workflow (columns only), enrollment product decisions above, instructor temp-password email.
10. `rediss://` connections use `ssl_cert_reqs=none`.

## Student Theme Restoration — Phase 1

Status: **implemented and verified in a browser against a mock API** (details under "Verification"). Live OS theme-change events and real-backend flows were not verified.

### What removed dark mode
Commit `1f2acc5` replaced `ThemeContext` with a constant light value (it also deleted the `pamsu_theme` key), stripped the `.dark` token block from `index.css`, and `index.html` hard-coded `#0f1117 !important` on html/body/#root. The editor kept a separate `light`/`vs-dark` toggle. No old files were restored from history.

### Architecture (single source of truth)
- `features/theme/ThemeContext.jsx` — `StudentThemeProvider`, mounted inside `AuthProvider` and `Router`. Dark is enabled only when `isAuthenticated && role === "student" && user_id != null && pathname starts with /student`. Otherwise the document is forced to light, regardless of stored values. It applies `class="light|dark"`, `data-theme` and `color-scheme` to `<html>`, so portals (modals) inherit the theme.
- `features/theme/themeStorage.js` — preference (`system|light|dark`), per-account key `pamsu_theme_pref_v1:<user_id>`; malformed values fall back to `system`; `system` removes the key. Stores only the preference string. No backend, no migration.
- System mode follows `prefers-color-scheme` live via `useSyncExternalStore` (listener removed on unmount). Other tabs of the same account sync through the `storage` event.
- `index.html` — small pre-paint script applies the theme for a student on `/student/*` to avoid a flash; the provider then re-applies or resets it. The hard-coded dark `!important` background was replaced by light defaults (`html.dark` gets the dark surface).
- `index.css` — Tailwind `@custom-variant dark` is class-based (it no longer follows the OS). Light tokens unchanged; new `:root.dark` token set; new tokens `--bg-selected`, `--bg-overlay`, `--text-placeholder`, `--shadow-card`, scrollbar and selection tokens. In dark, `--color-psu-maroon`, `-maroon-dark`, `-red` and `-gold-dark` are re-pointed so existing `bg-psu-*` fills keep working.
- Brand text moved to semantic tokens: `text-psu-maroon`→`text-text-brand`, `text-psu-red`→`text-text-rose`, `text-psu-gold-dark`→`text-text-amber`, `bg-psu-cream`→`bg-selected`, `bg-slate-900/4x`→`bg-overlay`. In light mode these resolve to identical values.

### Sidebar control
`ThemeToggle` (rewritten) sits in the profile area of the **student** sidebar only (`Sidebar.jsx` passes it through `AppSidebar`'s `renderThemeControl`; the instructor sidebar does not). Expanded: Light / Dark / System radio group plus a status line. Collapsed (and mobile): one button cycling System → Light → Dark with a descriptive accessible name. The practice workspace has no sidebar, so it shows the collapsed button in its toolbar (same preference).

### IDE
`features/workspace/editorThemes.js` defines Monaco themes `pamsu-light` / `pamsu-dark` (syntax, selection, caret, line numbers, find matches, widgets, scrollbars, minimap). Workspace and PracticeWorkspace pick the theme from the effective student theme; the separate editor theme toggle and the `pamsu_editor_theme` key are no longer used. Font size, tab size, word wrap and minimap settings are untouched. No execution, terminal or submission code changed.

### Contrast (computed from resolved colors, WCAG ratios)
Dark text on base/panel/alt/selected surfaces: main 13.1–16.2, muted 6.9–8.5, brand 8.5–10.5, emerald 8.7–10.8, amber 9.1–11.2, rose 6.7–8.2 (all ≥ 4.5). Placeholder 5.2–5.7 (dark). White on dark-mode maroon fill 5.24, on red 5.20. Dark input border vs panel 3.33, maroon fill vs panel 3.37, gold focus ring vs panel 8.87 (≥ 3). Editor syntax colors 5.6–10.4 on both editor backgrounds. Light placeholder raised from 3.36 to 5.69. The SoloPractice completed chip uses `emerald-700` (5.48 with white; `emerald-600` was 3.77). Known pre-existing light-mode miss: `text-emerald` on `bg-alt` is 4.36. Computed contrast (above) plus an in-browser audit of rendered text (below).

### Student surface covered
Dashboard, Assignments, My Classes, Class details, Solo Practice, Practice workspace, Workspace (IDE), Analytics, Submissions + details, Notifications, Audit history, Settings, sidebar/status bar, Modal, StateViews (alerts, empty/error/loading), CustomSelect, Join/Alert/Confirmation/Sign-out modals. Flatpickr styling is instructor-only (ActivityEditor) and was left light.

### Verification
Run on 2026-10-17 with the Vite dev server and a throwaway mock API (not committed); seeded student sessions with fake tokens.
- `npm run lint`: exit 0, no output. `npm run build`: passes. `git diff --check`: clean.
- Passed in the browser (OS emulated dark unless noted): new student with no preference → follows OS (dark); manual Light on a dark device → light and kept after reload; manual Dark on a light device → dark and kept after reload; "System" → applies current device theme and clears the stored key; second student account in the same browser did not inherit the first's preference; route changes keep the theme; sign out → login is light while a dark preference is still stored; instructor and admin routes stay light with OS dark and a stored dark preference for their ids, and show no theme control; student → `/unauthorized` via client navigation resets to light; expired student token on `/student/*` ends on light login.
- IDE: Monaco switched live between `pamsu-light` and `pamsu-dark` from the toolbar control, and stayed consistent on workspace reload.
- Rendered-text contrast audit (every visible text node vs. composited background, 4.5:1 / 3:1 large) on 12 student routes in light and dark: no failures except the disabled "Paste" button (disabled controls are exempt). The Join class dialog (modal, backdrop, input, buttons) was reviewed visually in dark.
- Mobile 375px (dark): no horizontal overflow on 6 student routes; the collapsed theme button is 43px wide. Added a compact theme button to the IDE header below `lg`, where the sidebar is hidden.
- **Not verified:** live reaction to an OS theme change (the browser pane's color-scheme emulation fires no `change` events, even for a plain listener; the code uses `matchMedia` + `useSyncExternalStore`, and re-selecting System re-reads the OS value correctly); real backend data and submission/grading flows; real devices; Firefox/Safari; keyboard-only walkthrough; reduced-motion; Monaco find/diagnostic widgets visually.

### Intentionally unchanged (light-only)
Login, Forgot Password, Register (redirects), Unauthorized, NotFound, admin, instructor pages and grading, backend, migrations, auth/route protection, API contracts.

### Remaining / for later phases
Admin dark mode (separate phase, not started). Instructor dark mode: see Phase 2.

## Instructor Theme Restoration — Phase 2

Status: **implemented and verified in a browser against a mock API.** The admin interface remains light-only; admin theming is a separate phase and is not started. Backend-dependent workflows were not tested against a real backend.

### Reused Phase 1 infrastructure (nothing duplicated)
- One provider (`StudentThemeProvider` in `features/theme/ThemeContext.jsx`, name kept to avoid churn), one storage module (`themeStorage.js`), one token set in `index.css`, one `ThemeToggle`, one pair of Monaco themes (`editorThemes.js`).
- The provider's enable rule is now a role→route-prefix map: student on `/student/*` and instructor on `/instructor/*`. Anything else (login, forgot password, admin, unauthorized, 404, logged out, a role on another role's route) is forced to light even if a dark preference is stored.
- The preference is still per account (`pamsu_theme_pref_v1:<user_id>`), so an instructor's choice never applies to a student or admin account in the same browser. No backend, migration or dependency was added.
- `index.html` pre-paint script now also handles `instructor` on `/instructor/*`.

### Sidebar control
`InstructorSidebar` passes `ThemeToggle` through `AppSidebar`'s `renderThemeControl` (profile area, expanded: Light/Dark/System radios and status line; collapsed/narrow: single cycling button). The admin area has no control.

### Components touched
- Brand text classes moved to semantic tokens (`text-text-brand`, `text-text-rose`, `bg-selected`; identical values in light): ActivityDetails, ActivityEditor, ClassManagement, PracticeModuleManager, SplitPaneGradingWorkspace, ClassRosterView, BulkEnrollModal, CreateClassModal, EditClassModal.
- Grading Bench: the Monaco `DiffEditor` was hard-coded `theme="light"`; it now follows the effective theme (`pamsu-light`/`pamsu-dark`, with added diff insert/remove colors). Grading, payloads and release logic are untouched.
- Flatpickr (ActivityEditor scheduling): the CSS was hard-coded light; it is now tokenised (calendar surface, border, arrows, weekdays, days, time inputs, popover shadow via `--shadow-popover`).
- Editor syntax: comment and line-number colors adjusted for AA on diff-highlighted lines (dark `#a89d93`, light `#5f5a54`); this also applies to the student IDE.
- Already token-based and covered without edits: InstructorDashboard, LiveMonitoring, GradingBenchRoot, GradingClassView, InstructorSettings, StudentGradebookModal, shared Modal/StateViews/CustomSelect (themed in Phase 1).

### Verification (2026-10-18, Vite dev server + mock API; seeded fake sessions)
- `npm run lint`: exit 0. `npm run build`: passes. `git diff --check`: clean.
- Rendered-text contrast audit (all visible text nodes vs composited backgrounds, 4.5:1 / 3:1 large; disabled controls exempt) on 13 instructor routes in dark and light: no failures, except (a) the Activity Editor AST checklist, which is intentionally blurred and dimmed (opacity 0.3) until a difficulty is chosen, and (b) two transient readings caught mid-fade-in that passed on re-run. Create class, Remove student and Bulk enroll dialogs and the open date picker also showed no failures in dark. The Create module dialog was reviewed visually in dark.
- Role isolation: instructor with OS dark and no saved choice → dark; manual dark on OS light kept after reload; System restores following the device (stored key cleared); sign out → login light even though a dark preference is stored; instructor visiting `/student/*` or `/admin/*` lands on a light `/unauthorized`; admin with OS dark and a stored dark preference stays light with no theme control; a student account in the same browser kept its own dark choice and the student theme control still works.
- Grading Bench: typed a score and feedback, switched Light→Dark; the same input nodes kept their values (no remount, selection kept). Diff editor switched live between light and dark.
- Live Monitoring: the poll stayed at an exact 10 s cadence across four theme switches (no extra fetches, same card nodes).
- Mobile 375px (dark): no horizontal overflow on 11 instructor routes; theme button (43px) present on each.
- **Not verified:** live reaction to an OS theme change (the browser pane emits no `change` events, same as Phase 1); real backend data, grading save/release, activity publish, roster changes, bulk import and monitoring with real sessions; the Activity Editor with validation errors, ActivityDetails modals and Practice Module task modal; Analytics charts (the student Analytics page uses CSS bars, no chart library); other browsers/devices; keyboard-only walkthrough; reduced motion.
- Diff highlight intensity in the grading diff editor was judged by eye plus computed contrast for syntax colors on highlighted lines (≥ 4.8:1 dark, ≥ 4.8:1 light).

### Remaining
Admin dark mode (separate phase). `ActivityEditor.jsx.bak` and `.bak2` exist in `features/instructor/` and were not touched.

## Sidebar polish and PostgreSQL suite run (2026-10-18)

_Branch: `dev` · Base commit: `f0bc529` (`origin/dev`) · Nothing committed or pushed. No real database was changed._

### Repository-state note (read first)
- At the start of the session, local `dev` was at `c285f54`, **5 commits behind `origin/dev`** (`0eb9c17`, `e946455`, `44a933d`, `1a80b09`, `f0bc529`, by Zithxnm). Those commits hold the student and instructor theme work (Phase 1 and 2 above) and the full backend audit. There were no tracked modifications.
- `backend/app/services/student_provisioning_service.py` and `backend/tests/test_masterlist_import.py` were **untracked** locally: `c285f54` described them but never added them. `origin/dev` tracks re-created versions with different content (see "Production blocker found first" above). The local originals would have blocked the fast-forward, so they were **moved, not deleted**, to `docs/remediation/preserved-untracked-2026-10-18/` (untracked, not staged). Then `git merge --ff-only origin/dev` was run with the owner's approval.
- Untracked helper scripts (`fix_*.py`, `check_*.py`, …), `psu_theme_backups/`, `stash-frontend-diff.txt` and `docs/remediation/auth.py.uncommitted-2026-10-16.diff` were left as they were.

### 1. Sidebar: icon-only theme toolbar and sign-out
Applies to the student and instructor sidebars (both use `AppSidebar`). Admin has no sidebar theme control and stays light-only. This supersedes the "Sidebar control" description in Phase 1 and Phase 2 (radio group with visible labels plus a status line); the theme architecture is unchanged.
- **Expanded rail:** the profile row (avatar, name, email) is unchanged. Below it is one 32 px row: a recessed track with three icon toggle buttons (sun, moon, monitor; 32×28 px each), plus an icon-only **Sign out** button (32×32) on the right. The visible labels and the "Following device · …" line were removed. The bottom block went from about 128 px to **85 px** (measured), so the navigation gets more room. Sidebar width and the nav items are unchanged.
- **Selected state, not colour alone:** the selected button is raised (panel surface plus card shadow) out of the recessed track, has a gold underline (`--color-psu-gold`, the same accent as the active nav item), and its icon is drawn with a heavier stroke and in `text-text-brand`. Unselected icons use `text-text-muted`. Only existing tokens are used, so light and dark both follow the theme.
- **Accessibility:**
  - `role="group"` with `aria-label="Color theme"`; buttons have `aria-label` "Use light theme" / "Use dark theme" / "Use system theme" and `aria-pressed`. These replace `role="radio"`, which needed arrow-key handling that was never implemented.
  - The System button has `aria-describedby` pointing at always-present text ("Follows your device setting (currently dark)").
  - A visually hidden `role="status"` live region announces changes ("Theme: Light, set manually").
  - The existing global `:focus-visible` outline (`--border-focus`) is the focus indicator.
  - Collapsed rail and the IDE toolbars: the existing single cycling button is kept, with its full sentence as the accessible name. Sign out always has `aria-label="Sign out"`.
- **Tooltips:** new `components/ui/Tooltip.jsx`. It shows on hover and on keyboard focus (`:focus-visible` only, so a mouse click doesn't leave it open), and hides on Escape, blur, scroll or resize. It renders in a portal with fixed positioning, so the rail's `overflow-hidden` can't clip it, and it is clamped to the viewport. It is `aria-hidden` (a visual mirror of the accessible name). Placement: above in the expanded rail, to the right in the collapsed rail, below in the workspace and practice headers (`tooltipSide="bottom"`). The System tooltip includes the device state ("Use system theme (device: dark)").
- **Unchanged:** `ThemeContext.jsx`, `themeStorage.js` (per-account `pamsu_theme_pref_v1:<user_id>`), `index.css` tokens, the `index.html` pre-paint script, sign-out and logout logic (`SignOutModal` → `logout()` → `/login`), navigation, auth.

### 2. Tracker continuation: PostgreSQL-only backend suites ("Full backend audit", Still open, item 1)
Phase 1 and Phase 2 of the theme restoration were already complete. The only theme item left is admin dark mode, which is a separate phase that nobody has approved, so it was **not started**. The earliest open item that needs no decision is item 1 of the full backend audit's "Still open" list: the PostgreSQL migration and concurrency suites had not been run (the audit had no PostgreSQL). This machine has PostgreSQL 18.4, so they were run here.
- **Setup (no real database touched):** `PAMSU_TEST_DATABASE_URL` was set to the local server's `postgres` maintenance database, using the credentials from `backend/.env`; the URL was never printed. The suites only use it to `CREATE` and `DROP` their own `pamsu_ide_*_pytest_<uuid>` databases. Only these 5 files were run with the variable set, not the whole suite.
- **Result: 7/7 PASS (22 s).**
  - `test_alembic_migrations.py` 3/3: no URL in `alembic.ini`; one baseline and one head; full upgrade, check, **downgrade to base**, re-upgrade, check (this confirms the committed Fix B on a fresh database).
  - `test_execution_request_idempotency_concurrency`, `test_grade_concurrency`, `test_partner_execution_concurrency` and `test_submission_concurrency`: 1/1 each.
- **After the run:** the only `pamsu_ide%` databases on the server are the pre-existing `pamsu_ide_alembic_test` (not created by this session, left alone) and `pamsu_ide_db`. `pamsu_ide_db` is still at `c25114413200` with 21 users (checked through a read-only session).
- **Still not covered:** PostgreSQL 15, the project's target version (only 18.4 is installed).

### 3. Directly related fix: Windows test-id limit
- **Full SQLite suite on this Windows machine (before the fix):** 809 passed, 5 skipped, **4 errors** (13 min 28 s).
- **Cause:** all 4 errors came from `test_backend_audit_regressions.py::test_pathological_code_is_reported_not_crashing`. Its two parametrized inputs (100 kB strings) became part of the test id. Pytest exports the id in `PYTEST_CURRENT_TEST`, and Windows rejects environment variables over 32,767 characters (`ValueError`), failing setup and teardown of each case. This is not an application defect, and on Linux the suite passes.
- **Fix:** short `ids=` on that parametrize, with a comment. The inputs and assertions are unchanged.
- **After the fix:** the file passes 35/35, so the full suite is 811 passed and 5 skipped, matching the audit's Linux result. The full suite was not re-run end to end after this one-line change.
- **Timing note:** on Windows the suite takes about 13 minutes, compared with about 70 s in the audit. A connection to the refused port `redis://127.0.0.1:1` is retried by Windows for about 2 s instead of failing at once. This was not changed.

### Files modified (tracked)
```
audit-status.md                                    (this section)
backend/tests/test_backend_audit_regressions.py    (short parametrize ids; Windows env-var limit)
frontend/src/components/layout/AppSidebar.jsx      (theme toolbar + icon sign-out in one row; tooltips)
frontend/src/features/theme/ThemeToggle.jsx        (icon-only toggle buttons, aria-pressed, sr-only status, tooltips)
frontend/src/features/practice/PracticeWorkspace.jsx  (tooltipSide="bottom" on the header theme button)
frontend/src/features/workspace/Workspace.jsx      (tooltipSide="bottom" on the header theme button)
```

### Files created
```
frontend/src/components/ui/Tooltip.jsx                          (portal tooltip; to be committed)
docs/remediation/preserved-untracked-2026-10-18/                 (the two original untracked files; NOT for commit)
```

### Verification
| Check | Result |
|---|---|
| `npm run lint` | **PASS** (exit 0, no output) |
| `npm run build` | **PASS** |
| `git diff --check` | **PASS** (only `core.autocrlf` LF→CRLF notices) |
| Backend: `test_backend_audit_regressions.py` | **PASS** 35/35 |
| Backend: full SQLite suite | 809 passed, 5 skipped, 4 errors **before** the id fix; those 4 now pass (see section 3) |
| Backend: PostgreSQL-only suites (18.4) | **PASS** 7/7 |

**Browser:** Vite dev server; the backend was not running, so pages showed "Server unavailable". The sessions were fake student and instructor sessions seeded in `localStorage` and cleared afterwards.
- **Expanded rail (1025 px and 763 px with the rail expanded):**
  - The three icons are aligned in one track (34 px pitch), and sign-out sits on the same row, vertically centred.
  - No horizontal overflow, and the profile row is unchanged.
  - Viewed in dark (System) and light (manual).
- **Theme changes:**
  - Clicking Light gives `html.light`; the key is stored as `light`; `aria-pressed` moves; the status reads "Theme: Light, set manually".
  - Dark persisted across a route change.
  - System clears the stored key, follows the emulated OS (dark), and its description reads "Follows your device setting (currently dark)".
- **Tooltips:**
  - The hover tooltip renders above the button, inside the viewport.
  - With the keyboard, Tab to the Light button shows the focus ring and the tooltip; Escape hides the tooltip and keeps focus.
  - In the collapsed rail the tooltip renders to the right, outside the 60 px rail, without clipping.
- **Sign out:** the tooltip reads "Sign out"; clicking opens the existing confirmation dialog, and the tooltip hides; confirming goes to `/login` with the token cleared, `html.light`, and no theme control.
- **Instructor sidebar:** same layout, and the stored Dark preference is shown as pressed.
- **375 px (mobile emulation):** the rail is collapsed; the theme and sign-out buttons are 43×36; no horizontal overflow.
- No console errors.
- **Not verified:**
  - the header theme button's tooltip in the IDE and practice workspaces (those pages need a backend to render their toolbar);
  - screen-reader output (only the attributes were checked);
  - live OS theme-change events (the pane emits none, as in Phase 1);
  - other browsers and touch devices;
  - an admin session (admin doesn't use `AppSidebar`; no admin code was touched).

### Remaining / next pending task
1. **Next:** "Full backend audit", Still open, **item 2**: admin actions (deactivate, delete, password reset, settings) write no audit record, because `audit_records.action_type` has a DB CHECK constraint. **Needs approval for a migration** that widens the constraint. Not started.
2. Items 3–10 of that list each need a product decision or a design change, and were not started:
   - fail-open Redis behaviour;
   - guest-account policy;
   - synchronous Judge0 wait in practice submit;
   - AI tutor dependency and wiring;
   - legacy `POST /execution/submissions/`;
   - `default_ast_strictness`;
   - retakes and enrollment decisions;
   - `rediss://` certificate checks.
3. Admin dark mode: a separate phase, **not approved**, not started. Login, public auth and admin stay light-only.
4. Run the PostgreSQL suites on PostgreSQL 15.
5. **Housekeeping:**
   - Compare `docs/remediation/preserved-untracked-2026-10-18/` with the committed versions, then delete the folder.
   - `ActivityEditor.jsx.bak`/`.bak2` and the root helper scripts are still untracked.
   - Rotate the SMTP key (still open from earlier sections).

## Preserved-file comparison and admin audit logging investigation (2026-10-18)

_Branch: `dev` at `50bc701` (equal to `origin/dev`; the sidebar commit was made and pushed by the owner during this session) · Nothing committed or pushed by this session. No migration applied anywhere. The only real-database access was read-only._

### 1. Preserved originals vs tracked versions
Compared `docs/remediation/preserved-untracked-2026-10-18/` (originals from the 2026-10-17 session, never committed) with the tracked files that `e946455` re-created. **Nothing was overwritten, merged or deleted.**

**Empirical check:** the preserved test file (23 tests) was run against the **current tracked service**. The repository was not changed; pytest loaded `tests.conftest` as a plugin. Result: **19 passed, 4 failed.**
- 2 failures: the duplicate messages no longer name the rows ("appears on rows 5, 6").
- 1 failure: different email-domain wording.
- 1 failure: the preserved email test's fake SMTP doesn't accept the new `timeout=` argument. In a scratch copy with only that stub fixed (`**kwargs`), it **passes**: the rendered setup email has no "Temporary Password", says "Forgot password?", and doesn't contain `PamsU@2026`.

**`student_provisioning_service.py`** (preserved 337 lines, tracked 436):

| Topic | Preserved original | Tracked (`e946455`) | Assessment |
|---|---|---|---|
| Password for new accounts | bcrypt hash of a random secret (one bcrypt cost per row) | `"!" + token_urlsafe(32)`, not a bcrypt hash; `verify_password` returns False on its `ValueError` | Tracked is better (no hashing cost, can never verify). **Preserved is obsolete** |
| Reset → sign in | — | Preserved test `test_student_sets_password_through_reset_otp_flow` **passes** on tracked code: the OTP reset replaces the marker and the student can sign in | Behaviour kept |
| File checks | `.xlsx` detected by extension **or** `PK` magic; anything else read as CSV; no size limit | Requires a `.csv`/`.xlsx` name; 2 MB limit (`MAX_MASTERLIST_BYTES`, used by the router); empty file / no rows / no worksheet rejected; repeated header names rejected; stops reading `.xlsx` after the row limit; closes the workbook | Tracked is stricter and safer |
| Existing non-student account with the same email and school ID | Reported as **skipped** | **Failed**: "belongs to a non-student account" | Tracked is correct |
| Excel numeric-ID hint | Always added to a school-ID error | Only when Excel stored the ID as a number | Tracked is more precise |
| Error detail per row | **All** validation messages, plus "Missing email, school ID, name." in one line | First error only | Preserved is more informative (minor) |
| Duplicates inside the file | Names the rows ("rows 2, 3"); a row can fail on both email and school ID | Generic message; email checked first (`elif`) | Preserved is more helpful to MIS (minor) |
| Conflict logging | `logger.warning` on a rolled-back batch | None | Minor |
| Public names | `parse_masterlist`, `REQUIRED_COLUMNS_MESSAGE` | `_parse_masterlist`, `make_unusable_password_hash`, `UNUSABLE_PASSWORD_PREFIX`, `MAX_MASTERLIST_BYTES` | A repository search finds **no reference** to the preserved-only names. `admin.py` uses `MAX_MASTERLIST_BYTES`, and the tracked tests use `UNUSABLE_PASSWORD_PREFIX` |

**`test_masterlist_import.py`** (preserved 14 functions / 23 cases, tracked 16 functions / 26 cases):
- **Only in tracked:** non-student email; pending enrollment completed for a created student; unauthenticated import; `.xlsx` numeric-ID hint; sign-in refused before a password reset.
- **Behaviour only the preserved file covers:**
  - **(a)** the **rendered** setup email contains no credential. The tracked test only checks that `temp_password=None` is passed to the stubbed sender.
  - **(b)** the **full** reset-OTP → successful sign-in path. The tracked test only checks that sign-in fails before a reset.
- The other preserved cases (row limit, split names, `.xlsx`, duplicates, conflicts, invalid rows) have tracked equivalents.

**Recommendation (smallest safe reconciliation; not applied):**
1. Port the two preserved tests (a) and (b) into `backend/tests/test_masterlist_import.py`, with the fake SMTP accepting `**kwargs`. This is test-only and adds coverage of two security properties.
2. Optional UX change: name the duplicate row numbers in the duplicate messages. That changes user-facing text; decide with MIS.
3. Don't port the bcrypt password, the extension-less CSV fallback, or the "skip non-student" behaviour. They are obsolete or less safe.
4. Then delete `docs/remediation/preserved-untracked-2026-10-18/` (the owner's decision).

### 2. Admin audit logging: root cause
Item 2 of the full backend audit's "Still open" list: "Admin actions (deactivate, delete, password reset, settings) write no audit record".

**Existing infrastructure (reuse it; nothing new is needed):**
- `AuditRecord` (`audit_records`): `actor_user_id` FK `RESTRICT`, `action_type`, `resource_type`, `resource_id`, `outcome`, JSON `audit_data`, `occurred_at`, a unique `audit_key`, and an immutability rule.
- `services/audit_service.create_audit_record(..., commit=False)` flushes inside the caller's transaction, so the domain change and its audit record commit or roll back together. `classroom_service`, `task_service`, `evaluation_service` and `submission_service` all use this through a `_record_audit` helper with a deterministic `audit:{action}:{resource}:{id}` key.
- `AuditRecordCreateInternal` (strict) runs `validate_audit_data`, which rejects known sensitive keys (`password`, `otp`, code, grades, …).

**What each admin write does today** (`backend/app/routers/admin.py`):

| Endpoint | Operation | Audit record today |
|---|---|---|
| `POST /admin/students` | Create student | **None for the account.** Pending enrollments it completes write `student_enrolled` (atomic, per-class savepoint) |
| `POST /admin/students/bulk-register/file` | Masterlist import | **None for the accounts.** Pending enrollments write `student_enrolled` |
| `POST /admin/students/{id}/pending-enrollments/apply` | Retry pending enrollments | `student_enrolled` per class: **already correct** |
| `POST /admin/guests` | Create guest | **None** |
| `POST /admin/instructors` | Create instructor | **None** (it also emails the plaintext password; pre-existing, item 9) |
| `PATCH /admin/users/{id}/status` | Activate / deactivate | **None** |
| `DELETE /admin/users/{id}` | Delete account | **None** |
| `PATCH /admin/users/{id}/password` | Admin password reset | **None** |
| `PATCH /admin/settings` | Maintenance mode, default strictness, registration | **None**. Also, `set_system_setting` **commits each key separately**, so a failure partway leaves a partial update |
| `GET /admin/*` | Reads | Not audited; no read is audited anywhere in the app |

**Root cause:**
- It is an **architectural gap**: the audit calls were never written. It is not caused by swallowed exceptions or wrong transaction boundaries; none of these handlers call the audit service at all.
- For deactivation, deletion, password reset and settings, the calls **cannot** be added as things stand. The DB constraints `ck_audit_records_action_type` / `ck_audit_records_resource_type` (baseline `18d3ef8f020d`, never changed since) and the matching `AuditActionType` / `AuditResourceType` `Literal`s allow only the 20 baseline action types and 7 resource types. None of them describes these actions, and there is no resource type for settings.
- A read-only check of local `pamsu_ide_db` confirmed both constraints exactly match the baseline. It has 37 audit rows, all of existing types (`login_succeeded` 34, `login_failed` 1, `grade_created` 1, `submission_created` 1).
- **Account creation is the exception:** `user_registered` / `user` are allowed, but **nothing writes them anywhere**, because the self-registration flow was retired. Reusing them for admin provisioning needs no migration, but it changes what "registered" means (decision D1).

**Other findings:**
- **Sensitive data:** the key blocklist is exact-match, so it misses `new_password`, `temp_password`, `token`, `access_token`, `refresh_token`, `secret` and `api_key`.
  - No current code writes those keys, and the proposal below never includes a password, hash, OTP or token.
  - Application-only hardening (no migration): add those keys to `PROHIBITED_AUDIT_KEYS`, and build admin `audit_data` from a fixed per-action set of fields.
- **Identification:**
  - The proposed records name the actor (`actor_user_id` = the admin), the action, the target (`resource_type`/`resource_id` = the user id, or `global` for settings), the time (`occurred_at`) and the outcome (`succeeded`).
  - However, `GET /admin/audit-logs` returns neither `resource_id` nor `audit_data`, so an admin can't see **whom** an action affected. That fix is application-only.
- **Failed attempts:** a refused delete (409, the account has records) would roll back its own audit row with it. Recording `outcome="failed"` would need a second, separate transaction after the rollback (decision D4).
- **No back-fill:** historical admin actions were never recorded and won't be fabricated.

### 3. Is a migration necessary? Yes, for 4 of the 5 action groups
An application-only change can't store an action type the DB CHECK constraint rejects: the insert raises `CheckViolation`, and the admin action rolls back with it. The `Literal`s and model can be widened in code, but the deployed constraint can't. The only alternatives are worse:
- misusing existing types (for example `enrollment_status_changed` for an account), which corrupts the audit vocabulary;
- dropping the constraint, which weakens integrity.

### 4. Migration proposal (DRAFT; not applied, not committed)
**Where:** isolated worktree `C:\Users\ACER\Documents\Codes\pamsu-python-ide-admin-audit-draft`, branch `draft/admin-audit-action-types`, cut from `50bc701`. All files there are **uncommitted**. The worktree has no `backend/.env`, so it can't reach a real database by accident.

1. **Problem:** admin account, status, password, deletion and settings actions can't be audited, because the constraints don't allow their types.
2. **Why not application-only:** see section 3.
3. **Schema change:** revision `61330560eec5_allow_admin_audit_action_types.py`, `down_revision = c25114413200`, giving a single head (verified).
   - `ck_audit_records_action_type` = the 20 baseline values plus `user_created`, `user_status_changed`, `user_password_reset`, `user_deleted` and `system_settings_updated`.
   - `ck_audit_records_resource_type` = the 7 baseline values plus `system_setting`.
   - `AuditRecord` (`domain_models.py`) and `AuditActionType` / `AuditResourceType` (`audit_schema.py`) are widened identically. No column, index or other table changes.
4. **Existing data:** none is touched. The new lists are strict supersets, so every existing row stays valid.
5. **Forward:** on PostgreSQL, `SET LOCAL lock_timeout = '10s'`, then drop and re-add each constraint; re-adding validates it with a single table scan. Other dialects use `batch_alter_table` (migrations don't run on SQLite in this project).
6. **Downgrade:**
   - It restores the exact baseline lists.
   - It **refuses, changing nothing,** if any row uses a new type, because audit rows are immutable and are never deleted to make it fit. In that case, roll back by restoring the pre-upgrade backup, or simply leave the widened constraint in place, which is harmless.
   - Offline (`--sql`) downgrade is refused, because the row check needs a connection.
   - Nothing about it is irreversible.
7. **Locking:**
   - `DROP`/`ADD CONSTRAINT` take an `ACCESS EXCLUSIVE` lock on `audit_records`. It is held until the migration transaction commits (Alembic uses transactional DDL on PostgreSQL).
   - Every audited action (logins, grading, submissions) waits on that table for the duration. That is a scan of a small table (37 rows locally; production size unknown).
   - The lock timeout makes it fail fast rather than queue behind a long transaction.
8. **Compatibility:**
   - The chain is unchanged, there is one head, and no historical migration is edited.
   - Old application code never writes the new types, so the migration can be deployed before or together with the code that uses them.
   - Code that writes them **must not** run before the migration: the admin action would fail with a 500 and roll back.
9. **Tests on disposable PostgreSQL 18.4** (new `backend/tests/test_admin_audit_migration.py`, run in the worktree; temporary databases only): **6/6 PASS** in 26 s, with `test_alembic_migrations.py`. They cover:
   - the new types are rejected at `c25114413200` and accepted at `61330560eec5`;
   - an existing row survives the upgrade;
   - unknown values are still rejected;
   - the **DB constraint values equal the ORM model's** (`alembic check` doesn't compare CHECK constraints, so this guards against drift);
   - downgrade refuses while a new type is in use, and the revision, constraint and row are unchanged afterwards;
   - an unused downgrade restores the baseline lists exactly and keeps old rows, and re-upgrade works;
   - the full upgrade → downgrade base → re-upgrade passes through the new revision.
   - **Still needed:** PostgreSQL 15 (the project's target), and the real admin audit writes (not implemented).
10. **Deployment and rollback:**
    - `start.sh` runs `alembic upgrade head` **on every start**, so merging this into a deployed branch applies it on the next deploy.
    - Before deploying:
      - back up the database;
      - check the constraints read-only: `SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'audit_records'::regclass AND contype = 'c';` (they should match the baseline);
      - deploy migration, model and audit-writing code together.
    - **Rollback:** revert the application code and keep the widened constraint, which is harmless. Downgrade only if no new-type rows exist.
    - The separate `main` branch problem (missing migration files, recorded earlier) still blocks deploys from `main`.
11. **Decisions needed:** see D1–D6 below.

**Proposed use after approval (not implemented):** add one admin audit helper in `routers/admin.py` (or a small service). It follows the `_record_audit` pattern with `commit=False` before each existing `db.commit()`, so each action and its record are atomic.
- **`user_created`** (resource `user`, id = the new user): `{"role", "source": "admin_form" | "guest" | "instructor" | "masterlist"}`. The masterlist import writes one record per created row inside its existing all-or-nothing transaction.
- **`user_status_changed`:** `{"is_active", "previous_is_active"}`.
- **`user_password_reset`:** `{"password_version"}`; never the password or the hash.
- **`user_deleted`:** `{"role"}`; identity fields depend on D3.
- **`system_settings_updated`** (resource `system_setting`, id `global`): `{"changes": {key: {"from", "to"}}}` for changed keys only; the values are booleans or enums. `set_system_setting` gets a `commit=False` mode, so the three keys and the record commit once.
- **New tests:** `tests/test_admin_audit_logging.py`.
  - One record per admin action, with the right actor, target and fields.
  - No secret keys.
  - A failed action leaves no record.
  - An audit failure rolls the action back.
  - Non-admins get 403 and no record.

### 5. Tests executed this session
| Test | Result |
|---|---|
| Full backend suite, SQLite, main checkout (`50bc701` content) | **811 passed, 5 skipped, 0 failed** (15 min 05 s). This is the full re-run the previous session didn't do, so the Windows id fix is confirmed |
| Preserved `test_masterlist_import.py` against the tracked service | 19 passed, 4 failed (explained in section 1); the email-body test passes with only its stub fixed |
| Worktree (draft): `test_admin_audit_migration.py` + `test_alembic_migrations.py`, PostgreSQL 18.4, temporary databases | **6/6 PASS** |
| Worktree (draft): `test_audit_models`, `_router`, `_schemas`, `_service`, `_workflow`, `test_pending_enrollment_workflow`, `test_masterlist_import`, `test_backend_audit_regressions`, `test_admin_audit_migration` on SQLite | **194 passed, 3 skipped** (the PostgreSQL-only migration tests) |
| Worktree: `git diff --check`, `alembic heads` | Clean; single head `61330560eec5` |
| Worktree: pyflakes on the new files | Only the expected pytest fixture-import warning in the test (same pattern as `conftest.py`'s `noqa` import) |
| Read-only checks of `pamsu_ide_db` before and after | Revision `c25114413200`, 37 audit records, unchanged; no temporary databases left |

**Not run:**
- admin audit-logging behaviour tests (there is nothing to test until the writes are implemented);
- PostgreSQL 15;
- the full suite inside the worktree (only the related suites above).

### 6. Decisions needed (owner / security)
- **D1:** account creation: new `user_created` (as drafted), or reuse the unused `user_registered` (no migration for that part)?
- **D2:** approve the five new action types, the `system_setting` resource type, and their names.
- **D3:** `user_deleted`: keep only the user id and role, or also the email / school ID? Those would retain personal data of a deleted account, but without them the id is the only trace.
- **D4:** record refused or failed admin attempts (`outcome="failed"`, a separate transaction)?
- **D5:** one summary record per masterlist import, in addition to the per-account records?
- **D6:** the masterlist reconciliation in section 1 (port the 2 tests; whether to name duplicate rows), and deleting the preserved folder.

### 7. Next pending task
**Admin audit logging stays open. It is investigated and the migration is drafted, but nothing is implemented.**
1. Owner reviews the draft in the worktree and decides D1–D5.
2. After approval, on `draft/admin-audit-action-types`:
   - implement the audit writes;
   - make settings updates atomic;
   - extend `PROHIBITED_AUDIT_KEYS`;
   - return `resource_id` from `GET /admin/audit-logs`;
   - add `tests/test_admin_audit_logging.py`;
   - re-run the full suite and the PostgreSQL suites (also on 15 if available).
3. Then items 3–10 of "Still open" (unchanged).

Cleaning up the worktree when it's no longer needed: `git worktree remove ../pamsu-python-ide-admin-audit-draft`, after saving or committing its files.

## Admin audit logging: implemented on the draft branch (2026-10-18)

_Branch: `draft/admin-audit-action-types`, fast-forwarded to `dev` (`e444596`) before the work started. Worktree: `C:\Users\ACER\Documents\Codes\pamsu-python-ide-admin-audit-draft`. **Nothing committed, pushed or merged. Migration `61330560eec5` was not applied to any real database.** `pamsu_ide_db` was only read, and it was the same before and after every PostgreSQL run: revision `c25114413200`, 37 audit records._

Owner decisions D1–D6 (from the investigation above) were approved and applied as follows.

### Audit events now written (`backend/app/routers/admin.py`)
| Admin action | Success record (same transaction as the change) | Refused / failed record (separate transaction, after rollback) |
|---|---|---|
| `POST /admin/students` | `user_created` (role, `source: admin_student_form`, `enrolled_from_pending`) | Duplicate email or school ID (400): **no record**, because no account exists and it is form validation |
| `POST /admin/guests` | `user_created` (role, `source: admin_guest_form`, `guest: true`) | Duplicate: no record |
| `POST /admin/instructors` | `user_created` (role, `source: admin_instructor_form`, `setup_email: queued_after_commit`) | Duplicate: no record |
| `POST /admin/students/bulk-register/file` | One `user_created` per created account (`source: masterlist_import`, `import_id`, `row`), plus one `masterlist_imported` summary (`file_type`, `rows`, `created`, `skipped`, `failed`, `enrolled_from_pending`, `pending_left`) | `masterlist_imported` `failed` with `reason: invalid_file` (400) or `database_conflict` (409). No `user_created` |
| `PATCH /admin/users/{id}/status` | `user_status_changed` (role, `previous_is_active`, `is_active`) | Own account: `denied`, `own_account`. Unknown id: `failed`, `not_found` |
| `PATCH /admin/users/{id}/password` | `user_password_reset` (role, `password_version` only) | Unknown id: `failed`, `not_found` |
| `DELETE /admin/users/{id}` | `user_deleted` (role, `was_active`); the id is kept in `resource_id` | Own account: `denied`. Unknown id: `failed`, `not_found`. Account with records (409): `failed`, `has_dependent_records`, and **no** success record |
| `PATCH /admin/settings` | `system_settings_updated` (resource `system_setting`, id `global`, `changes: {key: {from, to}}`, changed keys only; no record when nothing changed) | Database error: `failed`, `database_error`, `requested_keys` |
| `POST /admin/students/{id}/pending-enrollments/apply` | Already wrote `student_enrolled` per class (unchanged) | — |

- **Actor:** always `current_admin.user_id` from the authenticated token; it is never taken from the request.
- **Masterlist summary type:** the summary event needed its own type, because none of the five approved ones describes an upload. It uses one added action type, `masterlist_imported`, and one added resource type, `masterlist_import`, both in the same unapplied draft migration. **They need the owner's confirmation**, as the only addition beyond D2.

### Guarantees (each covered by a test)
- **Atomicity:**
  - A success record is added with `create_audit_record(commit=False)` in the action's own transaction (`services/admin_audit_service.record_admin_action`).
  - If the record can't be written (schema validation, audit-service error or database error), the action is **rolled back** and the client gets **503** "The change was not saved because it could not be recorded in the audit log". A change never commits without its record.
  - The masterlist import writes its per-account records and its summary inside the existing all-or-nothing transaction.
- **Settings are atomic:**
  - `set_system_setting(..., commit=False)` flushes; the three keys and the record commit once.
  - A failure partway leaves **all** settings as they were and returns 503 "Nothing was changed", with a `failed` record.
  - The old behaviour committed each key separately.
- **Truthful outcomes:**
  - Failure records are written only after the rollback, in their own transaction, and are never `succeeded`.
  - If a failure record can't be written, this is logged with `logger.exception` and the original error response is still returned.
- **External side effects:** account-creation records say `setup_email: queued_after_commit`. The email is only queued, as a background task after the commit, and its delivery is **not** claimed or audited.
- **Deleted accounts:**
  - The record keeps the internal user id (`resource_id`), the role and `was_active`; **no email, school ID or name** (D3).
  - The audit-log endpoint then shows `target_user_id` with `target_exists: false`.
- **Unique audit keys:** each `user_created` record has a unique key. A first draft used a deterministic per-user-id key; SQLite can reuse a deleted account's id, which made the next account creation fail with 503. A regression test reproduces that and is shown to fail with deterministic keys.

### Privacy filter (`backend/app/schemas/audit_schema.py`)
- **Normalization:** keys are split on camelCase, then on any non-alphanumeric character (hyphen, space, dot), then lowercased.
- **What `is_sensitive_audit_key` rejects:**
  - the existing exact list;
  - any key containing `password`, `passwd` or `passphrase` (including split forms like `pass_word`);
  - the tokens `otp`, `token(s)`, `jwt`, `secret(s)`, `credential(s)`, `cookie(s)` and `pwd`;
  - `{api, private, secret, signing, encryption, access, session}_key`;
  - `{reset, verification, otp, auth, confirmation, recovery, security, login, mfa, totp}_code`.
- **Allowlist:** `password_version`.
- **Values:** bcrypt-hash and JWT-shaped strings are rejected anywhere in the metadata.
- **Checked:** 21 credential-like spellings are rejected; 12 useful keys (`class_code`, `subject_code`, `password_version`, `is_active`, …) are kept.
- **Existing data:** the only `token`-named keys in the code base are similarity counters in `jaccard.py`, which never go to audit metadata, and similarity data is already prohibited there.

### Admin audit-log endpoint (`GET /admin/audit-logs`)
- **Kept:** every existing key, plus pagination and the admin-only access.
- **Added:**
  - `resource_id`;
  - `target_user_id` (for `user` resources);
  - `target_exists`;
  - `target_name` / `target_role` (current values, `null` for a deleted account);
  - `details` (the privacy-validated `audit_data`).
- **Ordering:** a tie-break on `audit_id` makes paging deterministic, because records written in one transaction share `occurred_at` on PostgreSQL.
- **Frontend:** it reads only the old keys and is unchanged. The admin UI doesn't show the target yet (follow-up).

### Masterlist (D6)
- Duplicate rows name the rows involved again: "The same school ID appears on rows 2, 3." If both values repeat, both are reported. The tracked test now asserts the exact text.
- **Ported from the preserved originals:**
  - `test_rendered_setup_email_contains_no_credential`, with the fake SMTP updated to accept `timeout`/`**kwargs`;
  - `test_student_sets_password_through_reset_code_then_signs_in`.
- No obsolete implementation code was restored. The preserved folder is untouched.

### Migration `61330560eec5` (draft; not applied anywhere real)
- **Chain:** `down_revision = c25114413200`, single head, and no historical migration changed (`git diff -- backend/alembic` is empty; the revision file is new).
- **Allowed values:** 20 baseline + 6 new action types and 7 baseline + 2 new resource types. `AuditRecord`, `AuditActionType`/`AuditResourceType` and the DB constraint agree, and a PostgreSQL test compares DB and ORM values directly.
- **Downgrade:** it refuses, changing nothing, while any record uses a new type.
- **Deployment order:** the application code writes the new types, so **it must not run before this migration**: such a write fails, and the admin action rolls back with a 503. `start.sh` runs `alembic upgrade head` before the API starts, so deploying both together is safe. Back up first.

### Files
Modified:
```
backend/app/core/system_settings.py               (commit=False mode; read_stored_system_settings)
backend/app/models/domain_models.py               (CHECK lists: 6 actions, 2 resources)
backend/app/routers/admin.py                      (audit records for every mutation; atomic settings; audit-log target fields)
backend/app/schemas/audit_schema.py               (Literals; normalised sensitive-key and value filter)
backend/app/services/student_provisioning_service.py  (per-account + summary records; row numbers in duplicate reasons)
backend/tests/test_masterlist_import.py           (2 ported security tests; duplicate-row assertions)
audit-status.md                                   (this section)
```
Created:
```
backend/alembic/versions/61330560eec5_allow_admin_audit_action_types.py
backend/app/services/admin_audit_service.py
backend/tests/test_admin_audit_logging.py         (55 tests)
backend/tests/test_admin_audit_migration.py       (3 PostgreSQL-only tests)
```

### Tests (Windows, Python 3.13.3, pytest 9.1.1)
| Suite | Result |
|---|---|
| `test_admin_audit_logging.py` (SQLite) | **55 passed** |
| `test_masterlist_import.py` (SQLite) | **28 passed** (26 + 2 ported) |
| Audit, pending-enrollment and masterlist suites before the new tests (SQLite) | 159 passed (no regressions from the changes) |
| Mutation check: success-record writes disabled | 9 success-record tests fail, as they should; failure-path tests unaffected |
| Mutation check: deterministic `user_created` keys | The id-reuse regression test fails, as it should |
| **Full backend suite, SQLite (final code)** | **868 passed, 8 skipped, 0 failed** (13 min 38 s). Compared with the 811 baseline: +55 admin audit tests, +2 ported tests. The 8 skips are the 5 existing and 3 new PostgreSQL-only tests. After the run, `test_admin_audit_logging.py` + `test_masterlist_import.py` were re-run on the final files: 83 passed |
| **PostgreSQL 18.4, temporary databases:** `test_admin_audit_migration` (3), `test_alembic_migrations` (3), 4 concurrency suites (4) | **10 passed** |
| `alembic heads` / `git diff --check` / pyflakes `backend/app` | single head `61330560eec5` / clean / no warnings (the migration test has the usual pytest fixture-import notice) |

**Not verified:**
- **PostgreSQL 15** (the project's target version; only 18.4 is installed).
- **Admin endpoints against a migrated PostgreSQL database end to end.** The SQLite test database is created from the same ORM CHECK constraints, and the PostgreSQL test proves the ORM and migration values are identical, but the HTTP flows themselves ran on SQLite.
- **Real SMTP delivery.**
- **The browser admin UI.**

### Remaining / decisions
1. **Confirm** the added `masterlist_imported` / `masterlist_import` types.
2. **Refused attempts by non-admins** (403 from `get_current_admin`) are **not** audited: the dependency rejects them before any admin handler runs, and there is no action type for "unauthorized admin attempt". Auditing them needs a design decision about noise and a type.
3. Duplicate or validation rejections of the account-creation forms are not audited (no target account exists).
4. **Pre-existing, unchanged:** `POST /admin/instructors` still emails the plaintext initial password (open item 9). The audit record never contains it.
5. **Frontend follow-up:** show the target and details in the admin audit-log tab.

### Next task
1. **Owner review** of the draft branch, then a commit on `draft/admin-audit-action-types`, and a PR into `dev` once approved.
2. **Before merging:**
   - run the PostgreSQL suites on PostgreSQL 15 if possible;
   - check production's `audit_records` constraints read-only (SQL in the investigation section).
3. **Then:** items 3–10 of the backend audit's "Still open" list. **Item 2 (admin audit logging) is done in code on the draft branch; it is not merged or deployed.**

### Pre-commit review (2026-10-18): 2 blocking issues fixed
An independent review of the full diff against `dev` found two blocking defects and one minor one. All three are fixed and covered by regression tests. **The test numbers below supersede the ones in the section above.**

1. **Blocking: deleting a user rewrote immutable history.** This predates the branch, but the branch exposed it.
   - `User.audit_records_created` and `User.academic_events_created` had SQLAlchemy's default delete behaviour. Deleting a user who had ever acted (for example, logged in) loaded those rows, set their nullable `actor_user_id` to **NULL**, and deleted the account with 200. This bypassed the database's `ON DELETE RESTRICT` and the immutability rules.
   - It was reproduced first: the delete returned 200 and `login_succeeded.actor_user_id` became `None`.
   - **Fix:** `passive_deletes="all"` on both relationships (`domain_models.py`). The ORM no longer touches those rows, `RESTRICT` refuses the delete, and the endpoint returns 409 plus a `failed` `user_deleted` record (`has_dependent_records`). There is no schema change.
   - **Consequence:** an account that has any audit record or academic event as actor (for example, any login) can't be deleted, only deactivated. That is what the 409 message already said.
2. **Blocking: audit-failure logging could leak secrets.**
   - `AdminAuditError` chained the original exception, and the router logged it with `exc_info`.
   - A pydantic `ValidationError` includes `input_value` (the rejected metadata). A SQLAlchemy error includes flush parameters, and the audit lookup's autoflush can include a pending `password_hash` UPDATE.
   - **Fix:**
     - `safe_error_summary()` logs exception class names only;
     - `AdminAuditError` is raised `from None`;
     - `record_admin_failure` and the router log without `exc_info`.
3. **Minor:** target-id parsing in `GET /admin/audit-logs` now requires ASCII digits. `"²".isdigit()` is `True`, and `int("²")` raised an error.

**New regression tests** (in `test_admin_audit_logging.py`, now **60 tests**):
- deletion is refused, and history is untouched, for an audit record and for an academic event;
- rejected metadata never reaches the error or its chain;
- audit failures log none of an injected hash, the new password or a secret;
- non-ASCII digit resource ids.

Both leak tests were **shown to fail** under a plugin that restores message-text logging.

**Results after the fixes**, on files with recorded `git hash-object` fingerprints that were confirmed unchanged after the runs:

| Suite | Result |
|---|---|
| Full backend suite, SQLite | **873 passed, 8 skipped, 0 failed** (12 min 19 s) = 811 baseline + 60 admin audit + 2 ported masterlist. The 8 skips are the PostgreSQL-only tests |
| PostgreSQL 18.4, temporary databases (`test_admin_audit_migration` 3, `test_alembic_migrations` 3, 4 concurrency suites) | **10 passed**. `pamsu_ide_db` before and after: `c25114413200`, 37 audit records |
| `alembic heads` / `git diff --check` / `pyflakes backend/app` | `61330560eec5` only / clean / clean |

**Review conclusions (no further blocking issues):**
- **Actor:** always `current_admin.user_id` from the token.
- **Access:** every mutation and `GET /admin/audit-logs` return 403 for students and instructors and 401 without a token, with no records written.
- **Untouched areas:** authentication, role checks and grading code are unchanged.
- **Migration:**
  - parent `c25114413200`, one head, no historical file edited;
  - existing rows are untouched;
  - downgrade refuses while new types are in use.
- **Deploy order:** against a database where the migration hasn't run, the new types violate the CHECK constraint. The error is wrapped as `AdminAuditError`, and the action **fails closed with 503**; it is never committed without its record or misreported as a duplicate.

**Remaining risks (not blocking):**
- **Pre-existing, all endpoints:** a database error raised at `db.commit()` itself (outside the audit write) is logged by FastAPI with SQLAlchemy's statement parameters, which can include a new `password_hash`. Recommended separate change: `create_engine(..., hide_parameters=True)` in `core/database.py`.
- **PostgreSQL 15 is not verified.**
- **Admin HTTP flows were tested on SQLite only.** The CHECK constraints there come from the same ORM definitions, and the PostgreSQL test proves the ORM and migration values match.
- **Non-admin 403 attempts** aren't audited.
- The added `masterlist_imported` / `masterlist_import` types still need owner confirmation.

## SQLAlchemy statement parameters in error logs (2026-10-18)

Branch `claude/nice-faraday-a9cfcd` (worktree `.claude/worktrees/nice-faraday-a9cfcd`), based on `dev` `e444596`. Separate from the admin audit branch on purpose.

### Vulnerability
Found during the pre-commit review of the admin audit branch. When a database error was raised at `db.commit()` outside the audit helper (for example a dropped connection during an admin password reset), FastAPI logged the unhandled SQLAlchemy exception. SQLAlchemy's exception text includes the statement's bound parameters, so the server log could receive a freshly computed `password_hash` or other personal data. This affected every endpoint, not only admin ones. The admin audit code itself already logs only exception class names.

### Root cause
`create_engine` defaults to `hide_parameters=False`, so `StatementError.__str__` appends `[parameters: (...)]`. The application engine in `backend/app/core/database.py` did not override it.

### Fix
- `backend/app/core/database.py`: added `"hide_parameters": True` to `engine_options`. All other engine options are unchanged (`pool_pre_ping`, SQLite `connect_args`, PostgreSQL pool settings). Messages now read `[SQL parameters hidden due to hide_parameters=True]`. The same flag also hides parameters from SQLAlchemy's SQL echo logging.
- This is the only application `create_engine` in `backend/app`. `backend/app/db/upgrade_p14_*.py` and `upgrade_p15_*.py` reuse this engine.

### Regression test
New `backend/tests/test_database_logging.py` (3 tests):
1. The application engine and `engine_options` have `hide_parameters` set to True.
2. Through the application `engine` and `SessionLocal` (in-memory SQLite forced by `conftest.py`), a unique-constraint violation with a canary `password_hash` value: neither `str(error)` nor `repr(error)` contains the value. The test skips if the engine is not SQLite, so it never writes to a real server.
3. Control: an engine without the flag does leak the value, which proves the canary check means something.

Results: **3 passed**. With the fix temporarily removed, 2 failed and the message showed `[parameters: ('pbkdf2-sha256$leak-canary-...',)]`. The fix was then restored.

### Full suite
`python -m pytest -q -p no:cacheprovider` from the worktree's `backend/`, with `PAMSU_TEST_DATABASE_URL` and `DATABASE_URL` unset (SQLite only), on `e444596` plus this change: **814 passed, 5 skipped, 0 failed** (11 min 33 s). That is the `dev` baseline of 811 passed and 5 skipped, plus the 3 new tests. The run used the main checkout's interpreter (`backend/venv`), because the worktree has no venv.

### Remaining risks / not verified
- No PostgreSQL run (neither 15 nor 18). `hide_parameters` is dialect-independent in SQLAlchemy 2.0, but psycopg error text was not checked.
- `backend/alembic/env.py` builds its own migration engine without the flag. It is left as is, because it runs migrations rather than requests. Data migrations with sensitive parameters would still print them if a migration fails.
- Test-only engines in `backend/tests` are unchanged. No test asserts on parameter text.
- Other log paths were not audited: application code that logs `str(exc)` from non-SQLAlchemy sources, and request or response body logging.
- The installed SQLAlchemy is 2.0.50, while `requirements.txt` pins 2.0.52.

### Branch status
- `claude/nice-faraday-a9cfcd`: was created at `main` `e271aa9`, whose backend does not import, then fast-forwarded to `dev` `e444596` (`--ff-only`, no merge commit). The fix, the test and this section are committed together and pushed to `origin/claude/nice-faraday-a9cfcd`. It is **not merged into `dev`**.
- `draft/admin-audit-action-types`: committed as `b661ed8` and pushed to origin, **not merged into `dev`**. Before merging, the owner must:
  - confirm the added `masterlist_imported` / `masterlist_import` audit types;
  - ideally run the PostgreSQL suites on PostgreSQL 15;
  - check the production `audit_records` constraints, read-only;
  - take a backup;
  - deploy migration `61330560eec5` together with its code.

### Next steps
1. Open and review PRs into `dev` for `claude/nice-faraday-a9cfcd` and for `draft/admin-audit-action-types`.
2. Then items 3–10 of "Full backend audit" → "Still open". They stay open; the backend audit is **not** complete.

## PR review, #31–#33 merges and follow-up security fixes (2026-10-19)

_Linux checkout, Python 3.14.8, SQLAlchemy 2.0.52 (the pinned version). No `.env` and no PostgreSQL server on this machine. No migration was applied anywhere, and no real database was touched. Handover notes are also in [this comment on #30](https://github.com/EsguerraJanuard/pamsu-python-ide/pull/30#issuecomment-6252988856)._

### PR state
| PR | Branch @ head | State |
|---|---|---|
| [#31](https://github.com/EsguerraJanuard/pamsu-python-ide/pull/31) SQL parameters hidden from errors | `claude/nice-faraday-a9cfcd` @ `d4ea382` | **Merged** into `dev` as `1796da3` (squash, by the owner). Same tree as the reviewed `d4ea382` |
| [#30](https://github.com/EsguerraJanuard/pamsu-python-ide/pull/30) admin audit logging | `draft/admin-audit-action-types` @ `b661ed8` | **Draft**, open. Since #31 it **conflicts with `dev` in `audit-status.md` only** |
| [#32](https://github.com/EsguerraJanuard/pamsu-python-ide/pull/32) login identifier | `fix/login-failed-identifier` @ `559d815` | **Merged** into `dev` as `ae276a3` (squash, by the owner). Same content as the reviewed `559d815` |
| [#33](https://github.com/EsguerraJanuard/pamsu-python-ide/pull/33) database error logging | `fix/db-error-log-details` @ `763bee2` | **Merged** into `dev` as `6a358d8` (squash, by the owner). Same content as the reviewed `763bee2` |

The only CI on these PRs is Vercel (frontend preview). **No CI runs the backend tests**; all results below are local.

### Review of #30 and #31 (before #31 was merged)
- **#31:**
  - `hide_parameters=True` was added, and every other engine option is unchanged.
  - The test goes through the application `engine` and `SessionLocal`, and a control case proves the canary assertion is meaningful.
  - The 2.0.50 vs 2.0.52 discrepancy came from the Windows venv. `hide_parameters` behaves the same in both, so no pin change.
- **#30:**
  - The code, the migration (parent `c25114413200`, superset lists, guarded downgrade) and the tests match its description.
  - **Finding:** a failed login stored the raw text of the email field. #30's new `resource_id`/`details` fields in `GET /admin/audit-logs` then showed it to admins. A scratch test (not committed) reproduced it: the username `my-secret-pass-123` was returned as both `resource_id` and `details.email`.
  - The cause is fixed by #32. Rows already stored can't be edited, so #30 must still hide them in the endpoint.
- **#30 PR changes:** title and description replaced (decisions, deploy order, read-only production SQL, the finding), and converted to Draft.

### Tests (full backend suite, SQLite)
| Tree | Result |
|---|---|
| `origin/dev` `e444596` (before #31) | 811 passed, 5 skipped, 0 failed |
| #31 `d4ea382` | 814 passed, 5 skipped, 0 failed |
| #30 `b661ed8` | 873 passed, 8 skipped, 0 failed; `alembic heads` = `61330560eec5` |
| Scratch merge of #30 + #31 (tracker conflict resolved by keeping both sections; never pushed) | 876 passed, 8 skipped, 0 failed; single head; `git diff --check` clean |
| #32 `559d815` | 834 passed, 5 skipped, 0 failed (814 + 20 new) |
| #33 `763bee2` | 819 passed, 5 skipped, 0 failed (814 + 5 new) |
| **`dev` `6a358d8`** (#31 + #32 + #33 merged) | **839 passed, 5 skipped, 0 failed** (814 + 20 + 5) |

**Mutation checks:**
- #32: with the old behaviour restored, its 7 unrecognized-input tests fail.
- #33: with the handler removed, 2 of its tests fail.

**Not run:** PostgreSQL of any version, so PostgreSQL 15 stays unverified.

### #32: never store unrecognized login identifiers
- **`routers/auth.py`:** a failed login keeps the identifier only if it is a well-formed university email: no extra `@`, no whitespace, at most 100 characters (the `resource_id` limit). Anything else is stored as `unrecognized`.
- **Unchanged:** unknown university emails and wrong passwords for existing accounts are recorded as before.
- **Logging:** an audit-write failure logs the exception class only. Before, `logger.exception` printed the text, which could echo the typed input; for example, any identifier over 100 characters failed validation and was logged.
- **Tests:** `tests/test_login_audit_identifier.py`.

### #33: unhandled database errors logged without their message
- **Problem:** `hide_parameters` doesn't remove the database's own error text. PostgreSQL's `DETAIL: Key (…)=(…)` and `Failing row contains (…)` can carry row values, including a password hash. Unhandled SQLAlchemy errors reached the default server handler, which logs the full traceback.
- **Fix:**
  - New `core/database_errors.py`, registered in `main.py` for `SQLAlchemyError`. It logs the error classes, SQLSTATE, constraint name, method, path and correlation ID, and returns `500 {"detail": "Internal server error."}`.
  - The submission dispatch failure log uses the same summary.
- **Tests:** `tests/test_database_error_logging.py`, with a psycopg-shaped error carrying a canary value.
- **Not covered:**
  - a real PostgreSQL run;
  - Celery task failure logs;
  - errors that application code catches and logs itself;
  - errors raised after a response has started.

### Integration
- **Conflicts:**
  - #32 and #33 didn't touch `audit-status.md`, and their code doesn't overlap with #30.
  - #30's only conflict is `audit-status.md`: every branch appended a section after the same line.
  - **Resolution:** keep every section in date order and delete only the conflict markers.
- **Order:**
  1. ~~#32 and #33~~: done.
  2. Update #30 from `dev`, resolve the tracker conflict, and add the endpoint masking of stored `login_failed` identifiers.
  3. Re-run the full suite and the PostgreSQL suites, on 15 if possible.
  4. Merge #30.
  5. Take a backup, run the read-only production check, then do a Render Manual Deploy.

### Still open
- **#30, before merge or deploy:**
  - confirm the `masterlist_imported`/`masterlist_import` types;
  - PostgreSQL 15 run;
  - read-only production check (`SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'audit_records'::regclass AND contype = 'c';`, expecting the baseline 20 action types and 7 resource types, plus `alembic_version` = `c25114413200`);
  - verified backup;
  - deploy order (`start.sh` runs `alembic upgrade head` before the API starts; the code must not run without the migration);
  - accounts that have logged in can only be deactivated, not deleted;
  - non-admin attempts on admin endpoints are not audited;
  - the admin UI doesn't show the target fields;
  - hide the `login_failed` identifiers already stored.
- **Backend audit "Still open" items 3–10:** unchanged, each needs a product decision. The backend audit is **not complete**.

### Next pending backend audit task
1. Finish #30 as listed above (#31, #32 and #33 are merged).
2. Then "Full backend audit" → "Still open" item 3: token revocation and rate limits fail open while Redis is down. Decide fail-open or fail-closed per route.
