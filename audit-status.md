# PAMS(U) IDE — Frontend Audit Status

_Last updated: 2026-10-21 (newest section at the end) · Branch: `dev` · This top section: base commit `b5f111f`_

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

## Redis outage fallback and #30 decisions (2026-10-19)

### #30 owner decisions (by Zithxnm, recorded in the #30 description)
- **Masterlist audit types:** keep `masterlist_imported` and `masterlist_import`.
- **Account deletion:** accepted. An account that has ever acted (for example, logged in) can only be deactivated. Real deletion (for example, anonymising) would be a separate design.
- **Non-admin 403 attempts on admin endpoints:** not audited for now. The request log already records them (path, status, time).
- **Also on #30 since the last section:**
  - `dev` merged in, and the `audit-status.md` conflict resolved by keeping every section (`3b27c52`);
  - stored `login_failed` identifiers masked in `GET /admin/audit-logs` (`ce86db6`);
  - full suite 904 passed, 8 skipped.
- **#30 remaining blockers:** a PostgreSQL 15 run, the read-only production check, and a verified backup. Then deploy (`start.sh` runs the migration).

### "Full backend audit" → "Still open" item 3: decided and implemented
**Decision (Zithxnm):** in-memory fallback. Neither fail-open (the old behaviour) nor fail-closed.
- **Fail-open, before:** while Upstash was unreachable, every rate limit was off. That meant unlimited password guessing and password-reset-code guessing, and email flooding. A token that logged out during the outage also kept working until it expired (30 min by default).
- **Fail-closed, rejected:** nobody could log in or reset a password during an outage, and with revocation every authenticated request would fail.

**Change** (branch `fix/redis-outage-fallback`):
- **New `core/memory_fallback.py`:**
  - a thread-safe store whose entries expire;
  - capped at 100,000 keys: expired keys are dropped first, then the oldest;
  - keys are the same hashed keys as in Redis, so no raw emails are kept.
- **`core/rate_limit.py`:** if Redis fails, the request is counted in memory, and the same limits apply. The warning now says "counting in memory".
- **New `core/token_revocation.py`**, used by `get_current_user` and `/logout`:
  - every logout is kept in memory until the token expires, as well as in Redis;
  - a token logged out before or during an outage stays rejected, even if Redis comes back without the key;
  - if Redis is down, only memory is checked, with a warning.
- **Why memory is enough:** `start.sh` runs Uvicorn as one process, so in-memory counts cover the whole Render deployment. They reset when it restarts.
- **Unaffected:** password resets and deactivation are checked in the database.

**Tests:**
- New `tests/test_redis_outage_fallback.py` (8 tests). The test suite runs with Redis unreachable, so these exercise the real fallback paths:
  - the login limit gives a 429 on the 11th try;
  - limits are kept per identifier;
  - logout → 401 with Redis down;
  - a memory revocation survives an empty Redis;
  - Redis is still written and read when it's up;
  - the store's window expiry and size cap.
- `conftest.py` now empties both memory stores around every test.
- `test_rate_limit_is_per_identifier_and_fails_open` became `…_falls_back_to_memory`.
- **Mutation check:** with both fallbacks switched off (back to fail-open), 4 tests fail.
- **Full SQLite suite:** 847 passed, 5 skipped, 0 failed (839 + 8).
- **Not verified:** a real Upstash outage, and multiple Uvicorn workers. The fallback is per process; if the API ever runs several workers, each worker counts separately.

### Next pending backend audit task
1. #30: PostgreSQL 15, the production check, the backup, then merge and deploy.
2. "Still open" item 4: guest accounts. Unlimited creation behind the shared proxy IP, no cleanup, they can join any class whose code they know, and the sandbox class belongs to whichever instructor comes first. This needs product decisions.

## Guest accounts (2026-10-19)

"Full backend audit" → "Still open" **item 4: decided and implemented** (branch `fix/guest-account-limits`). Item 3, the Redis outage fallback, is merged as #35.

### What was wrong
- **Self-service guests** ("Continue as Guest Student" on the login page) were only limited to 2 per minute per IP. On Render that is effectively one shared bucket: up to about 2,800 accounts a day, and one person could block guest access for everyone.
- Each guest cost a bcrypt hash.
- Guests could join any real class whose code they knew, and use Judge0 there.
- Guests were never cleaned up, and the admin user list hid them.
- The sandbox class was owned by whichever instructor or admin row came first, so it appeared in a random instructor's dashboard. Two simultaneous first guests could both try to create it.
- A guest's 6-hex-character id could collide.

### Owner decisions (Zithxnm)
1. Keep the public guest button, with a **daily cap**.
2. Guests are **sandbox only**: no joining real classes.
3. Guests are **deactivated 7 days** after creation (never deleted).
4. The sandbox class is **owned by an admin**.

**Scope:** these rules apply to **self-service guests** only: role student, `guest_…@pampangastateu.edu.ph`, school ID `GST…`. Guests an admin creates through `POST /admin/guests` keep the normal student rules.

### Change
- **New `services/guest_service.py`:**
  - **Daily cap:** `GUEST_DAILY_LIMIT = 100` new self-service guests per rolling 24 hours. It's counted in the database, so it holds even while Redis is down. Beyond it, `/guest` returns 429 with a message the login page already shows.
  - **Guest creation:** a 12-hex id, an unused `GST` school ID, and an unusable password marker (no bcrypt cost).
  - **Sandbox:**
    - owned by the first active admin; created on first use, and safe against two guests arriving at once;
    - **an existing sandbox owned by an instructor is moved to an admin** on the next guest sign-in, with a `classroom_updated` audit record (actor: system);
    - with no active admin, no sandbox is created, and the guest still gets a session.
- **`POST /classrooms/join`:** self-service guests get 403.
- **`get_current_user`:** a self-service guest older than 7 days gets 403 ("This guest account has expired…").
- **`/guest`:** each new guest sign-in also deactivates expired guests in one `UPDATE`. They are deactivated, not deleted, so their history remains. This deactivation is not written to the audit log.
- **`GET /admin/users`:** new `include_guests` option (default `false`, as before) and a stable `user_id` order. The guest filter now matches only self-service guests; the old `startswith("guest_")` treated `_` as a wildcard.

### Tests
- **New `tests/test_guest_accounts.py` (14):** guest identity; no usable password; the daily cap counted per rolling 24 hours (only self-service guests) and the 429 response; join refused for guests but allowed for students and admin-created guests; 7-day expiry, with older non-guest accounts unaffected; the deactivation sweep; sandbox ownership, moving an existing sandbox with its audit record, and no admin; and the admin list option.
- `test_guest_login_enrolls_into_sandbox` updated to the admin-owned rule.
- **Mutation checks:** switching off each rule (cap, join block, expiry, sweep, admin owner) makes its own test fail.
- **Full SQLite suite:** 861 passed, 5 skipped, 0 failed (847 + 14).
- **Not tested:** two guests creating the sandbox at the same moment. That code path catches the unique-constraint error and re-reads the class.

### Follow-ups
- **Admin UI:** a "show guests" toggle using `include_guests=true`.
- **Production sandbox:** the move to an admin happens on the first guest sign-in after deploy. It needs at least one active admin.

### Next pending backend audit task
1. **#30:** PostgreSQL 15, the production check, the backup, then merge and deploy.
2. **"Still open" item 5:** `POST /practice/tasks/{id}/submit` waits on Judge0 synchronously (up to 15 s), against the AGENTS.md 3-second rule.

## Items 5 and 8 (2026-10-19)

Item 4 (guest accounts) is merged as #36.

### Item 5: practice submit waits on Judge0: deferred until after #30 (owner decision, Zithxnm)
- **Today:** `POST /practice/tasks/{id}/submit` keeps the request open while Judge0 runs (`wait=true`, up to 15 s). The AGENTS.md 3-second rule says longer requests are cut off, and the student then sees "Could not reach the server".
- **Agreed fix:** run it the way the IDE's Run button does. Submit returns at once; Judge0 runs in the background and calls back; the page polls. The response should also return the `attempt_id`, which item 6 (AI hint) needs.
- **Why it waits:**
  - A practice attempt has no "pending" state (`is_successful` is NOT NULL), so the fix needs a migration that adds a status column to `practice_attempts`.
  - That migration must be chained after #30's `61330560eec5`. Two migrations from the same parent leave two Alembic heads, and `start.sh` (`alembic upgrade head`) fails on deploy.
- **Rejected alternatives:**
  - polling Judge0 directly: each check is a paid RapidAPI request;
  - giving existing columns a "pending" meaning: that would distort the practice statistics.

### Item 8: default AST strictness: decided and implemented (#37)
- **Before:** the admin "Default AST strictness" setting was saved but never read. Practice-module checks always used "moderate".
- **Owner decision (Zithxnm):** the setting is the starting level of new instructor accounts and the level used where no instructor applies. Existing instructors keep their own level. No migration.
- **Change:**
  - `get_default_ast_strictness()`, with "moderate" for an unknown stored value;
  - used by `POST /admin/instructors`, practice submit, and the missing-instructor fallback in activity analysis and evaluation;
  - the admin help text was updated.
- **Tests:** `tests/test_default_ast_strictness.py` (9, including the first practice-submit tests, with a fake Judge0). With hard-coded "moderate" restored in practice or in instructor creation, its test fails.
- **Results:**
  - full SQLite suite 856 passed, 5 skipped on its own;
  - a scratch merge of #30 + #36 + #37 gave 935 passed, 8 skipped, with a single head;
  - frontend lint and build pass.

### Next pending backend audit task
1. **#30:** PostgreSQL 15, the production check and the backup, then merge and deploy.
2. **Item 5**, right after #30 merges (migration chained after `61330560eec5`).
3. **Items with no migration still open:**
   - 6: AI tutor dependency and wiring;
   - 7: legacy `POST /execution/submissions/`;
   - 9: retakes, enrollment decisions, instructor temporary-password email;
   - 10: `rediss://` certificate checks.

## Deployment branch and ownership verification (2026-10-19)

_Read-only verification: nothing was pushed, merged, deployed or migrated. No Vercel or Render setting was read or changed. No `.env` was read. Evidence: GitHub deployment records (`gh api …/deployments`), Git history, and unauthenticated read-only requests to the public backend (`GET /health`, `GET /`, `GET /ready`, and CORS preflights to `/health`)._

### Ownership (reported by the owner)
- GitHub repository: owner (EsguerraJanuard).
- Vercel (frontend): owner.
- Render (backend `pamsu-backend`): Errol's account. Not accessed.
- Integration branch: `dev`.

### Frontend (Vercel)
- **Verified (GitHub deployment records, created by `vercel[bot]`):** Production deployment `7159090118` = `3e8fa3f` (`origin/dev` tip, #37), state `success`, 2026-10-18T18:49:40Z.
- **Verified (pattern):** since 2026-10-08T09:00Z, every Production deployment is a `dev` commit that isn't on `main`. The last Production deployment of the `main` tip (`e271aa9`) was 2026-10-08T08:34Z. Feature branches get only Preview deployments. This is consistent with the Vercel Production Branch being `dev`. The Vercel project setting itself wasn't read (no Vercel CLI or token here). The owner can confirm it under Project → Settings → Git.
- **Note:** two Production deployments on 2026-10-13 (`6086b26`, `e9db143`) are commits that are no longer on any branch, so `dev` history was rewritten that day.
- **API URL:** `frontend/.env.production` (tracked) sets `VITE_API_BASE_URL` to `https://pamsu-backend.onrender.com`. Whether a Vercel environment variable overrides it is **unverified**.

### Backend (Render)
- **Reported (stale):** `errol_final_deployment_steps.md` says Render deploys from `main`.
- **Verified (behaviour of the live service):** the production backend answers CORS preflights for `https://pamsu-python-ide.vercel.app` and **rejects** an unrelated `*.vercel.app` origin (400). `main`'s code (`e271aa9`) allows every `*.vercel.app` origin. The narrowed rule exists only from `e946455` (2026-10-17, `dev`) onward. **So the live backend isn't running `main`'s code. It runs a commit at or after `e946455`, consistent with Render deploying `dev`.**
- **Unverified:** the configured Render branch, the exact live commit (anywhere from `e946455` to `3e8fa3f`), whether auto-deploy is on, the start command, and the health-check path. `/health` and `/` report only version `1.0.0`, the same on every branch.
- **`/ready` returns 503:** `execution_partner_auth` is not configured (`PAMSU_PARTNER_EXECUTION_TOKEN` isn't set on Render, and `render.yaml` doesn't declare it). It gates only `/internal/partner-results`; Judge0 callbacks don't use it. `database` reports ready.
- **Cold start:** the first `/health` took 62 s (free tier, spun down). The frontend's request timeout is 15 s.

### Database revision
- **Inferred, not verified:** every commit from `e946455` to `3e8fa3f` has the single head `c25114413200`. `render.yaml` starts the service with `bash start.sh`, which runs `alembic upgrade head` under `set -e` before Uvicorn. If Render uses that start command, the healthy service implies production is at `c25114413200`. Confirm with the read-only query below.

### Frontend / backend compatibility
- Frontend changes after `e946455`: theme work (`1a80b09`, `f0bc529`, `50bc701`) and #37's admin help text. None needs a newer backend contract, so the deployed frontend works with any backend commit in that range.
- If the live backend predates `3e8fa3f`, the admin help text describes #37 behaviour the backend doesn't have yet.

### Not yet in production (verified from Git; deploy status as above)
- #30 (`draft/admin-audit-action-types` @ `ce86db6`, Draft) is on no deployed branch, so migration `61330560eec5` is in no deployed code.
- #31–#37 are on `dev`. Whether the live backend includes all of them depends on its exact commit (unverified).

### Deployment risks for pending PRs
1. **If Render auto-deploys `dev`, merging #30 is the production deploy.** `start.sh` applies `61330560eec5` on the next start. The backup and the read-only production check must happen **before the merge**, not just before a "deploy".
2. **Vercel previews use the production backend.** Preview builds read `.env.production`, and the backend's CORS rule allows `pamsu-python-ide-*.vercel.app`. Testing a PR preview reads and writes production data.
3. **Version skew on merge:** Vercel deploys within about a minute of a push to `dev`, and Render deploys separately. #30 doesn't change the frontend. Item 5 will change both (asynchronous submit plus polling), so deploy its backend first or merge it when the skew is acceptable.
4. **`main` is not deployable:** its Alembic graph fails (`333fed79e9f7` missing), and it still has `GET /admin/seed-production`. Don't point Render at `main`.
5. **Credential in the repository:** `errol_final_deployment_steps.md` (tracked on `dev`) contains a plaintext production admin password. Rotate it and remove the file from future commits.

### Manual checks for Errol (Render dashboard, read-only)
1. Service `pamsu-backend`: **Settings → Build & Deploy → Branch** (expected `dev`), and **Auto-Deploy** (On / Off / After CI checks).
2. **Events / Deploys:** the latest *successful* ("Live") deploy, with its full commit SHA, branch and time, and any later failed deploys.
3. **Settings:** Root Directory (`backend`), Build Command, **Start Command** (expected `bash start.sh`), Docker or Python runtime, and **Health Check Path** (should be `/health`, not `/ready`).
4. **Logs of the live deploy:** the `Running database migrations...` line, and that `alembic upgrade head` finished without error.
5. **Environment:** only that `PAMSU_ENVIRONMENT` is production and `PAMSU_CORS_ALLOWED_ORIGINS` is set (don't share values). Also whether `PAMSU_PARTNER_EXECUTION_TOKEN` is intended to be set.
6. **Read-only SQL on the production database** (Supabase SQL editor):
   `SELECT version_num FROM alembic_version;` (expect `c25114413200`) and
   `SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'audit_records'::regclass AND contype = 'c';` (expect the baseline 20 action types and 7 resource types).
7. **Whether a verified, restorable Supabase backup exists** (date and how it was checked).

### Status
The backend audit is **not complete**. This section changes no priorities: #30 (PostgreSQL 15, production check, backup, then merge) remains first. Item 5 follows #30 (migration chained after `61330560eec5`). Items 6, 7, 9 and 10 remain open.

## Release readiness and #30 deferral (2026-10-20)

_Main checkout `dev` @ `b62e225` (local; 1 commit ahead of `origin/dev` `3e8fa3f`, and that commit changes only this file). Prepared at the owner's request for one commit containing this section and the deletion of `errol_final_deployment_steps.md`; the owner commits and pushes. Nothing was committed, pushed, merged, deployed or migrated by this session. No credential was printed or changed._

### Verdict
**Not production-ready yet.** The release code passes its automated tests. But the credential exposure is still open, and no critical workflow has been verified in production. Don't call it production-ready until every blocker below is closed.

### Owner decision: #30 deferred
- PR #30 (admin audit logging) and migration `61330560eec5` are **deferred until after Wednesday's release** (owner, 2026-10-20). Not merged, pushed, deployed or applied.
- **State kept:**
  - GitHub head `ce86db6`, Draft.
  - Worktree `../pamsu-python-ide-admin-audit-draft` at `2dfe381`, **6 commits ahead, unpushed:** `5c47e24` (merge of `dev`), `19de347` (docs), `2dfe381` (masks all-digit login identifiers).
- **Reconsider after delivery**, once:
  - the production revision and `audit_records` constraints are confirmed;
  - a verified backup exists;
  - PostgreSQL 15 is tested, or the risk is accepted in writing;
  - the 6 commits are pushed;
  - a full suite passes on the exact merge commit.
- **Test evidence for `2dfe381`:** the reconciliation session's run (2026-10-19, 00:57–01:11Z) gave 936 passed, 8 skipped, exit 0. The run didn't record its SHA. It's attributed to `2dfe381` because the commit was made 7 minutes before the run and the tree hasn't changed since, the 8 skips match #30's PostgreSQL-only tests, and `2dfe381` adds one test.

### Release candidate and test evidence
| Check | Result |
|---|---|
| Full backend suite on the release code (`3e8fa3f`, run from `b62e225`) | **870 passed, 5 skipped, 0 failed** (14 min 20 s; 2026-10-20 02:22–02:37Z; Windows) |
| Test environment | Isolated: in-memory SQLite; `DATABASE_URL`, `PAMSU_TEST_DATABASE_URL` and `REDIS_URL` unset; Redis unreachable; SMTP blanked and Celery stubbed by `conftest.py` |
| Skipped | **The 5 PostgreSQL-only suites:** `test_alembic_migrations` and the execution-idempotency, grade, partner-execution and submission concurrency suites. No PostgreSQL run (15 or 18) exists for this commit |
| Frontend `npm run lint` (2026-10-19, same frontend) | Pass |
| Vercel Production | `3e8fa3f`, success (GitHub deployment record) |
| Live backend (unauthenticated read-only checks, 2026-10-20) | `/health` returns 200 after a 62 s cold start. An unrelated `*.vercel.app` origin is rejected (400), so production runs `dev` code at or after `e946455`. The exact commit is unverified |

**The automated tests stub SMTP, Redis, Celery and Judge0. They are not production verification.**

### Email delivery: can it work in production?
The smoke test expects password-reset and account-setup emails to arrive, so the code was traced:
- **`/ready` gives no evidence either way.** `otp_email_adapter: contract_only` is a hard-coded entry in `readiness_check` (`main.py`). It never inspects the SMTP settings.
- **Password reset** (`/users/password-reset/start` and `/resend`):
  - `get_otp_delivery_adapter` (`integrations/otp_delivery.py`) uses SMTP only when `SMTP_HOST`, `SMTP_USER` and `SMTP_PASS` are **all** set.
  - Otherwise it picks `UnavailableOTPDeliveryAdapter`, which always fails.
  - The sender is `SMTP_SENDER_EMAIL`, falling back to `SMTP_USER`.
- **Account-setup emails** (`email_service.send_provisioning_email`):
  - sent by the masterlist import (one per created student) and by instructor creation; `POST /admin/students` sends none;
  - need only `SMTP_USER` and `SMTP_PASS`;
  - the host defaults to `smtp-relay.brevo.com`, and the sender to `noreply@pampangastateu.edu.ph`.
- **Failures are invisible to users.** Both paths send in a background task after the response. Reset always answers "If an account exists with this email, a verification code has been sent.", and a failed send is only logged. **A success message in the UI is not evidence. Only a received email is.**
- **Email works in production only if all of these hold:**
  - `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` and `SMTP_SENDER_EMAIL` are all set on Render;
  - the Brevo account accepts the sender. The two paths default to different senders, so setting `SMTP_SENDER_EMAIL` explicitly matters;
  - the rotated key is in place;
  - Render allows outbound connections to the relay on port 587. **Unverified:** check Render's current outbound-SMTP rules for this instance plan, and the logs.
- **Impact:** masterlist students have no password. They can sign in only after a reset email, so without working email they can't sign in at all.
- `render.yaml` declares no SMTP variable. None of the above is verified in production.

### Release blockers
| # | Blocker | Owner | Status |
|---|---|---|---|
| 1 | Rotate the production admin password. It was in plaintext in `errol_final_deployment_steps.md`. That file is still at the tip of `main`, the repository's default branch, so it shows on the GitHub front page, and it's in every branch's history. Change it while signed in as that admin, through `PATCH /users/me/password`. **Don't use "Forgot password?" for this account** (see "Admin accounts" below) | Errol (requested 2026-10-20) or owner | **Pending at time of writing** |
| 2 | Rotate the SMTP/Brevo key, coordinating the Render variable update and any deploy it triggers | Errol + owner | **Pending: not confirmed** |
| 3 | Render configuration: branch, auto-deploy, live commit, start command, health-check path; environment variables reported as set/not set, including the four SMTP variables and an accepted sender | Errol | Pending |
| 4 | Production database (read-only): PostgreSQL version and `alembic_version` (expected `c25114413200`, inferred, not verified) | Errol | Pending |
| 5 | A verified, restorable production backup | Errol | Pending |
| 6 | Production smoke test (below), with Errol watching the logs | Owner + Errol | **Pending: never run** |
| 7 | Remove `errol_final_deployment_steps.md`. It was also out of date: it described merging `dev` into `main`, the old split-name migration, and the removed `seed-production` route. Nothing else referenced it | Owner | **Deleted from `dev` by the commit that adds this section.** It's still at the tip of `main` and in every earlier commit, so rotation (item 1) is the fix. Removing it from `main` needs a separate decision once Render's branch is confirmed (item 3). Rewriting public history isn't recommended before delivery |
| 8 | Errol's laptop shut down mid-session, and nothing reached GitHub after 2026-10-18 18:49Z. He should report `git status`, stashes and unpushed commits before redoing anything | Errol | Unknown |

The checklist for Errol is drafted but **not sent**.

**What this push changes in production:** it carries only this file and the deletion, with no application code and no migration.
- Vercel builds a new Production deployment with the same frontend.
- If Render auto-deploys `dev`, the backend restarts on the same code, and `alembic upgrade head` has nothing new to apply.
- If auto-deploy is off, Render doesn't change.

### Public history scan (2026-10-20; names and counts only, no values)
- **No `.env` or key file was ever committed** on any branch.
- **No Brevo key, Redis URL with a password, or Google API key** appears in any commit.
- **Database URLs with passwords** appear only in removed root helper scripts (`check_db*.py`, `check_admin*.py`; removed in `0eb9c17`) and in Docker setup:
  - they point to `localhost` (the local development PostgreSQL superuser) or to compose placeholders;
  - none points to production;
  - change the local PostgreSQL password if it's used anywhere else.
- **`JWT_SECRET_KEY` in `.env.example`** is a placeholder. `render.yaml` has Render generate the production value (`generateValue: true`).
- **The only production credential found in public history is the admin password (item 1).** The SMTP key was exposed in session output, not in the repository.

### Admin accounts: finding and recommendation
**Finding.** The production admin is a demonstration account, made before the project moved to Claude.
- **Its email is a generic role address on the university's real email domain**, not a named person's mailbox. That address may be a real mailbox run by someone outside the project. Because "Forgot password?" sends the reset code to the account's email:
  - using "Forgot password?" on this account could hand a code to that mailbox's owner;
  - if the mailbox exists, its owner could take over the production admin account.
- **There's no other way to change an admin password in the app.** The admin dashboard has no "change my password" form, and `GET /admin/users` leaves out admin accounts. So for now, the password can only be changed while signed in as the admin, through `PATCH /users/me/password`.
- **No endpoint creates or grants the admin role.** Only `backend/seed_admin.py` does, and it needs database access. It also makes the person running it choose the admin's password (`ADMIN_PASSWORD`).

**Rules for real MIS/admin accounts** (the system will hold College of Computing Studies student records):
- **One account per named person, on their own university mailbox.** No shared or generic role addresses: whoever runs that mailbox controls the account, and actions can't be traced to a person.
- **Only the person knows their password.** Never set by someone else, and never in files, chat or the repository.
- **Two or three active admins,** so nobody gets locked out. Deactivate an account when its owner leaves the role.
- **Record admin actions** (PR #30). Under the Data Privacy Act (RA 10173), access to student records should be accountable and logged.

**Recommendation (owner decision pending; not implemented):**
- **Approach: pre-provision each admin account with no usable password,** and have the person set one through "Forgot password?" on their own mailbox.
  - This is how masterlist students already work, and it's tested.
  - The admin account itself works as the allowlist entry. Only the real mailbox owner can activate it.
  - A separate admin allowlist that turns into an account on first sign-in would need the retired registration flow back (an `InstructorAllowlist` table from that flow still exists). It gives no extra protection.
- **Order of work:**

| When | Step | Owner |
|---|---|---|
| Before delivery | Change the demonstration admin's password while signed in (blocker 1) | Errol or owner |
| After delivery | Create named admin accounts for the MIS staff, then deactivate the demonstration admin. It can't be deleted once it has records | Errol (database access) |
| After delivery | Change `seed_admin.py` to create the account with no usable password and send a setup email, instead of taking `ADMIN_PASSWORD` | Code change, needs approval |
| Before university rollout | Admin-only "Manage administrators" screen: add or deactivate admins, never your own account, at least two active. Plus PR #30's audit logging and an admin "change my password" form | Code change, needs approval |
| Long term | Sign-in through the university's own accounts (Google Workspace or Microsoft 365) with multi-factor authentication. Needs university IT's cooperation | Owner + university IT |

### Production smoke test (planned, not run)
**Rules:**
- Use test accounts only, and write down every record created.
- Don't test on Vercel preview URLs.
- Stop on a critical failure. Don't hot-fix on `dev`: a push may redeploy production.

**Steps:**
0. Warm up the backend: `/health` returns 200.
1. Sign in as student, instructor and admin; a wrong password is refused.
2. "Forgot password?" for a test student: **the email arrives**, the code works, and the new password signs in.
3. Masterlist import of one test row: **the setup email arrives** with no credential in it. Then do step 2 for that student.
4. The instructor publishes a test activity and enrolls the test student.
5. Workspace **Run**: output appears, and it isn't stuck at "queued" or "queue unavailable". Errol sees the Celery task and the Judge0 callback in the logs.
6. **Submit**: the submission is saved and listed, and background evaluation completes.
7. Practice submit: a result within 15 s.
8. Grading Bench: grade, save, release. The student sees the grade and a notification.
9. Log out: the old session is rejected.
10. Optional: guest sign-in lands in the sandbox only (needs an active admin).

### Next
1. Errol changes the admin password (requested 2026-10-20). This commit doesn't wait for that. The file is already in plain view at the tip of `main`, so this section adds no exposure, and the commit removes the file from `dev`.
2. Errol and the owner rotate the SMTP key. Send Errol the checklist, and collect blockers 3, 4, 5 and 8.
3. Run the smoke test. Declare the release production-ready only once blockers 1–6 are closed. Record the results in a new dated section.
4. After delivery: decide how admin accounts are provisioned (see "Admin accounts"), then replace the demonstration admin with named accounts.

## Panel requirements: verification and fixes (2026-10-20, code complete, NOT committed or deployed)

### Overall progress
- **Verification:** every request in the oral-defense form (FORM-23, 2026-09-30: De Leon, Mallari, Dungo; plus the adviser's requests) was checked against the code at `c58a059`. Most of the Antigravity checklist's "critical" items were already fixed (AST rule-key aliases, practice IDOR, bulk-enroll regex, registration toggle, name crashes, guest crashes, hardcoded passwords, seed backdoor, JTI logout, CORS, `ws://localhost`, color violations).
- **Owner decisions (2026-10-20):** faculty lockout only (no login OTP); new task fields via migration; per-student retake using the existing `retake_allowed` column; suggested score prefilled in the Grading Bench (the instructor still saves and releases the grade; no automatic grade).
- **Status:** every gap below is implemented, tested and checked in the browser. Nothing is committed, pushed or deployed.

### What changed, per panel request
- **Isolated workspace (Dungo):**
  - Drafts are keyed `pamsu-workspace-draft-u<userId>-<activityId>`.
  - Explicit sign-out removes every draft; the sign-out dialog now says so.
  - A 401 expiry keeps the user's own drafts.
  - Legacy unscoped drafts are deleted at sign-in.
  - The workspace remounts per account.
- **AST full score (Dungo) → suggested score:**
  - The Grading Bench pre-fills round(100 × found ÷ required) and explains it. The instructor still saves and releases the official grade.
  - **Pre-existing bug fixed:** the Grading Bench read only the `ast_findings` table, which no code ever fills. Its "Structure check (AST)" therefore always said "no required structures". It now falls back to the evaluator's own `ast_analyses[].details.findings` and shows found and needed counts.
- **Automatic difficulty and construct analysis (Mallari, De Leon):**
  - `POST /instructors/tasks/analyze-solution` accepts `reference_code`, `description` or both (422 when both are blank). It returns `difficulty_level`, `difficulty_reason`, `suggested_ast_rules` and `constructs` (source and matched phrases).
  - Solution counts reuse the evaluator's detectors. Difficulty is the highest level among the constructs found, with the same levels as the editor categories (`frontend/src/utils/astRules.js`, `RULE_LEVELS` in `ast_analyzer.py`). When a solution is given, it alone sets the difficulty.
  - The activity editor's "Analyze the activity" panel sends the description, scenario, instructions and optional solution. It auto-applies the difficulty and rules, lists the reasons, and skips rules above the level with a note.
- **Advanced requirements (adviser):** a "Required at least N" stepper (1–20) under each checked rule. Activity details, the workspace and the grading bench show the counts.
- **Scenario and solution explanation (De Leon):**
  - New columns `tasks.scenario` and `tasks.solution_explanation` (migration `5e8a1c7d9b42`).
  - The editor has both fields. The activity page and the student workspace show the scenario.
  - Students see the explanation ("How the solution works") on their submission only after their grade is released.
  - The workspace now also shows the problem description; it used to show only the instructions.
- **Editing due dates and reminders (Mallari):**
  - The activity editor has an edit mode at `/instructor/activities/:id/edit`, reached from an "Edit activity" button. It PATCHes only the changed fields; the audit showed `changed_fields: ['due_at']`.
  - When a published activity's deadline moves, students get a "Deadline changed" notification.
  - Due-soon reminders ("Deadline in less than 24 hours") are created when a student reads notifications or the unread count. There is one per unsubmitted published activity, idempotent per deadline. Render has no scheduler, which is why it works this way.
- **Retake or republish (Dungo):**
  - "Allow another attempt" in the Grading Bench calls `POST /instructors/submissions/{id}/retake`. It is owner only, idempotent, audited as `submission_status_changed`, and the student is notified.
  - One late attempt through `/submissions/` is allowed; it becomes official and uses up the allowance. Attempts before the deadline stay unlimited and do not use it up.
  - Students see a notice on their submission, and the activity card shows "Submit another attempt".
  - The legacy `/execution/submissions/` route stays deadline-strict.
  - Moving the deadline in edit mode reopens the whole activity.
- **Faculty login security (De Leon):**
  - An instructor or admin account with 5 failed logins in 15 minutes gets 423 Locked, with `Retry-After` and a message the login page shows.
  - The lock is checked before the password. Locked attempts are audited as `login_failed`/`denied` and don't extend the lock.
  - The count comes from audit records (works with Redis down). Students are unaffected.
- **Middle name (Mallari):** an optional Middle name field in the admin create-faculty and create-student forms (stacked fields). `full_name` joins first, middle and last, with a 150-character limit. Storage is still the single `users.name` column.
- **PSU naming (Mallari):** "PAMSU" became "PSU Python IDE" or "Pampanga State University" in the visible text:
  - the tab title, PWA manifest, sidebar and error page;
  - the API error messages and the OpenAPI title;
  - the welcome and OTP emails (the OTP heading is now maroon and gold, not emerald).

  Internal `PAMSU_*` env vars and `pamsu_*` storage keys are unchanged on purpose. The production `SMTP_SENDER_NAME` env var on Render may still say "PAMSU" and must be checked there.
- **Label and text size (Mallari):** `.field-label` is now 14 px in the main text color (was 12 px muted), and badges are 12 px (was 11 px). All 9–10 px text became 11–12 px, and editor labels are `text-sm`.
- **Submit gating (De Leon):**
  - The Create/Save button is disabled until a title, a class and a difficulty are set, with a hint naming what is missing.
  - The workspace Submit is disabled while the code is only comments or the untouched starter code.

### Files modified (tracked)
- Backend:
  - `app/integrations/otp_delivery.py`, `app/main.py`, `app/models/domain_models.py`
  - `app/routers/admin.py`, `auth.py`, `instructor.py`, `notifications.py`, `registration.py`
  - `app/schemas/evaluation_schema.py`, `notification_schema.py`, `submission_schema.py`, `task_schema.py`
  - `app/services/academic_event_service.py`, `ast_analyzer.py`, `email_service.py`, `evaluation_service.py`, `submission_service.py`, `task_service.py`
  - `tests/conftest.py`, `tests/test_task_openapi_contracts.py`
- Frontend:
  - `index.html`, `vite.config.js`, `src/App.jsx`, `src/index.css`, `src/services/api.js`
  - `src/components/ErrorBoundary.jsx`, `src/components/layout/AppSidebar.jsx`, `src/components/layout/SignOutModal.jsx`
  - `src/features/admin/AdminDashboard.jsx`
  - `src/features/auth/AuthContext.jsx`, `ForgotPassword.jsx`, `Login.jsx`, `Register.jsx`
  - `src/features/instructor/ActivityDetails.jsx`, `ActivityEditor.jsx`, `LiveMonitoring.jsx`, `PracticeModuleManager.jsx`, `grading/SplitPaneGradingWorkspace.jsx`
  - `src/features/student/ActivityCard.jsx`, `studentData.js`
  - `src/features/submissions/SubmissionDetails.jsx`
  - `src/features/workspace/Workspace.jsx`
- `audit-status.md`

### Files created (untracked: must be added explicitly, or the build and backend break)
- `backend/alembic/versions/5e8a1c7d9b42_activity_guidance_and_deadline_reminders.py` (the ORM maps the new columns, so the backend needs this migration)
- `backend/app/services/login_security_service.py` (imported by `auth.py`)
- `backend/tests/test_panel_recommendations.py` (17 tests)
- `frontend/src/features/workspace/draftStorage.js` (imported by `Workspace.jsx` and `AuthContext.jsx`)
- `frontend/src/utils/astRules.js` (imported by the editor, details, practice, grading and workspace pages)

### Verification
- **Backend, full suite:** **885 passed, 5 skipped, 0 failed** (14 min 24 s, SQLite). Two cases were deselected (`test_pathological_code_is_reported_not_crashing`, Windows-only env-var length). The baseline at `c58a059` was 868 passed; the 17 new tests account for the difference.
- **New tests:** `tests/test_panel_recommendations.py`, 17 passed, covering the analyzer, scenario and explanation privacy, deadline-change notifications, due-soon reminders, retake, faculty lockout and middle name.
- **Migration:** `tests/test_alembic_migrations.py` against the local PostgreSQL server: 3 passed (upgrade, downgrade, re-upgrade of `5e8a1c7d9b42`). The test used its own temporary database; `pamsu_ide_db` was not touched. Only PostgreSQL 18.4 is available here, not the PG15 target.
- **Frontend:** `npm run lint` clean, `npm run build` OK.
- **Browser walkthrough:** a throwaway SQLite copy in the session scratchpad, with email, Redis and Judge0 blanked; `qa/.qa-data` was not touched. Verified:
  - the analyzer from the description, then with a reference solution;
  - the min-count stepper (for loop ×2);
  - create and publish with scenario and explanation;
  - edit the deadline: only `due_at` was sent, and the student got "Deadline changed";
  - two students on one browser after a session expiry: no draft leak;
  - sign-out clears all drafts;
  - Submit is disabled on the comment-only template;
  - a submission evaluated (run directly, since Celery is down locally), then the Grading Bench showed the per-rule found/needed counts and a suggested score of 29 (2 of 7);
  - grade released, after which the student saw the explanation;
  - deadline closed, then "Allow another attempt" with badge, notice and notification; the late attempt was accepted and the allowance used up;
  - a due-soon reminder for the student who had not submitted;
  - admin created "Ana Santos Reyes" with a middle name;
  - 5 wrong passwords then the correct one showed the lockout message.
- **Known and unchanged:** the Monaco DiffEditor "TextModel got disposed" console error when leaving the grading page (pre-existing). A one-off React "uncontrolled to controlled input" warning appeared once during scripted input and could not be reproduced on a fresh load or in normal use.

### Deployment notes (read before pushing)
- `start.sh` runs `alembic upgrade head` on Render, so pushing to `dev` applies `5e8a1c7d9b42` to production on the next deploy. It adds two nullable columns and widens one check constraint; there is no data backfill.
- PR #30's migration `61330560eec5` also revises `c25114413200`. Before #30 merges, its `down_revision` must be changed to `5e8a1c7d9b42` (or a merge migration added).
- Production still needs the end-to-end smoke test from the release handover. Production evaluation runs through Celery and Redis, which the local walkthrough could not exercise.

### Pending tasks / next steps
1. Commit and push (the user runs the commands), then smoke-test production. Check: create with the analyzer, the edit-deadline notification, a submission evaluated by Celery showing the structure check and suggested score, retake, reminder, faculty lockout, and the admin middle name.
2. Check the Render env `SMTP_SENDER_NAME` (it may still say "PAMSU").
3. Re-point PR #30's migration onto `5e8a1c7d9b42` before it merges.
4. Manuscript only (not code):
   - SOP 1 and 2 rephrase, title, remove the V-Model, RRLs, scope and limitations;
   - the scoring criteria (explain the suggested score: share of required structures found, then the instructor's review of telemetry and output);
   - the difficulty definitions (Beginner/Intermediate/Expert, as in `astRules.js`);
   - the retake policy (one instructor-granted late attempt; unlimited attempts before the deadline);
   - "standard library only".

## Release checks with Errol: production state (2026-10-21)

_Checked with Errol (owner of the Render account, with Supabase and Brevo access), following the owner's release-checks brief, 2026-10-20 17:30–18:40 UTC. Claude deployed nothing and changed no database or Render setting. Errol made the two production changes listed below himself. No credential, `.env` value or connection string was read, printed or committed. Account identities are left out of this public file on purpose._

### Production now
| Part | State | Evidence |
|---|---|---|
| Frontend (Vercel Production) | `bd17c3f` | GitHub deployment record (`vercel[bot]`, success, 2026-10-20 07:41Z) |
| Backend (Render) | `bd17c3f` code | `GET /health` reports "PSU Python IDE Backend", the name `bd17c3f` introduced. Errol: the deploy succeeded |
| Database | PostgreSQL **17.6**; `alembic_version` = `5e8a1c7d9b42` | Read-only `SELECT`s in the Supabase SQL editor (run by Errol) |
| `audit_records` CHECK constraints | 20 action types, 7 resource types, 3 outcomes (the baseline) | Same |
| Active admin accounts | 1 (none before 2026-10-20 ~18:05Z) | Same, then the `seed_admin.py` output |

### Production changes on 2026-10-20 (made by Errol)
1. **~17:40Z: manual Render deploy of `dev` (`bd17c3f`).**
   - `start.sh` applied migration `5e8a1c7d9b42`, confirmed by `alembic_version`.
   - No backup existed (see "Backup").
   - From 07:41Z until this deploy, the frontend was ahead of the backend. The new activity editor always sends `scenario` and `solution_explanation`, and the old `TaskCreate` (`extra="forbid"`) rejects unknown fields. So creating an activity would have returned 422 (inferred from code; not tested in production).
2. **~18:05Z: one admin account created** with `backend/seed_admin.py` (not modified).
   - Errol ran it himself, entering the URL and the password at hidden prompts.
   - He shared the temporary password with the owner by call.
   - This is a temporary demonstration account. Replace it with named accounts before real use (see "Admin accounts" in the 2026-10-20 section).

### Findings
- **No admin account existed before this.** `active_admins` was 0, so the password in `errol_final_deployment_steps.md` never worked in production. This matches the owner's "Invalid email or password" result.
- **Guest sign-in worked with no admin.** `get_or_create_sandbox_classroom` returns the existing sandbox when no active admin exists. Now that an admin exists, the next guest sign-in moves the sandbox to the admin and writes a `classroom_updated` audit record. That's expected.
- **PostgreSQL 17.6, not 15.**
  - #30's "PostgreSQL 15 tested" condition should read 17.
  - No suite has run on 17: the migration tests ran on 18.4, everything else on SQLite.
- **Deploys:**
  - Render deploys only when Errol clicks Manual Deploy. It's his account, and there's no GitHub webhook because he isn't a repository admin.
  - Vercel deploys every push to `dev`. So a push that changes both sides leaves the frontend ahead of the backend until Errol deploys, and a push with a migration applies it at that click.
  - **Coordinate pushes to `dev` with Errol.**
- **Render environment-variable saves** (Render documentation):

  | Option | What it does |
  |---|---|
  | "Save and deploy" | Redeploys the existing build with the new values |
  | "Save, rebuild, and deploy" | Builds the latest commit |
  | "Save only" | Waits for the next deploy; a restart doesn't pick up the new values |
- **Email:**
  - The SMTP variables are set on Render (set/not set only), and `SMTP_PORT` is 2525.
  - Render's free plan blocks outbound ports 25, 465 and 587 only, so 2525 isn't affected.
  - Errol reports that OTP email works. A received email in the smoke test is still the proof.
- **AI Tutor ("Full backend audit", Still open, item 6):**
  - Broken in four places since `7748c49` (2026-10-01): no UI, no `attempt_id` in the submit response, no `ai_hint` storage, and no Gemini SDK.
  - Restored in PR #38: Redis-backed hints, **no migration**, a new `google-genai` dependency; 911 passed, 5 skipped.
  - **Not merged or deployed.** Close item 6 once it's merged and Errol has deployed the backend.

### Backup
- **None exists.** The Supabase free tier gives no backups.
- No restore has been tested, and no dump has been taken.
- A `pg_dump` contains students' personal data, so whether to take one, and where to keep it, is the owner's decision.

### Release blockers (from 2026-10-20): status now
| # | Blocker | Status 2026-10-21 |
|---|---|---|
| 1 | Rotate the production admin password | **Superseded.** No admin account existed, so the leaked password never worked. A new admin exists (above) |
| 2 | Rotate the SMTP/Brevo key | **Pending.** Errol and the owner together, on a call; use "Save and deploy" |
| 3 | Render configuration | **Mostly known:** branch `dev` (from the live code); manual deploys only; the start command runs migrations (evidenced by `alembic_version`); `SMTP_PORT` 2525. Health-check path and instance type not reported |
| 4 | Production database version and revision | **Done:** PostgreSQL 17.6, `5e8a1c7d9b42` |
| 5 | A verified, restorable backup | **Open: none exists** (free tier). Owner decision |
| 6 | Production smoke test | **Not run** |
| 7 | `errol_final_deployment_steps.md` | Unchanged: deleted from `dev`, still at the tip of `main` |

### Verdict
**Still not production-ready:** blockers 2, 5 and 6 are open. Everything checked so far matches the code at `bd17c3f`.

### Next
1. **Errol and the owner:** swap the SMTP key, then use "Forgot password?" on a test student. The email must arrive.
2. **Owner and Errol:** run the smoke test (2026-10-20 section), with Errol watching the Render logs. Include creating an activity (the 422 gap) and the panel features.
3. **Owner:** decide on a backup.
4. **Owner:** review PR #38. After the merge, Errol deploys the backend.
5. **After delivery:** #30, re-pointed onto `5e8a1c7d9b42` and tested on PostgreSQL 17.

## Release day: checks at `5be5142`, legacy submission route, Redis TLS (2026-10-21)

_Main checkout, `dev` fast-forwarded from `bd17c3f` to `origin/dev` `5be5142` (PR #38, squash-merged by Errol on 2026-10-20 at 18:34Z). This session committed, pushed, merged and deployed nothing, and changed no production setting or database. Production was checked only with unauthenticated public reads. No credential was printed. The local PostgreSQL URL was read from `backend/.env` inside a script that refuses any non-local host and never prints it._

### Production state (read-only, 2026-10-21 ~00:45Z)
| Part | State | Evidence |
|---|---|---|
| Frontend (Vercel Production) | `5be5142` (#38), since 2026-10-20 18:39Z | GitHub deployment record (`vercel[bot]`, success) |
| Backend (Render) | Healthy: `/health` 200 after a 52 s cold start (00:43Z). **Whether it runs #38 is unverified.** #38 adds no route and the API docs are off in production, so it can't be told apart from `bd17c3f` without signing in | Public `GET /health` |

- **#38 is merged.** "Full backend audit" item 6 (AI Tutor) closes once Errol's backend deploy is confirmed. To check, a failed practice submit should show the tutor.
- **Until that deploy, the tutor stays hidden.** The old backend's practice-submit response has no `attempt_id`, and the panel only appears when it has one. Nothing breaks.

### Test evidence at the release tip `5be5142`
| Check | Result |
|---|---|
| Merged tree vs PR #38 head `c1afdbc` | **Identical tree** (`e967fd4`), so #38's run (911 passed, 5 skipped) covers the merged code |
| Full SQLite suite, `5be5142`, Windows | **910 passed, 5 skipped, 1 failed** (23 min 47 s, 00:42–01:07Z). The failure is a timing bug in a #38 test, not the app (next section) |
| PostgreSQL-only suites, `5be5142`, local PostgreSQL 18.4 | **7 passed** (33 s): the migration chain through `5e8a1c7d9b42` (upgrade, downgrade, re-upgrade), plus the submission, grade, execution-idempotency and partner-execution concurrency suites. Temporary databases were dropped; `pamsu_ide_db` wasn't touched |

- **First concurrency run since the panel changes.** The retake work changed `submission_service.py`.
- **Still no PostgreSQL 17 run.** Production is on 17.6; only 18.4 is installed here.
- **The local `backend/venv` is behind `requirements.txt`:** redis 4.6.0 (pinned 7.0.1), SQLAlchemy 2.0.50 (pinned 2.0.52), and no `google-genai`. The suite passes anyway, because the tutor tests stub the SDK. To refresh it, run `pip install -r requirements.txt` in that venv.

### #38 test that depended on machine speed, fixed
- **Failure:** `test_practice_ai_tutor.py::test_polling_itself_is_limited_per_student` sends 61 hint polls and expects the 61st to get 429 (limit 60 per 60 s).
- **Cause:** the test setup points Redis at a closed port, so the limiter counts in memory (`core/memory_fallback.py`), in a fixed window timed by the real clock. On Windows each request waits out the 1 s Redis connect timeout (measured 1.02 s per request), so the 61 polls take about 62 s, and the window has reset before the last one. On Linux, where #38's 911-pass run was made, a refused connection fails at once.
- **Production impact: none.** Redis is reachable there, and the limiter behaves the same either way.
- **Fix (test only):** the test swaps in an `ExpiringMemoryStore` with a frozen clock, so all polls fall in one window. The limit is still checked: the 61st poll must return 429. It passed in 189 s, with requests slowed by a concurrent suite run, well past the 60 s window.

### Item 7: legacy `POST /execution/submissions/`, fixed
- **Problem:** the route inserted the attempt by itself, with:
  - no `submission_created` audit record, academic event or instructor notification;
  - no background evaluation and no submit run.

  Nothing in the frontend calls it, but any signed-in student can. So a student could hand in an official attempt that **skipped the structure and similarity checks** and left no audit trail. The instructor saw it as "awaiting_review" with no indicators.
- **Change:**
  - The route keeps its own checks first, so its documented 403/404/409 codes and its **strict deadline** don't change: a retake allowance still works only through `POST /submissions/`.
  - It then saves through `create_student_submission`, the same service `POST /submissions/` uses. The attempt, audit record, academic event and instructor notification commit together, and a failed audit or notification write returns 503 with nothing saved.
  - Afterwards it calls `queue_submission_processing`, the background-evaluation and submit-run step, now shared with `POST /submissions/` in `routers/submissions.py`.
- **Side effects:**
  - The status is now `submitted`, as for every other attempt, instead of `awaiting_review`.
  - A graded task with no class now gets 404, as on the main route; before, it was accepted.
  - The route also uses one Judge0 run per attempt, like the main route.
- **Not chosen:** removing the route. Nothing calls it, but removal changes the public API, so it's left to the owner.

### Related: legacy `GET /execution/submissions/{sub_id}` showed students the review indicators, fixed
- **Problem:** the route returned the full `SubmissionResponse` to students, including `jaccard_score` and `ast_pass_fail`. The schema marks both as instructor-only, and the student routes (`StudentSubmissionResponse`) leave them out. A student could check their own similarity score after evaluation, rework a copied solution and submit again before the deadline.
- **Change:** students get both fields as `null`. Instructors (owner only) still get the values. The stored row isn't changed.

### Item 10: `rediss://` certificate checks, fixed
- **Problem:** both the API's Redis client (`core/redis_client.py`) and Celery (`tasks/celery_worker.py`, broker and result backend) used `ssl_cert_reqs=none`. That accepts any certificate, so anyone able to intercept the connection could read or change the queue, rate-limit counters, token revocations and tutor hints.
- **Change:** a new `core/redis_tls.py` used by both:
  - `rediss://` URLs get `CERT_REQUIRED`, checked against certifi's CA bundle (`certifi` is already pinned). `redis://` URLs are unchanged.
  - **Emergency switch:** `REDIS_SSL_CERT_REQS=none` restores the old behaviour, with a warning in the log. Any other value still verifies.
- **Checked with the production pins** (redis 7.0.1, kombu 5.6.2, celery 5.6.3, certifi 2026.7.22, in a scratch venv) against badssl.com test hosts:
  - **Default:** a valid certificate is accepted (the connection then fails only because the host isn't Redis). Self-signed, expired, wrong-host and untrusted-root certificates are **rejected**, by redis-py and by Celery.
  - **With `=none`:** all four bad certificates are accepted, which is the old behaviour.
- **Not verified:** Upstash's own certificate (production credentials aren't available here). Upstash serves a publicly trusted certificate, so it should validate.
  - **After Errol's next deploy, check the Render log:** the Celery worker line `Connected to rediss://…` with no `CERTIFICATE_VERIFY_FAILED`. A Run in the smoke test proves it end to end.
  - **If the log shows the error:** set `REDIS_SSL_CERT_REQS=none` on Render with **"Save and deploy"** (no rebuild), then tell the owner.

### Tests for this session's changes
| Check | Result |
|---|---|
| New `tests/test_legacy_submission_route.py` | **6 passed**: same records as `/submissions/` (audit record, academic event, instructor notification, evaluation queued, submit run); newest attempt official; documented 403/404 codes; still 409 after the deadline even with a retake allowance, and the allowance stays usable on `/submissions/`; nothing saved when the audit write fails (503); student GET hides the indicators, instructor GET shows them, other users get 403 |
| New `tests/test_redis_tls.py` | **12 passed**: `redis://` gets no TLS options; default, `required`, unknown values → verify with certifi; `none` → off with a warning; no certifi → system store; in a fresh process, the API client and Celery broker and backend all get the same options |
| `tests/test_api_workflow.py` (updated) | Passed. The legacy submit now expects `submitted`; the student GET expects `null` indicators; an instructor GET was added that expects the values |
| Mutation checks | With the old `execution.py`, 3 of the 6 legacy-route tests fail (records, 503 rollback, hidden indicators); the other 3 pin down unchanged behaviour. With the old `redis_client.py` and `celery_worker.py`, both connection-point tests fail |
| Full SQLite suite with these changes (01:03–01:26Z) | **928 passed, 5 skipped, 1 failed.** 928 = the baseline's 910 plus the 18 new tests. The one failure is the same timing test: the run collected it before its fix |
| `tests/test_practice_ai_tutor.py` after the fix (whole file) | **24 passed** (8 min 44 s) |
| **Final tree** (the full run above plus the test-only fix) | **929 passed, 5 skipped, 0 failed** across the two runs. No single end-to-end run of the final tree; the only difference is that one test function |
| pyflakes on the changed files, `git diff --check` | Clean |

### What a push of this commit does
- **Vercel:** rebuilds the same frontend. No frontend file changed.
- **Render:** nothing until Errol's next Manual Deploy. That deploy, needed anyway for #38, also carries items 7 and 10. **No migration** (the head stays `5e8a1c7d9b42`).
- **To deploy #38 alone:** Errol deploys first, and the push comes after.

### Production smoke test for today (supersedes the 2026-10-20 list)
Same rules as before: test accounts only, write down every record created, don't use Vercel previews, and stop on a critical failure. Errol watches the Render logs.
0. Warm up: `/health` returns 200. In the Render log, the Celery worker connected to `rediss://` with no certificate error.
1. Sign in as student, instructor and admin; a wrong password is refused. **Use the admin dashboard's "Change password" now**, so only the owner knows the admin password.
2. "Forgot password?" for a test student (after the SMTP key swap): **the email arrives**, the code works, the new password signs in.
3. Masterlist import of one test row: **the setup email arrives** with no credential in it. Then step 2 for that student.
4. **Create an activity** (the 2026-10-20 422 gap): use "Analyze the activity", fill in a scenario and solution explanation, set "Required at least N" on one rule, and publish. Enroll the test student.
5. Workspace **Run**: output appears, not stuck at "queued". Errol sees the Celery task and the Judge0 callback.
6. **Submit:** saved and listed. The evaluation completes, and the Grading Bench shows the structure check (found/needed) and a suggested score.
7. **Practice:** a correct submit shows a result within 15 s. **A failing submit shows the AI Tutor hint** (only after the #38 deploy).
8. **Grading Bench:** grade, save, release. The student sees the grade, the notification and "How the solution works".
9. **Edit the deadline** of the test activity: the student gets "Deadline changed". Close the deadline, use "Allow another attempt", and the student's late attempt is accepted once.
10. **Faculty lockout**, on a *test instructor*, never the only admin: 5 wrong passwords, then the lockout message.
11. Admin creates a test faculty account with a middle name.
12. Log out: the old session is rejected.
13. Optional: guest sign-in lands in the sandbox only. The first guest sign-in moves the sandbox to the admin, which is expected.

### "Full backend audit" → "Still open": status now
| # | Item | Status |
|---|---|---|
| 1 | PostgreSQL migration and concurrency suites | Run on 18.4 (2026-10-18, and again today at `5be5142`). **15/17 not run** |
| 2 | Admin actions not audited | PR #30, **deferred until after delivery** |
| 3 | Redis fail-open | Done (#35) |
| 4 | Guest accounts | Done (#36) |
| 5 | Practice submit waits on Judge0 | Waits for #30 (its migration chains after `61330560eec5`) |
| 6 | AI Tutor | **Merged (#38).** Close once Errol's deploy is confirmed |
| 7 | Legacy `POST /execution/submissions/` | **Fixed this session** (plus the legacy GET) |
| 8 | Default AST strictness | Done (#37) |
| 9 | Retakes, enrollment decisions, instructor temporary-password email | Retakes done (panel work). The other two need owner decisions |
| 10 | `rediss://` certificate checks | **Fixed this session** |

### Files
- **Modified:**
  - `backend/app/core/redis_client.py`
  - `backend/app/routers/execution.py`
  - `backend/app/routers/submissions.py`
  - `backend/app/tasks/celery_worker.py`
  - `backend/tests/test_api_workflow.py`
  - `backend/tests/test_practice_ai_tutor.py` (frozen clock in the polling-limit test)
  - `audit-status.md`
- **Created** (untracked: **add them explicitly**. `redis_client.py` and `celery_worker.py` import `redis_tls.py`, so without it the backend won't start):
  - `backend/app/core/redis_tls.py`
  - `backend/tests/test_legacy_submission_route.py`
  - `backend/tests/test_redis_tls.py`

### Next
1. **Owner:** commit and push this session's work. Agree the timing with Errol (see "What a push of this commit does").
2. **Errol:** Manual Deploy on Render (#38 plus this commit). Check the Celery `rediss://` connection line in the log.
3. **Unchanged from the release-checks section:** the SMTP key swap with Errol, the smoke test above, and the backup decision. **The release is not production-ready until those are done.**
4. **After delivery:**
   - #30, re-pointed onto `5e8a1c7d9b42` and tested on PostgreSQL 17; then item 5;
   - owner decisions for item 9;
   - whether to remove the legacy `/execution/submissions/` routes.

## MIS admin dashboard UI overhaul (2026-10-21)

_Branch `dev` on top of `3ab3576`. Frontend only: no API, backend or migration change. Every request, handler, validation rule and confirmation dialog is unchanged; only layout and styling changed, plus two small fixes noted below. Nothing was committed or pushed by this session._

### What changed, per tab
- **Shell (all tabs):**
  - The header shows the signed-in admin (name, email, initials avatar) next to Sign out, and has a maroon–gold–maroon line along its bottom edge.
  - The sidebar is sticky, with an "Administration" label and a "PSU Python IDE · MIS console" footer.
  - Each section fades in on tab change.
  - **Result messages** ("X is now suspended", …) now clear when you switch tabs. Before, they followed you to every section.
- **Overview:**
  - A maroon banner with a greeting, today's date, and a status chip: "All services open", or "Maintenance mode on" in gold.
  - **Four stat cards** with icon tiles and a maroon-to-gold top border: Instructors, Students and Classrooms (from `/admin/stats`), and **Student access** (Open or Paused, from the saved maintenance setting). Each has a one-line note on what it counts; for example, Students includes guest accounts, which the Students tab doesn't list.
  - **Recent activity:** the 6 latest audit events, with actor, event, role, resource, relative time ("12 min ago", full date on hover) and an outcome pill, plus a link to the full audit trail. It reuses the audit list the page already loads, so there's no extra request.
  - **Quick actions:** add a faculty account, add a student account, import a masterlist, review the audit trail, system settings. Each opens its tab and moves focus to the right field (email field, or the upload box).
- **Faculty and Students:**
  - **Layout:**
    - The create form now sits **above a full-width directory**, instead of beside it.
    - Measured at 1366 px, the old side-by-side layout left the table 680 px, so "Reset password" wrapped and the Actions column scrolled sideways. Side by side, it was still 62 px too narrow even at 1600 px.
    - On Students, the form and the masterlist upload share the top row from 1024 px up.
  - **Forms:**
    - The card has a header (title, one-line purpose); the fields adapt to the card's width (container queries): email paired with the temporary password (faculty) or the school ID (students), and first/middle/last name in one grouped row.
    - Inputs are taller, the temporary password has a "shown once" hint, and a large **Create account** button sits in the card footer.
  - **Masterlist:** a dashed drop zone ("Choose a masterlist file · CSV or .xlsx") replaces the plain button. It's the same file input and handler.
  - **Directory tables:**
    - The card header shows the title, an account count and, on Students, the search box. While searching, the count reads "1 of 8 accounts".
    - Rows: an initials avatar with a bold name over the email, the school ID in a mono chip, and **pill badges with a dot** (green Active, grey Suspended).
    - Bordered action buttons with icons. Suspend tints red on hover, Activate green, and each button's screen-reader name includes the person's name.
    - Row hover is a cream tint.
  - **Fix:** the Faculty tab now has "Load more accounts". The directory loads 50 accounts at a time, and before, faculty beyond the first page were never shown.
- **Audit trail:** the same table style:
  - **When:** the date above the time;
  - **Actor:** initials avatar, **bold name**, role ("Automated" for system actions);
  - **Event:** in medium weight;
  - **Resource:** a neutral chip;
  - **Outcome:** a pill. Green Succeeded, red Failed, gold Denied.
  - The card header has an event count.
- **Settings:**
  - Centered in a `max-w-4xl` column, header included.
  - "Platform policies" is one card with a divided header and one row per setting: the maintenance switch with an On/Off label, self-registration as a "Disabled" pill (or a warning when the legacy flag is on), and the strictness choices as selectable cards.
  - A footer holds "Unsaved changes" and Save.
  - **Change password** uses the same divided header, through a new optional `divided` prop on `SettingsSection`/`ChangePasswordSection` in `AccountSections.jsx`. The instructor and student settings pages don't pass it, so they're unchanged.

### Verification
- `npm run lint` clean; `npm run build` OK; `git diff --check` clean.
- **Browser setup:** a copy of the QA kit run from the session scratchpad, on ports 8013 (API) and 5177 (app), with its own throwaway SQLite database. Email, Redis, Judge0 and AI were blanked by the kit; `qa/.qa-data` and production were never touched. The data was seeded through the API: 4 faculty, 8 students, one suspended account, one failed sign-in and one classroom. Checked at 1366×768:
  - every tab rendered, with no page or table overflow on any tab at 1366 px or 1600 px;
  - quick actions: Faculty focused the email field; Masterlist focused the upload box and scrolled it into view;
  - a faculty account was created through the new form: success message, count 4 → 5, and the new row appeared;
  - Suspend through the confirmation dialog: "Suspended" pill and an "Activate" button;
  - student search, with the "x of y" count;
  - maintenance mode on → "Unsaved changes" → Save → the Overview showed "Maintenance mode on" and "Student access: Paused";
  - the discard-unsaved-settings dialog: Discard moved tabs and reverted the switch;
  - at 375 px: no horizontal overflow, the tab strip scrolls, and the cards stack.
- No console errors from the final code and no backend errors. The only console errors came from one hot-reload moment mid-edit, a version of the file that never shipped.
- **Seen but not changed:**
  - On the SQLite QA copy, every time in the app shows UTC: SQLite drops the time zone, so "8 h ago" shows in UTC+8. Production stores `timestamptz` and sends the offset, so production times are correct (as in the owner's production screenshot).
  - Admin account changes (create, suspend, reset) still write no audit record. That's PR #30, deferred.

### Files modified (tracked, no new files)
- `frontend/src/features/admin/AdminDashboard.jsx`
- `frontend/src/features/settings/AccountSections.jsx` (optional `divided` prop)
- `audit-status.md`

### What a push of this commit does
- **Vercel deploys it to production immediately.** The admin dashboard changes for anyone signed in as MIS. Students' and instructors' pages are unchanged.
- **Render:** nothing; no backend file changed.
- **If the production smoke test is running at the time,** the admin screens will look different mid-test, though they work the same way.

### Next
- **Unchanged from the release-day section:** the SMTP key swap, the production smoke test and the backup decision.
- **Optional follow-ups:** a "show guests" toggle on the Students directory (`include_guests=true`); admin dark mode (not approved).

## Admin dashboard: account editing, faculty search/export, audit filters (2026-10-21)

_Branch `dev` on top of `5c4d43c` (the UI overhaul, already pushed and live on Vercel). **Backend and frontend change; no migration.** Nothing was committed or pushed by this session._

### What changed
1. **Edit action (Faculty and Students):**
   - Each row has **Edit** before Reset password and Suspend. A dialog corrects the **full name** and **university email**. Storage is the single `users.name` column, so the name is one field.
   - **New endpoint `PATCH /admin/users/{user_id}`** (admin only), body `{name?, email?}`:
     - `extra="forbid"`: role, school ID, password and status can't be changed through it (422).
     - Names are trimmed with spaces collapsed, at most 150 characters. Emails must be `@pampangastateu.edu.ph`, are lowercased, and can't start with `guest_` (reserved for self-service guests).
     - **409** if another account already uses the email (case-insensitive). **403** for administrator accounts, including your own, and for self-service guests. **404** for an unknown account.
     - **An email change expires every unused password-reset code for the old and the new address.** A code sent to a mistyped address can no longer be used. Reset completion already looked the account up by email, so this is a second safeguard.
     - **A student's corrected email joins the classes that had queued it**, the same as at account creation. The response's `pending_enrollments` reports them.
     - The response has `changed_fields`; a no-op returns `[]`.
   - **Not audited:** no `audit_records.action_type` fits an account edit. As with the other admin actions (suspend, reset, settings), this waits for PR #30's migration. Add `user_updated` there.
2. **Faculty directory:** the same search box as Students (name, email or ID, with an "x of y" count) and **Export CSV** in the page header.
   - **Both exports now fetch every account**, 500 per request, not only the rows loaded on screen.
   - Cells a spreadsheet would run as formulas (`= + - @`) are prefixed with `'`.
   - Files are `psu_faculty.csv` and `psu_students.csv` (was `pamsu_students.csv`, per the panel's PSU naming).
3. **Audit trail: filters and page numbers.**
   - **New endpoint `GET /admin/audit-logs/search`** (admin only), newest first, with a stable tie-break:
     - **Filters:** `q` (part of the actor's name or email; case-insensitive; `%` and `_` matched literally), `action_type` (the 20 allowed types), `outcome`, `actor_role` (`admin`, `instructor`, `student`, `system`), `occurred_from` (inclusive) and `occurred_to` (exclusive). An offset in the bounds is converted to UTC; a bound without one is taken as UTC.
     - **Paging:** `page` and `page_size` (5–100). The response is `{items, total, page, page_size, action_types}`, and items also carry `actor_email`.
   - **UI:**
     - A filter bar: Actor search (debounced), Event, Outcome, Role, From/To dates (local days), and Clear filters.
     - A pager footer: "Showing 26–33 of 33 events", 25/50/100 rows per page, Previous/Next with "Page 2 of 2". The header has a count badge and a Refresh button.
     - The actor cell shows role · email.
   - **The original `GET /admin/audit-logs` is unchanged** (a plain list). The Overview's Recent activity still uses it.
4. **Settings:** the "Student self-registration" row and its warning are **removed**.
   - The API still requires the field, and a save now always sends `registration_enabled: false`. Accounts are MIS-provisioned only (panel requirement), and the setting defaults to off.
   - If production ever had it on, the next settings save closes the legacy `/registration` API.

### Works with today's production backend (the deploy gap)
Vercel publishes the frontend on push, and the backend waits for Errol's Manual Deploy. So the new page was checked against a backend that lacks both endpoints (simulated by answering the page's requests with 404/405):
- **Audit trail:** a 404 "Not Found" from `/search` switches to the plain newest-first list with "Load older events", plus the note "Filters and page numbers become available after the next server update." The list is fetched fresh at that moment.
- **Edit:** the old backend answers 405 (only `DELETE` exists on that path). The dialog says editing needs the latest server update and changes nothing.
- **Faculty search, export and the Settings change** need no backend change.

### Verification
| Check | Result |
|---|---|
| New `tests/test_admin_account_edit_and_audit_search.py` | **24 passed**: name and email correction (sign-in moves to the new email); no-op; 9 invalid or forbidden bodies (role, school ID, password, guest_ prefix, blank or long name, foreign domain, double @, empty); 409 duplicate; 403 for admin, self and guest; 404; non-admin 403 and anonymous 401; reset codes expired for both addresses on an email change but not on a name change; pending class joined on a student email correction; none for instructors; search paging and total, name/email search, literal `%`/`_`, combined filters, system actor, date bounds (inclusive/exclusive, UTC+8 offset), 7 bad parameters → 422, non-admin 403; old list shape unchanged |
| Full backend suite (SQLite, Windows, 03:02–03:26Z) | **953 passed, 5 skipped, 0 failed** (929 before + 24 new) |
| Frontend `npm run lint`, `npm run build`, `git diff --check` | Clean |

**Browser** (the scratch QA copy from the previous section, at 1366×768):
- **Faculty:** the Edit, Reset password and Suspend buttons fit with no table overflow.
- **Edit dialog:**
  - focus starts in the name field, and Save stays disabled until something changes;
  - the email-change warning appears;
  - saving updated the row and showed "Saved Jose Reyes: the name is now …, and they now sign in as …";
  - a duplicate email showed the server's 409 as a field error, a non-university email was caught in the browser, and Cancel left the row unchanged.
- **Faculty search and export:**
  - "reyes" found 1 row, with "1 of 5 accounts";
  - the export, captured in the page rather than downloaded, was `psu_faculty.csv` with all 5 faculty, including the suspended one ("No").
- **Audit trail** (33 events):
  - pages of 25 + 8, and 50 per page;
  - actor "BEA" → 3, plus outcome Succeeded → 0;
  - role Admin → 5, event Classroom created → 1;
  - from tomorrow → 0, and an inverted range shows the date error;
  - Clear filters restores all 33.
- **Old-backend fallback** for both endpoints, as described above.
- **Settings:** only Maintenance mode and Default AST strictness, and the save request carried `registration_enabled: false`.
- **Errors:** the only console error was the browser's network log of the intended 409. The backend logged no application errors (only Windows connection-reset noise).

### Files
- **Modified:**
  - `backend/app/routers/admin.py` (the edit endpoint and the audit search; the old list now shares the row builder)
  - `frontend/src/features/admin/AdminDashboard.jsx`
  - `audit-status.md`
- **Created** (untracked, add it by name):
  - `backend/tests/test_admin_account_edit_and_audit_search.py`

### What a push of this commit does
- **Vercel deploys the dashboard at once.** Faculty search, export and the Settings change work immediately. Edit and the audit filters show "needs the server update" or the plain list until the backend is deployed.
- **Render:** the two endpoints arrive at Errol's next Manual Deploy (which also carries #38 and `3ab3576`). **No migration.**

### Next
- **Errol:** deploy the backend, then check Edit and the audit filters on production.
- **After delivery:**
  - add `user_updated` (and the other admin action types) through PR #30, so edits are audited;
  - optionally let MIS correct a student's school ID (left out on purpose: the request was names and emails).

## Account provisioning email: wiring, admin UI copy, new template (2026-10-21)

_Branch `dev` on top of `364e20c`. Backend and frontend change; no migration. Nothing was committed or pushed by this session, and no real email was sent: tests stub SMTP, and the local QA copy has no SMTP key._

### How the email is sent (verified in code)
| Path | Before | Now |
|---|---|---|
| `POST /admin/instructors` (Faculty form) | Welcome email with the temporary password | Same, plus last name and account ID for the new template |
| `POST /admin/students` (Student form) | **No email at all.** The admin had to pass the password on by hand | **Welcome email with the temporary password and school ID** |
| `POST /admin/students/bulk-register/file` (masterlist) | Setup email for each created student, **no password** (by design: masterlist accounts have no usable password until the student sets one through "Forgot password?") | Same design. The email says no password was issued and links to `/forgot-password`. The greeting uses the file's own first and last name columns when it has them |
| `PATCH /admin/users/{id}/password` (admin reset) | Not emailed; the admin is shown the new password once | Unchanged. "Share it securely" stays in that message because it's accurate |

- **Dispatch:**
  - Each route queues `send_provisioning_email` as a FastAPI **background task after the commit**: one SMTP session per recipient, after the response.
  - It runs in the API process (not Celery): no retry, and a failure is only logged, so the admin never sees it.
  - **That's why the success message still shows the temporary password, as a fallback.**
- **SMTP:** `smtplib` with STARTTLS and login on `SMTP_HOST:SMTP_PORT` (Brevo's SMTP relay, port 2525 on Render), with a 15 s timeout per command.
- **Logging:**
  - Recipient addresses are now masked (`j***@pampangastateu.edu.ph`).
  - A failure logs only the error class and SMTP code (for example `SMTPAuthenticationError 535` or `SMTPSenderRefused`), never the error text, which can echo the address or the message.
  - Before, it logged full addresses and the raw error text.

### Environment variables (Render)
| Variable | Needed? | Notes |
|---|---|---|
| `SMTP_USER`, `SMTP_PASS` | **Required.** If either is missing, nothing is sent (logged as "not sent") | Brevo's **SMTP login and SMTP key**, not the REST API key: this code uses the SMTP relay, so **no `BREVO_API_KEY` is needed**. Errol reports both are set. **The key is the exposed one: rotation is still pending** (release blocker 2) |
| `SMTP_HOST` | Optional (default `smtp-relay.brevo.com`) | Errol reports it set |
| `SMTP_PORT` | **Required on Render** (the default 587 is blocked on the free plan) | Set to 2525 (reported) |
| `SMTP_SENDER_EMAIL` | Recommended (default `noreply@pampangastateu.edu.ph`) | **Must be a verified sender or domain in Brevo**, or every email is refused (`SMTPSenderRefused`). Not yet checked in Brevo |
| `SMTP_SENDER_NAME` | Optional (default "PSU Python IDE") | May still say "PAMSU" on Render. Check it |
| `FRONTEND_URL` | Optional (default `https://pamsu-python-ide.vercel.app`) | Base of the "here" link. Set it only if the frontend domain changes |

### New email template (`services/email_service.py`)
- **Layout:** tables and inline styles only (no `<style>` block); 600 px wide, full-width on phones.
  - **Header:** solid PSU gold `#eaae19`, with the logo and **PAMPANGA STATE UNIVERSITY** (bold, maroon `#77250b`) side by side in one table row.
  - **Body:** white, `#1f2937` text, 28–32 px padding.
  - **Footer:** solid gold, centered white text: **Contact Details**, address, phone, `info@pampangastateu.edu.ph` (a mailto link).
- **Content:**
  - "Good day {Last}, {First},". When only a full name is known (a masterlist with a single name column), that name is used as given; a surname is never guessed.
  - The welcome sentence as specified.
  - "Take note of your temporary account details:" with **School ID Number**, **Email / Username** and **Temporary Password** (monospace, kept on one line).
  - "To complete the process, please click **here** to sign in and reset your password." The link goes to `/login`, or for masterlist accounts to `/forgot-password` ("…to set your password and sign in").
- **Logo:**
  - `backend/app/assets/psu_logo_email.png`, a 128×128 copy (30 KB) of `frontend/public/school_logo.png`, shown at 56 px.
  - **Embedded as an inline image (Content-ID) in a `multipart/related` message**, which Gmail, Outlook and Apple Mail show without remote-image prompts. Base64 data URIs are blocked by Gmail and Outlook, and hosted images are hidden by default in Outlook.
  - If the file is missing, the email is sent without it.
- **Also:**
  - a plain-text part;
  - `Date` and `Message-ID` headers (deliverability);
  - every value HTML-escaped;
  - about 49 KB per email.
- **Fixed:** the old template named the school "Pampanga State **Agricultural** University" (a different university), and relied on a `<style>` block that several clients strip.
- **Accessibility:** white footer text on gold has a contrast of about **2.0:1** (WCAG asks for 4.5:1), so the contact lines are hard to read. It was kept as specified; maroon on gold (about 5.2:1) would be a one-line change.

### Admin UI copy (`AdminDashboard.jsx`)
- **Create forms:**
  - The description reads "The sign-in details are emailed to the instructor automatically" (faculty) or "For one student. The sign-in details are emailed automatically." (students).
  - The temporary-password hint reads "Account credentials will be automatically emailed to the user." (was "Shown once after the account is created. Share it privately.").
  - After creating an account: "Their sign-in details, including the temporary password, are being emailed to them. If the email doesn't arrive, the temporary password is …".
- **Masterlist:**
  - The card reads "New students are emailed their account details automatically." (was "No password is set or emailed.").
  - The result says each new student is emailed their account details and a link to set their own password.

### Verification
| Check | Result |
|---|---|
| New `tests/test_provisioning_email.py` | **18 passed**: MIME structure (related > alternative[plain, html] + inline PNG with a matching Content-ID); header, body and footer colours and text; greeting order; the three details; the `/login` link with "here"; footer contact lines; no "Agricultural" and no `<style>`; plain-text part; masterlist variant (no password, `/forgot-password`); HTML escaping (name, password); `FRONTEND_URL` override; sending without the logo; greeting fallbacks; STARTTLS, login and port 2525 via a fake SMTP; masked logs on success, failure and missing credentials; student and faculty creation queue the email with password, last name and ID; a refused duplicate sends nothing |
| `tests/test_masterlist_import.py` (updated stub) | Passed; it now also checks the greeting names and school IDs passed for column and single-name files |
| Full backend suite (SQLite, Windows, 03:38–04:03Z) | **971 passed, 5 skipped, 0 failed** (953 before + 18 new) |
| Frontend lint and build, `git diff --check` | Clean |
| Rendered preview (browser, 800 px and 375 px) | Header logo and name aligned; details wrap cleanly on a phone, and the password stays on one line; links correct. The footer's low contrast was confirmed visually |
| Local QA copy | The new copy shows on both forms. Creating a student queued the email; with no SMTP key the server logged "provisioning email to l***@pampangastateu.edu.ph not sent" |

**Not verified:** a real send through Brevo, and rendering in real mail clients (Gmail, Outlook). Do this in the production smoke test (step 3 there): create a test account and check the received email.

### Files
- **Modified:**
  - `backend/app/routers/admin.py`
  - `backend/app/services/email_service.py`
  - `backend/app/services/student_provisioning_service.py`
  - `backend/tests/test_masterlist_import.py`
  - `frontend/src/features/admin/AdminDashboard.jsx`
  - `audit-status.md`
- **Created** (untracked: add them by name):
  - `backend/app/assets/psu_logo_email.png`
  - `backend/tests/test_provisioning_email.py`

### What a push of this commit does
- **Vercel:** the new admin copy goes live at once.
- **Render:** the new template and the student-creation email arrive at Errol's next Manual Deploy. Until then, production keeps the old template, and **single student creation sends no email** (the copy says it does). Deploy the backend soon after the push.
- **No migration.**

### Next
1. **Errol:** deploy the backend. Rotate the SMTP key (release blocker 2), confirm the sender address is verified in Brevo, and check `SMTP_SENDER_NAME`.
2. **Smoke test:**
   - create a test student and a test faculty account, and check both emails arrive with the logo;
   - import a one-row masterlist, and check the email links to "Forgot password?".
3. **Optional:**
   - maroon footer text for legibility;
   - email the new password when an admin resets one;
   - reuse one SMTP connection for large masterlists.

## AI Tutor: restored and verified in production (2026-10-22)

**"Full backend audit" → "Still open", item 6 (AI Tutor) is closed.** Errol checked production on 2026-10-22: a failing practice submit shows the tutor's hint.

### What shipped
| PR | Change |
|---|---|
| #38 | Restored the tutor: `attempt_id` in the submit response, hints in Redis (24 h, memory fallback, no migration), `google-genai==2.28.0`, the tutor panel in `PracticeWorkspace.jsx` |
| #39 | Gemini retries with backoff (the SDK makes one attempt without `retry_options`); a failed generation is reported as `unavailable`, and "Try again" sends `retry=true` |
| #40 | 429 (quota used up) is no longer retried; Google's error text is logged; automatic function calling is off |
| #41 | **Fallback model:** when `gemini-3.8-flash` answers 503 or 429, the tutor asks `gemini-3.6-flash`. The worst case is 67 s, inside the 90 s generation lock and the frontend's ~80 s polling window |

### Why the fallback
- After #38 deployed, production logs showed `gemini-3.8-flash` answering **503 "high demand"**, then **429 "You exceeded your current quota"**: the Google project is on the free tier.
- **Errol approved the fallback on 2026-10-22.** It overrides the AGENTS.md rule "gemini-3.8-flash only, no fallback"; AGENTS.md (local, gitignored) should be updated to match.
- Linking a billing account to the Gemini project (Tier 1) is still the lasting fix if both models' free quotas run out.

### Next
1. **Errol:** update AGENTS.md to record the approved fallback.
2. **Owner:** decide whether to enable billing on the Gemini project.

## Audit follow-ups: what is still open (2026-10-22)

_Checked against `dev` @ `bb11f66`. From today, follow-up work is pushed straight to `dev` (Errol's decision). Vercel deploys each push at once; backend changes wait for Errol's manual Render deploy._

### Done in this commit
- **Removed the unused `xlsx` and `react-intersection-observer` packages** ("Frontend follow-ups"). Nothing imported them, and `xlsx` 0.18.5 has known npm security advisories. The lockfile only loses those two and `xlsx`'s eight sub-dependencies.
- **Removed the out-of-date strictness comment** in `InstructorSettings.jsx`. The sign-in response has included `ast_strictness_level` for some time.

### Older pending items that are already fixed (verified in the code)
- `/admin/*` router registered; `POST /guest` import error; `users.py` double router; the guest `PATCH /users/me` 500 (`UserResponse` accepts `GST…`/`FAC…`).
- The hardcoded `PamsU@2026` password; case-insensitive email checks in `POST /admin/students`; `DELETE /admin/users/{id}` on a student with enrollments (409, deactivate instead).
- CORS limited to this project's Vercel URLs; `rediss://` certificate checks; the ad-hoc `fix_*.py`/`check_*.py`, `write_migration.py` and `update_model.py` scripts are gone.
- The Judge0 callback is protected by its `correlation_id`: a random UUID that only the server and Judge0 see. No student-facing response includes it.
- Frontend: guest sign-in handles 429 and 5xx; the workspace treats a `failed` execution as finished.

### Still open
| # | Item | Needs |
|---|---|---|
| 1 | Admin actions not audited (deactivate, delete, password reset, settings, account edits): `audit_records.action_type` has a CHECK constraint | **A migration.** PR #30's `61330560eec5`, re-pointed onto the current head. Errol's OK first: no backup, and `start.sh` migrates on every deploy |
| 2 | Practice submit waits on Judge0 (up to 15 s), against the 3-second rule | Builds on item 1's migration chain |
| 3 | PostgreSQL 17 run of the migration and concurrency suites (production is 17.6) | A local PostgreSQL 17 |
| 4 | Release blockers: rotate the SMTP/Brevo key, production smoke test, backup | Errol and the owner |
| 5 | Remove the legacy `/execution/submissions/` routes? Should `POST /submissions/` create its own execution request? | Owner decisions |
| 6 | Enrollment questions (suspended students in bulk enroll, pending rows for archived classes, capacity, instructor visibility), instructor temporary-password email | Owner decisions |
| 7 | AI Tutor: enable billing on the Gemini project; record the approved fallback in AGENTS.md | Errol |
| 8 | Optional UI: "show guests" toggle (Students directory), "Re-apply pending enrollments" action, MIS editing a school ID, admin dark mode (not approved), rebuilding `PracticeModuleManager.jsx`/`ActivityEditor.jsx` on `PageShell` | Errol's choice |
| 9 | `ClassroomResponse` requires `section`, but the column is nullable: a classroom created outside the API would make `GET /classrooms/mine` return 500 | Small fix; low risk today, since the API always sets it |

## Admin action auditing: PR #30 ported onto `dev` (2026-10-22)

_"Still open" item 1 of the previous section. Errol approved the migration on 2026-10-22 and asked for a direct push to `dev` (no PR). PR #30 (`ce86db6`, Draft) was written against `00d5971`; `dev` has since changed `admin.py` a lot (account editing, audit search, provisioning email), so it was ported by hand rather than merged._

### What it does
- **Every admin change writes an audit record in the same transaction.** If the record can't be written, the change is rolled back and the admin gets 503 ("not saved because it could not be recorded"). Refused or failed attempts (own account, not found, email in use, dependent records, invalid file) get a separate `denied`/`failed` record.
- **Audited:** account creation (student form, guest, faculty, each masterlist row), **account edits (new: `user_updated`, which records which fields changed, never the values)**, activation/deactivation, password reset (only the new `password_version`), deletion, system settings (changed keys with from/to), and one `masterlist_imported` summary per upload (counts only).
- **Metadata privacy:** credential-like keys (`newPassword`, `reset_code`, `api_key`…) and values (bcrypt hashes, JWTs) are rejected by pattern.
- **Audit log API:** both `/admin/audit-logs` and `/admin/audit-logs/search` now add `resource_id`, `target_user_id`, `target_exists`, `target_name`, `target_role` and `details`. Old fields are unchanged. Stored login identifiers from failed sign-ins are masked unless they are well-formed university emails.
- **Dashboard:** the audit table shows the affected account under "Resource" (or "Deleted account #id"). With an older backend nothing changes.

### Migration `61330560eec5`
- **Re-pointed onto `5e8a1c7d9b42`** (the production revision) and extended with `user_updated`. Single head: `61330560eec5`.
- Widens `ck_audit_records_action_type` (+7) and `ck_audit_records_resource_type` (+`system_setting`, `masterlist_import`). No row is changed; one transaction, `lock_timeout` 10 s. Downgrade refuses once any row uses a new type.
- **Runs on production at Errol's next Render deploy** (`start.sh` → `alembic upgrade head`). There is no backup, but the change only widens two constraints; if it fails, PostgreSQL rolls the whole migration back.

### Tests
| Run | Result |
|---|---|
| Full backend suite, SQLite (`DATABASE_URL`, `PAMSU_TEST_DATABASE_URL`, `REDIS_URL` unset) | **1055 passed, 8 skipped** (the PostgreSQL-only suites) |
| New: `user_updated` records, refusals, rollback (4 tests) | Pass |
| `test_admin_account_edit_and_audit_search.py` | Updated for the intended contract: 27 action types, a really unknown type for the 422 check, old row fields kept plus target fields |
| `test_masterlist_import.py`, #30's setup-email test | Now decodes the MIME parts (the 2026-10-21 template encodes them) |
| **PostgreSQL 18.6**, throwaway local cluster (temporary databases only) | **22 passed, 0 skipped**: `test_admin_audit_migration` (upgrade, model match, both downgrade paths), `test_alembic_migrations` (whole chain to `61330560eec5`), the 4 concurrency suites and `test_redis_tls`. Production is 17.6; no 17 run |
| Frontend `npm run lint` / `npm run build` | Pass |

### Next
1. **Errol:** Render manual deploy. In the log, look for `Running upgrade 5e8a1c7d9b42 -> 61330560eec5`. Then edit a test account and check the Audit tab shows "User updated" with the account's name.
2. Item 2 (practice submit waits on Judge0) is unblocked: its migration chains after `61330560eec5`.
3. PR #30 can be closed as superseded.

## Demo seed: a semester in use, admin kept (2026-10-22)

_Errol asked for realistic demo data that keeps the admin account. He runs the reset against Supabase himself; nothing here touched production._

### What changed
- **`backend/seed.py` was rewritten; `backend/seed_content.py` is new.** `seed_dummy.py` and `seed_task.py` (load-test stubs: "Load Testing 101", `student1@…`, a shared weak password) were removed.
- **`python seed.py --reset`:**
  - shows the target database (never the password), the admins kept and what will be deleted, and asks you to type the database host;
  - refuses unless the database is on the current Alembic head;
  - then, in **one transaction**, empties every table except `users` (admin rows kept) and `system_settings`, and seeds the demo. Any failure rolls everything back.
- **The demo, about ten weeks into the term:**
  - 5 faculty and 183 students (fictional Kapampangan and Filipino names);
  - 6 active classes (CC 102 for BSIT 1-A/1-B, BSCS 1-A and BSIS 1-A; CC 104 for BSCS 2-A; IT 213 for BSIT 2-B) and last semester's archived CC 103;
  - 38 activities with scenarios, test cases and structure rules: released, in review, open and one scheduled;
  - about 880 submissions with their coding sessions, submit runs, evaluations and similarity;
  - grades (released and unreleased), practice progress, in-app notifications, and an audit trail with MIS masterlist imports and sign-ins.
- **Evaluations use the app's own code** (`evaluate_ast_details`, `find_highest_similarity`). Submit-run output comes from running the seed's own code templates. `python seed.py --self-check` checks that every code variant behaves as labelled.
- **Demo accounts** share one password (random, or `DEMO_PASSWORD`), written to `~/Documents/psu_demo_accounts.md` (mode 600), never to the repo. No email is sent.
- **`entrypoint.sh`** (local Docker stack) now runs `seed.py --reset --unattended`, and only when `PAMSU_ALLOW_DATABASE_RESET=true`. That mode refuses unless `PAMSU_ENVIRONMENT` is development or test.

### Verified (throwaway local PostgreSQL 18.6)
- Seeded in about 30 s:
  - the admin row was byte-for-byte unchanged and older accounts were removed;
  - no timestamp is in the future, and no grade predates its activity's due date.
- A second run on seeded data works.
- **30/30** GET endpoints used by the admin, instructor and student screens return 200 on the seeded data.
- The guards refuse:
  - the wrong host;
  - no admin (outside Docker);
  - `--unattended` without its flags;
  - a database one migration behind.

### Done (reported by Errol, 2026-10-22)
- **Render deployed `dev`:** migration `61330560eec5` is applied in production.
- **Production was reset to the demo semester** with `seed.py --reset`, keeping the admin account and system settings.

## October 22 handoff: owner decisions, practice submit, MIS features, backups (2026-10-22)

_Branch `dev`, starting from `6c8db89` (Errol's latest, fast-forwarded before any change). Januard set a **zero-budget policy** and delegated the remaining owner decisions to engineering judgment. Nothing here was pushed, deployed or run against production. All database work used throwaway local databases._

### The 2026-10-22 "Still open" list: status now
| # | Item | Status |
|---|---|---|
| 1 | Admin actions not audited | **Done earlier** (Errol, `61330560eec5`, deployed) |
| 2 | Practice submit waits on Judge0 (up to 15 s) | **Fixed in code.** Migration `b7e4c2a91f03`. Goes live at Errol's next Render deploy |
| 3 | PostgreSQL 17 run | **Done.** Migration and concurrency suites on **PostgreSQL 17.6** (production's version) and 18.4, throwaway local clusters: **28 passed on each**. The upgrade also ran on the demo semester's data (see "PostgreSQL 17.6 run") |
| 4 | Release blockers | **Code side ready.** SMTP: [rotation steps](docs/operations/smtp-key-rotation.md) and `ops/check_smtp.py`, but **Errol must rotate the key**. Backup: tool and workflow ready, but **need the secrets** (below). Production smoke test: **not run** |
| 5 | Legacy `/execution/submissions/` routes; who creates submit runs | **Decided and done** (removed; `POST /submissions/` only) |
| 6 | Enrollment questions; instructor temporary-password email | **Decided and done** |
| 7 | Gemini billing; AGENTS.md | Billing: **no** (zero budget); the approved `gemini-3.6-flash` fallback stays. AGENTS.md updated **locally**: it is gitignored, so Errol must update his own copy |
| 8 | Optional UI | **Done:** "Show guests", "Re-apply pending", School ID editing, a new queued-enrollments panel. **Not done (not requested):** admin dark mode, the `PageShell` rebuilds |
| 9 | `ClassroomResponse` requires `section` | **Fixed** |

### Decisions taken (owner delegated, 2026-10-22)
| Question | Decision | Why |
|---|---|---|
| Remove the legacy `/execution/submissions/` routes? | **Removed** (both now 404) | Dependency check: the frontend, `qa/`, `load_tests/` and `mock_judge0` never call them; only tests did. They duplicated `POST /submissions/`, `GET /submissions/{id}` and `GET /instructors/submissions/{id}`, and the POST was the item 7 bypass |
| Should `POST /submissions/` create its own execution request? | **Yes, and only it.** `POST /execution/requests/` now refuses `request_kind: "submit"` (409) | Each attempt gets exactly one paid Judge0 submit run, made from the stored snapshot. The frontend only sends `run` |
| Rate limit on run requests | **5 per 10 s per student** (`POST /execution/requests/`) | Each one is a paid Judge0 run, and the route had no limit |
| Suspended students in bulk enroll (enrollment decision 1) | **Refused and reported** (`suspended` count); nothing queued | Same rule as the pending-enrollment retry |
| Pending rows for archived classes (2) | **Kept; applied after reactivation** (unchanged, confirmed) | Keeps the instructor's intent without blocking |
| Class capacity (3) | **None** (no schema change) | No institutional requirement yet |
| Guests and pending enrollments (4) | **Self-service guests are never enrolled** (bulk enroll counts them as `ineligible`; the retry refuses them). Admin-created guests stay normal students | 2026-10-19 owner decision: guests stay in the sandbox |
| Who sees queued addresses (5) | **MIS only:** new `GET /admin/pending-enrollments`. Instructors keep the counts in their bulk-enroll result. No notifications | Addresses are personal data. Instructors see the student in the roster once enrolled |
| School ID matching for pending rows (6) | **No:** email only | Would need a migration and an instructor input |
| Instructor temporary-password email | **No password is ever emailed to faculty.** The account is created without a usable password, and the welcome email links to "Forgot password?" (one-time code) | Plaintext passwords in email are the weak point. Same pattern as masterlist students. MIS keeps "Reset password" as a fallback |

The single-student form (`POST /admin/students`) still emails the MIS-chosen temporary password, per Januard's 2026-10-21 spec. Switching it to the same password-free invite is recommended, as a separate change.

### 1. Practice submit returns at once (item 2, the 3-second rule)
- **Flow** (same pattern as the IDE Run button):
  1. `POST /practice/tasks/{id}/submit` saves a `pending` attempt and queues `dispatch_practice_attempt` (Celery). It answers immediately with `status: "pending"` and the `attempt_id`.
  2. The worker sends the code to Judge0 with a callback URL (`WEBHOOK_BASE_URL/practice/internal/judge0-callback?attempt_id=…&correlation_id=…`).
  3. Judge0 calls back. The callback records the verdict (status 3 plus the structure check) and counts the try in `practice_progress`.
  4. The page polls `GET /practice/attempts/{id}` every 1.5 s.
- **Cost unchanged:** one Judge0 submission per attempt. Judge0 itself is never polled (that would be a paid request each time).
- **States:** `pending`, `completed` (judged), or `failed`.
  - `failed` means the code never ran: queue down, Judge0 error status 13/14/missing, or no answer within 120 s (closed when the page next reads it).
  - Failed and pending attempts don't count as tries, are left out of the growth statistics, and get no AI hint (409 while pending, 400 when failed).
- **The callback is public** (Judge0 sends no credentials). It is bound to one attempt by a random UUID `correlation_id` that only the server and Judge0 see; students never receive it.
  - An unknown pair gets 404.
  - A finished attempt gets 409, and nothing changes.
- **Concurrency** (`services/practice_evaluation_service.py`):
  - the attempt row is locked `FOR UPDATE`, so a duplicate delivery is applied once;
  - the progress row is locked too, and when no row exists yet a savepoint plus the `(student_id, task_id)` unique constraint let two simultaneous verdicts both count, in one row;
  - the stale-attempt expiry is a conditional `UPDATE … WHERE status = 'pending'`, so it can't overwrite a verdict being recorded.
- **Migration `b7e4c2a91f03`** (chained after `61330560eec5`; single head):
  - `practice_attempts.status` VARCHAR(20) NOT NULL DEFAULT `'completed'` + `ck_practice_attempts_status`;
  - `correlation_id` VARCHAR(36), unique;
  - `completed_at` timestamptz.
  - **Additive only.** Existing rows read as `completed` (they were judged synchronously), and the old code still works on the new schema during Render's switch-over.
  - `lock_timeout` 10 s. PostgreSQL 11+ adds the defaulted column without rewriting the table.
  - Downgrade drops the columns, and refuses while any attempt is pending or failed.
- **Measured locally** (scratch copy with a fake Judge0 that answers after 2 s): submit answers in **149 ms** (it used to wait up to 15 s). The page shows "Checking…", then "Passed".
- **Frontend** (`PracticeWorkspace.jsx`):
  - polls the attempt and tolerates up to two failed polls in a row;
  - shows "could not be checked, does not count" for `failed`;
  - **still works with today's production backend**, which answers with the verdict and no `status`.

### 2. MIS features (item 8)
- **Show guests** (Student directory switch): uses `GET /admin/users?include_guests=true`, which production already has.
  - Guest rows get a "Guest" badge and only Suspend/Activate.
  - Account lists now include `is_guest`; older servers fall back to the `guest_`/`GST` pattern.
- **Re-apply pending** on each active student row: calls `POST /admin/students/{id}/pending-enrollments/apply`, which production already has. It reports classes joined and classes still waiting.
- **Queued class enrollments** panel ("Ready to apply" / "Waiting", per-row Apply), from the new admin-only `GET /admin/pending-enrollments`.
  - Each row says why it waits: no account yet, class archived, or account suspended.
  - Until Errol deploys, the panel says it needs the server update.
- **School ID editing** (Edit dialog, students only): `PATCH /admin/users/{id}` accepts `school_id`.
  - Format: 10 digits or `2026-00001`.
  - 409 if another account uses it; faculty get 400.
  - Audited as `user_updated` with `changed_fields: ["school_id"]`, never the value.
  - Older servers get a clear "needs the latest server update" message.
- **Faculty form:** no password field. With an older server (422 "password missing"), it retries once with a generated temporary password and shows it, the 2026-10-21 behaviour. Audit metadata records `sign_in_setup` (`set_by_instructor` / `set_by_admin`).
- **Instructor bulk enroll** result shows the new "Suspended account" count, and the ineligible text now mentions guests.
- **Browser-checked** on a scratch copy (SQLite, ports 8021/5181, fake Judge0): every item above, including a duplicate School ID refused under the field. No console errors besides that expected 409.

### 3. `ClassroomResponse.section` (item 9)
Optional in responses, so a class with no section (seed or SQL) no longer makes `GET /classrooms/` or `GET /classrooms/mine` return 500. Create and update still require a section.

### 4. Backups at zero cost (release blocker)
- **`ops/backup_database.py`**: `backup | verify | decrypt | restore | generate-key`.
  - `pg_dump` custom format of the `public` schema, after checking that pg_dump's version is at least the server's.
  - Refuses a dump without `users`/`alembic_version` data.
  - Fernet encryption before the file reaches the output folder.
  - JSON manifest (SHA-256, revision; no data) and `--keep N` rotation.
  - `restore` only into an **empty** database, in one transaction.
  - The URL is never printed or put on a command line (libpq variables).
- **`.github/workflows/database-backup.yml`**: nightly at 02:30 Manila, plus a manual run.
  - Installs the PostgreSQL 17 client and uploads only the encrypted dump (artifact kept 14 days).
  - **Off until** repository variable `DATABASE_BACKUP_ENABLED=true` and secrets `BACKUP_DATABASE_URL` (Supabase **Session pooler**, port 5432: GitHub runners are IPv4-only) and `BACKUP_ENCRYPTION_KEY` exist.
  - The repository is **public** (artifacts downloadable by anyone signed in), so the run refuses to start without the key. A private copy of the workflow is the stronger option (documented).
- **Not Render cron:** it has no free tier ($1/month minimum per cron job), and free instances have no persistent disk.
- **Tested** on PostgreSQL 18.4 (throwaway):
  - backup → verify → decrypt → restore into an empty database: 250/250 users, revision `b7e4c2a91f03`, `alembic check` clean;
  - rotation;
  - wrong key refused;
  - no key with `--require-encryption`: nothing dumped;
  - restore over a database with tables: refused.
  - Plus 10 unit tests.
- Guide: [`docs/operations/database-backups.md`](docs/operations/database-backups.md). It includes **"back up by hand before every deploy with a migration"** (this one included).

### 5. SMTP/Brevo key rotation (release blocker)
[`docs/operations/smtp-key-rotation.md`](docs/operations/smtp-key-rotation.md):
1. generate a new key in Brevo;
2. check it with `ops/check_smtp.py` (asks for the key without echoing it; logs in; optional test email; prints only SMTP codes);
3. set `SMTP_PASS` on Render, then Save and deploy;
4. test "Forgot password?";
5. delete the old key.

Also covers sender verification and the free plan's 300 emails/day. **Still to be done by Errol.**

### 6. Gemini fallback and AGENTS.md (item 7)
The fallback to `gemini-3.6-flash` (only on 503/429 from 3.8 Flash) is now the written rule. AGENTS.md is in `.gitignore`, so the update exists only in this machine's local copy; Errol must make the same change in his. Billing stays off under the zero-budget policy. If both free quotas run out, the tutor reports "busy" and students can retry.

### Tests
| Run | Result |
|---|---|
| Baseline at `6c8db89` before any change (SQLite, `REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS=0.05`, see note) | 1053 passed, 11 skipped |
| Full backend suite after the changes (SQLite, same setting) | **1104 passed, 17 skipped, 0 failed** (skipped: the PostgreSQL-only suites, run separately below, and 3 tests that need `google-genai`, which this local venv lacks) |
| **PostgreSQL 18.4** throwaway cluster: whole migration chain (up, down to base, up, `alembic check`), `test_admin_audit_migration`, new `test_practice_attempt_status_migration`, new `test_practice_callback_concurrency`, the 4 existing concurrency suites, `test_redis_tls` | **28 passed** |
| **PostgreSQL 17.6** (official EDB binaries, the production version): the same 28 tests | **28 passed**, 0 skipped |
| Concurrency suites repeated 5 times | 5/5 green on 18.4 (practice, submission, grade) and on 17.6 (all five suites) |
| Frontend `npm run lint` / `npm run build` | Pass |

- **New tests:** `test_practice_async_submit.py` (23), `test_practice_callback_concurrency.py` (3, PostgreSQL), `test_practice_attempt_status_migration.py` (3, PostgreSQL), `test_mis_enrollment_followups.py` (19), `test_backup_database_script.py` (10).
- **Rewritten:** `test_legacy_submission_route.py` (the routes stay gone; one submit run per attempt; run-request limit).
- **Updated to the new contracts:**
  - `test_api_workflow`, `test_coding_session_workflow`, `test_execution_workflow`, `test_openapi_contracts` (no legacy routes; no client submit runs);
  - `test_practice_ai_tutor`, `test_default_ast_strictness` (callback flow);
  - `test_provisioning_email` (faculty email has no password);
  - `test_pending_enrollment_workflow` (`suspended` field);
  - `test_admin_account_edit_and_audit_search` (school ID now editable);
  - `test_admin_audit_migration` (`61330560eec5` is no longer head).
- **Note for Windows test runs:** connecting to the closed Redis port in `conftest.py` takes ~2 s per call on Windows, so the suite took ~45 min. With `REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS=0.05` (an existing setting) it takes ~9 min, with the same "Redis down" behaviour.

### PostgreSQL 17.6 run (owner approved the download, 2026-10-22)
- **Binaries:**
  - EDB's `postgresql-17.6-1-windows-x64-binaries.zip` from `get.enterprisedb.com`, the Windows source postgresql.org links to;
  - 329,891,687 bytes; SHA-256 `d378882abd001a186735acd6f6ba716bca6ccd192e800412d4fd15ed25376b3e`.
  - EDB doesn't code-sign the individual binaries (the installed 18.4 isn't signed either).
  - Kept in the session scratchpad only: nothing installed, no Windows service.
- **Cluster:** throwaway, `127.0.0.1:55417`, temporary data folder, stopped afterwards. No deadlock or crash in its log.
- **Suites:** 28 passed, 0 skipped. The concurrency suites passed 5 times in a row.
- **Backup tool on 17:**
  - pg_dump 17.6 → verify → restore into an empty database: 300/300 users, revision `b7e4c2a91f03`, `alembic check` clean;
  - pg_dump 18 against a 17 server is accepted too (newer client).
- **Production-like upgrade:**
  - the demo semester (`seed.py --reset --unattended`: 183 students, 1,862 practice attempts, 1,245 progress rows) was stepped back to `61330560eec5`, production's revision, then upgraded with `alembic upgrade head`;
  - all 1,862 attempts read as `completed`, with `correlation_id`/`completed_at` empty, and `alembic check` is clean;
  - the migration itself takes well under a second: the whole command took 3.5 s, about the same as Alembic's start-up alone (4.5 s).

### What a push of this commit does
- **Vercel (at once):**
  - the practice page keeps working against the current backend (it still answers synchronously);
  - "Show guests" and "Re-apply pending" work immediately;
  - School ID editing, the queued-enrollments panel and password-free faculty invites say "needs the latest server update", or fall back (faculty), until Errol deploys.
- **Render (Errol's Manual Deploy):**
  - **take a backup first** (`ops/backup_database.py`, guide §3);
  - the deploy runs migration `b7e4c2a91f03` (look for `Running upgrade 61330560eec5 -> b7e4c2a91f03`).
  - The Celery worker in the same container picks up `dispatch_practice_attempt`.
  - `WEBHOOK_BASE_URL` must stay set (the IDE Run already needs it).
  - **After deploying, check practice:** submit a correct and a wrong solution on the live site. Both should finish within a few seconds, and the wrong one should show the AI Tutor.
- Browsers with an old cached bundle (PWA) show "Not passed yet / Checking your code…" without polling until they reload. Short-lived, because Vercel deploys before Errol does.

### Files
- **Backend:**
  - `alembic/versions/b7e4c2a91f03_track_practice_attempt_status.py` (new);
  - `app/services/practice_evaluation_service.py` (new);
  - `app/models/domain_models.py`, `app/routers/practice.py`, `app/routers/execution.py`, `app/routers/submissions.py`, `app/routers/admin.py`;
  - `app/schemas/practice_schema.py`, `app/schemas/enrollment_schema.py`, `app/schemas/classroom_schema.py`;
  - `app/services/classroom_service.py`, `app/services/guest_service.py`, `app/tasks/celery_worker.py`;
  - tests as listed above.
- **Frontend:** `features/practice/PracticeWorkspace.jsx`, `features/admin/AdminDashboard.jsx`, `components/modals/BulkEnrollModal.jsx`.
- **Operations (new):** `ops/backup_database.py`, `ops/check_smtp.py`, `.github/workflows/database-backup.yml`, `docs/operations/database-backups.md`, `docs/operations/smtp-key-rotation.md`.
- **Local only (gitignored):** `AGENTS.md`.

### Next (people)
1. **Januard:** push.
   - Generate the backup key (`ops/backup_database.py generate-key`) and keep a copy offline.
   - Add the two secrets and the variable from guide §2, then run the workflow once.
2. **Errol:**
   - rotate the Brevo key (`docs/operations/smtp-key-rotation.md`);
   - send Januard the Session pooler URI privately;
   - take a manual backup, then Manual Deploy;
   - check the practice page and the admin panel;
   - update his AGENTS.md copy.
3. **Both:** the production smoke test (2026-10-21 list).
4. **Optional:** the same password-free invite for the single-student form.

## October 22 follow-up: closing the known gaps (2026-10-22)

_After `8e9b377`. Januard asked what could still be done about the "known gaps" in `errol_handoff_oct22.md`. Nothing here touched production._

### Fixed
| Gap | What changed |
|---|---|
| **IDE Run: early Judge0 callback overwritten (real bug, found by the new contract test)** | **Before:** `dispatch_to_partner` set `status = "running"` after Judge0 answered its POST. If Judge0's callback had already arrived (a short program on a quiet Judge0), that write replaced `completed` with `running`, and the run looked stuck forever. Its final "failed" write after retries could likewise erase a result.<br>**Now:**<ul><li>"running" is set only on a request that is still `queued`;</li><li>"failed" is set only on a request nothing has answered;</li><li>a retry whose request was already answered sends nothing.</li></ul>No schema change |
| Practice dispatch could send the code twice (two paid runs) | `judge0_dispatch_outcome()` decides what happens after a failed send:<ul><li>**retry** only when Judge0 certainly did not queue the code (connect error, 429, 5xx);</li><li>**fail** at once on another 4xx;</li><li>**wait** when the answer was lost after sending (read timeout, broken connection): the attempt stays pending, and the callback or the 120 s expiry finishes it</li></ul> |
| Practice callback never tested against a Judge0-shaped server | **`mock_judge0/` rewritten** as a Judge0 CE stand-in:<ul><li>`POST /submissions` (`base64_encoded`, `wait`, `expected_output`, `callback_url`), `GET /submissions/{token}`;</li><li>status ids 3/4/5/11;</li><li>a PUT callback with base64 fields, like Judge0.</li></ul>The old mock needed fields the backend never sends. Docker Compose still uses the real Judge0 1.13.1 image.<br>**Results:**<ul><li>new `tests/test_mock_judge0_contract.py` (9 tests): real worker code → mock → real callback routes, for practice (pass, wrong output, runtime error, time limit) and the IDE Run, plus the race regressions;</li><li>**live over real HTTP** (uvicorn backend + uvicorn mock, real task code in threads): practice submits answered in 122–149 ms and finished in 1.4–2.0 s; IDE Run `stdout='Hello, PAMSU\n'`; `POST /submissions/` made exactly one submit run</li></ul> |
| Backup workflow never run on GitHub | New **`.github/workflows/backup-tool-selftest.yml`**:<ul><li>no secrets: a throwaway `postgres:17` service, the same client install and packages as the nightly job;</li><li>back up → verify → restore, then both safety guards;</li><li>runs when the tool or the workflow changes (so on this push), or by hand.</li></ul>Its shell steps were rehearsed on the local 17.6 cluster, including a failure correctly stopping the step |
| Windows test runs took ~45 min | `conftest.py` defaults `REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS` to 0.05 s (same "Redis unavailable" path). Full suite: **6.6 min**, no setting needed |
| 3 AI Tutor SDK tests skipped locally | `google-genai==2.28.0` (the pinned version) installed in the local venv: `test_practice_ai_tutor.py` **39/39, none skipped** |
| Brevo free plan (~300 emails/day) | A masterlist upload that creates more than 250 accounts now shows an amber warning: some welcome emails may not go out today; use "Forgot password?" tomorrow; split large lists. Browser-checked with a 260-row file |

### Looked at and left as is (why)
- **Cached old frontend (PWA):** `registerType: 'autoUpdate'` already swaps in a new bundle on the next page load. Only tabs opened before Vercel deployed `404d88a` and still open at Errol's deploy are affected; a reload fixes them. An hourly forced update was rejected: it could reload a student's page in the middle of coding.
- **IDE Run retries** still resend after a lost answer. Unlike practice, an execution request has no expiry, so not resending could leave a run waiting forever. A duplicate's callback is refused (409), and the race fixes keep the first result.
- **Need people or a decision, not code:**
  - the real RapidAPI Judge0 run (production only: Errol's deploy, then the checks in the handoff);
  - faculty invites until that deploy (the old backend still emails a temporary password);
  - backup artifacts in a public repository (encrypted; a private repository copy is safer);
  - GitHub's 60-day pause of scheduled workflows;
  - the single-student form's emailed password (Januard's 2026-10-21 spec).
- **Local venv ≠ Render:** this machine runs Python 3.13; Render runs 3.11.4. `pip install -r requirements.txt` stops at `greenlet==3.2.5`, which has no Windows build for 3.13, so a few pins differ locally (pydantic 2.13.3, google-auth 2.58.1, anyio 4.13.0). A Python 3.11 venv would match production exactly.

### Tests
| Run | Result |
|---|---|
| Full backend suite (SQLite, no environment settings) | **1127 passed, 14 skipped** (only the PostgreSQL suites), 0 failed |
| New `test_mock_judge0_contract.py` | 9 passed |
| `test_practice_async_submit.py` (+11 for the dispatch outcomes) | 34 passed |
| Live HTTP run, backend + mock Judge0 | practice ×3, IDE Run, submit run: all as expected |
| Frontend lint / build | Pass |

### Files
- **Modified:**
  - `backend/app/tasks/celery_worker.py`
  - `backend/tests/conftest.py`
  - `backend/tests/test_practice_async_submit.py`
  - `mock_judge0/main.py`
  - `frontend/src/features/admin/AdminDashboard.jsx`
  - `docs/operations/database-backups.md`
- **New:**
  - `backend/tests/test_mock_judge0_contract.py`
  - `.github/workflows/backup-tool-selftest.yml`
  - `errol_handoff_oct22.md`, updated to match

### What a push does
- **Vercel:** the masterlist warning.
- **GitHub:** the backup self-test runs once.
- **Render (Errol's deploy):** the IDE Run race fix and the practice dispatch change.
- No migration beyond `b7e4c2a91f03`.

## Student accounts without an emailed password (2026-10-22)

_After `b285d44`. Januard approved switching the single-student form to the same password-free invite as faculty (previously his 2026-10-21 spec emailed the MIS-chosen temporary password)._

- **Backend (`POST /admin/students`):**
  - `password` is optional. Without one, the account gets an unusable password marker.
  - The welcome email **never** contains a password; it links to "Forgot password?" (one-time code), like masterlist accounts and faculty invites.
  - A password sent by an older client is still set, so MIS could hand it over in person, but it is not emailed.
  - Audit metadata adds `sign_in_setup` (`set_by_student` / `set_by_admin`).
  - Queued class enrollments are still joined on creation.
- **Frontend (`AdminDashboard.jsx`):** one `createAccount()` path for both forms.
  - The student form no longer has a password field, and shows the same "No password to share" note.
  - **With today's production backend** (which still requires a password), the form retries once with a generated temporary password and shows it. That is the old behaviour, until Errol deploys.
  - The unused `TemporaryPasswordField` component is removed; "Reset password" in the directory is unchanged.
- **Now no account type ever receives a password by email:** single student, masterlist, or faculty.
- **Verified:**
  - Browser, new backend: a student whose address was queued got the set-your-own-password message and joined the class.
  - Browser, production's current code (`6c8db89`): the old server answered 422 (password missing), then 200 with the generated password, and the fallback message showed.
  - Tests:
    - `test_provisioning_email.py`: the student email is never given a password, with or without one sent;
    - `test_mis_enrollment_followups.py`: a password-free student, its audit metadata and the queued class.
- **Deploy:** frontend at once (Vercel), using the fallback until Errol deploys. Backend at Errol's next deploy. No migration.
- **GitHub:** the backup self-test ran on the `b285d44` push and **passed**. Every step went green: PostgreSQL 17 client install, backup, verify, restore, both guards.
