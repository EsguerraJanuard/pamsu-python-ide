# PAMSU Python IDE — Current AI Handoff

## Mandatory Reading

Before changing code, every AI assistant must read:

1. `docs/ai/PROJECT_CONTEXT.md`
2. `docs/ai/ROADMAP.md`
3. `docs/ai/WORKFLOW.md`
4. `docs/ai/CURRENT_HANDOFF.md`

These repository files are the authoritative source of truth.

---

## Current Repository State

Current local working branch:

```text
review/backend-p15-api-hardening
```

Backend version:

```text
0.15.0
```

Latest completed implementation scope:

- Pillar 15 — API Hardening and Production Readiness
- implementation complete on the local review branch
- final full review-branch regression passed
- review branch has not been pushed

Latest confirmed local commits:

```text
8134462 chore: bump backend version to 0.15.0
2ae65b8 feat: integrate request correlation and structured logging
0145824 feat: harden runtime configuration and request context
570eb4d feat: add student execution request idempotency
a078fad feat: harden pagination and concurrent write safety
ef99380 refactor: centralize bounded pagination and ordering
cdd44eb db: add guarded legacy schema alignment
50772ea build: add Alembic baseline and migration readiness
```

Latest authoritative review-branch regression:

```text
699 passed in 120.22s (0:02:00)
```

The Pillar 15 review branch must remain local.

Do not push the review branch.

Remaining Pillar 15 completion sequence:

1. replace and commit this handoff
2. confirm repository checks
3. merge the review branch locally into `dev`
4. rerun the complete backend regression on `dev`
5. push only `dev`
6. confirm the working tree is clean

---

## Pillar 15 Objective

Pillar 15 hardens the existing FastAPI backend for deterministic API behavior, safer concurrent writes, replay-safe student execution requests, migration readiness, validated runtime configuration, safe security middleware, and privacy-safe request observability.

Implemented areas:

- centralized bounded pagination
- deterministic ordering for paginated collections
- transactional row locking for concurrent official-attempt allocation
- transactional row locking for concurrent manual grading
- replay-safe partner execution update handling under concurrency
- student-scoped execution-request idempotency
- Alembic baseline and migration smoke verification
- guarded alignment for legacy development schemas
- evidence-based database index cleanup and additions
- N+1 query review for high-use listing services
- validated immutable application settings
- environment-controlled API documentation
- explicit CORS allowlists
- optional trusted-host enforcement
- correlation-ID middleware
- privacy-safe structured request logging
- backend version `0.15.0`

Pillar 15 does not execute student Python code inside FastAPI.

Student execution remains exclusive to the partner-owned isolated sandbox contract.

---

## Bounded Pagination and Deterministic Ordering

Implemented shared pagination support:

```text
backend/app/core/pagination.py
```

Integrated into:

- notification listing
- instructor review queue
- gradebook listing
- reporting queries
- audit-record listing

Behavior:

- page and page-size values are validated and bounded
- collection ordering is deterministic
- stable tie-breakers prevent duplicate or skipped rows between pages
- pagination behavior is centralized instead of reimplemented per service
- ownership and authorization filters remain enforced before results are returned

Verified focused results included:

```text
77 passed in 9.10s
182 passed in 13.40s
179 passed in 13.42s
```

---

## Concurrent Write Safety

### Submission Attempt Allocation

Updated submission workflows serialize attempt allocation by locking the relevant activity task row before allocating the next attempt number.

Implemented verification:

```text
backend/tests/test_submission_concurrency.py
```

Confirmed results:

```text
Focused concurrency test: 1 passed
Related submission regression: 22 passed
```

Concurrent accepted submissions do not receive the same attempt number.

Official-attempt behavior remains backend-controlled.

### Manual Grade Writes

Updated evaluation workflows lock the target submission and existing instructor-grade row within the grading transaction.

Implemented verification:

```text
backend/tests/test_grade_concurrency.py
```

Confirmed results:

```text
Focused concurrency test: 1 passed
Related evaluation and gradebook regression: 40 passed
```

Official grades remain manually controlled by authorized instructors.

### Partner Result Replay Concurrency

Partner execution result processing performs a post-lock replay check before accepting a new update record.

Implemented verification:

```text
backend/tests/test_partner_execution_concurrency.py
```

Confirmed results:

```text
Focused concurrency test: 1 passed
Related partner execution regression: 15 passed
```

Concurrent identical partner retries remain replay-safe.

---

## Student Execution Request Idempotency

Implemented across:

```text
backend/app/models/domain_models.py
backend/app/schemas/execution_schema.py
backend/app/services/execution_service.py
backend/app/routers/execution.py
backend/alembic/versions/4b3a1d9e7c25_add_execution_request_idempotency.py
```

Student execution-request behavior:

- accepts optional `Idempotency-Key`
- requires the key to be a UUID when supplied
- scopes idempotency to the authenticated student
- stores a normalized UUID and SHA-256 request digest
- never stores plaintext source-code content in idempotency metadata
- identical retries return the existing execution request
- key reuse with changed resolved request content returns `409 Conflict`
- malformed keys return `400 Bad Request`
- concurrent identical retries create one execution request
- concurrent identical retries increment the backend-controlled run counter once
- response schemas do not expose internal idempotency metadata
- response schemas do not expose partner-only execution fields

Confirmed verification included:

```text
Migration tests: 3 passed in 7.02s
HTTP workflow: 11 passed in 16.04s
Combined execution/idempotency regression: 80 passed in 24.18s
```

---

## Alembic Baseline and Migration Readiness

Alembic configuration:

```text
backend/alembic.ini
backend/alembic/env.py
```

Migration chain:

```text
18d3ef8f020d  baseline
4b3a1d9e7c25  add execution request idempotency
9f2c6e4a1b7d  optimize proven index coverage
```

Current migration head:

```text
9f2c6e4a1b7d
```

Implemented migration verification:

```text
backend/tests/test_alembic_migrations.py
```

Confirmed migration state:

```text
alembic heads: 9f2c6e4a1b7d (head)
alembic check: No new upgrade operations detected.
Migration tests: 3 passed in 5.28s
```

The Alembic baseline represents 20 application tables.

Migrations do not run automatically during FastAPI import.

Run migrations explicitly from `backend`:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
```

Check for model-to-migration drift:

```powershell
.\venv\Scripts\python.exe -m alembic check
```

---

## Guarded Legacy Schema Alignment

Implemented:

```text
backend/app/db/upgrade_p15_legacy_schema.py
```

Purpose:

- detect development databases created before the Alembic baseline
- identify required missing columns without destructive guessing
- apply only guarded known schema additions
- permit Alembic stamping and migration verification after alignment
- remain explicit and manually invoked
- avoid running during application import or startup

Observed legacy alignment:

```text
Initial dry run: 31 missing columns
Apply run: completed
Post-apply dry run: 0 missing columns
```

A local PostgreSQL backup was created before applying the legacy alignment.

No database credentials are recorded in this handoff.

---

## Query and Index Review

Reviewed high-use services for N+1 behavior:

- gradebook
- review queue
- reporting
- audit records
- notifications

Result:

- no proven N+1 pattern remained in the reviewed services
- listing workflows use explicit joins, scalar queries, or bounded aggregate queries
- no broad speculative eager-loading refactor was introduced

Implemented index migration:

```text
backend/alembic/versions/9f2c6e4a1b7d_optimize_proven_index_coverage.py
```

Added composite execution-request indexes:

```text
ix_execution_requests_student_queued
ix_execution_requests_task_queued
```

Removed redundant standalone or primary-key-equivalent indexes only where existing constraints or stronger composite indexes already provided equivalent coverage.

Confirmed affected regression:

```text
102 passed in 9.90s
```

---

## Validated Runtime Configuration

Implemented:

```text
backend/app/core/config.py
```

Updated consumers:

```text
backend/app/core/database.py
backend/app/core/security.py
backend/app/integrations/partner_auth.py
backend/app/main.py
```

Validated settings include:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `PAMSU_ENVIRONMENT`
- `PAMSU_PARTNER_EXECUTION_TOKEN`
- `PAMSU_CORS_ALLOWED_ORIGINS`
- `PAMSU_CORS_ALLOW_CREDENTIALS`
- `PAMSU_ALLOWED_HOSTS`
- `PAMSU_ENABLE_API_DOCS`
- `PAMSU_LOG_LEVEL`
- `PAMSU_CORRELATION_ID_HEADER`

Behavior:

- required database and JWT settings fail fast
- JWT secret length and algorithm are validated
- token expiration is bounded
- application environment is restricted to approved values
- CORS origins are normalized, deduplicated, and validated
- wildcard CORS origins are rejected
- production CORS origins require HTTPS
- credentialed CORS requires explicit origins
- trusted-host entries accept hostnames only
- production wildcard trusted hosts are rejected
- API documentation defaults to disabled in production
- log level and correlation-header name are validated
- sensitive values use secret wrappers and are excluded from representations
- configuration caching responds safely to test-time environment changes
- missing or short partner token does not block unrelated core settings
- partner endpoints and readiness preserve their existing `503` contract for missing or short partner configuration

Confirmed configuration regression:

```text
45 passed in 2.95s
56 passed in 3.63s
73 passed in 19.00s
```

---

## CORS, Trusted Hosts, and Documentation Exposure

Updated:

```text
backend/app/main.py
```

Dedicated tests:

```text
backend/tests/test_application_security_config.py
```

Behavior:

- CORS middleware is installed only when explicit origins are configured
- allowed origins are exact, not wildcard
- allowed methods and request headers are explicit
- untrusted origins do not receive approved CORS access
- trusted-host middleware is installed only when a host allowlist is configured
- invalid host headers return `400`
- Swagger UI, ReDoc, and OpenAPI routes are environment-controlled
- production defaults disable documentation routes
- development defaults keep documentation routes available
- unsafe wildcard configuration blocks application startup
- startup failures do not disclose secret values

Confirmed dedicated result:

```text
7 passed in 14.97s
```

---

## Correlation IDs and Privacy-Safe Structured Logging

Implemented:

```text
backend/app/core/request_context.py
backend/app/main.py
```

Every HTTP request:

- accepts the configured correlation-ID header
- preserves only valid UUID correlation IDs
- replaces missing, blank, or malformed values with a backend-generated UUID
- exposes the normalized correlation ID through `request.state`
- exposes the active value through a request-local `ContextVar`
- returns the correlation ID in the configured response header
- resets request-local context after completion

Structured request log fields are limited to:

- timestamp
- level
- event
- correlation ID
- HTTP method
- URL path
- status code
- duration in milliseconds

Request logs exclude:

- query strings
- request bodies
- response bodies
- headers
- cookies
- authorization values
- JWTs
- partner tokens
- OTP values
- database URLs
- source code
- standard input
- stdout or stderr
- hidden tests
- grades
- AST findings
- similarity details
- clipboard contents
- pasted text
- browsing history
- individual keystrokes
- screen, webcam, or microphone data
- raw exception messages and tracebacks

Confirmed middleware verification:

```text
Request-context tests: 10 passed in 0.54s
Integrated middleware/security tests: 28 passed in 20.15s
```

Observed health smoke:

```text
HTTP status: 200
Response state: healthy
Response correlation ID: generated UUID
Structured request log correlation ID matched the response header
```

---

## Main Application and OpenAPI

Updated:

```text
backend/app/main.py
backend/tests/test_system_health.py
backend/tests/test_openapi_contracts.py
backend/tests/test_classroom_openapi_contracts.py
```

Backend version:

```text
0.15.0
```

System endpoints remain:

```text
GET /
GET /health
GET /ready
```

OpenAPI and system contracts now report version:

```text
0.15.0
```

Confirmed version-contract results:

```text
System health/version contract: 11 passed in 1.17s
Classroom OpenAPI contract: 11 passed in 1.06s
OpenAPI contracts: 32 passed in 2.15s
Combined version-contract group: 54 passed in 2.74s
```

---

## Pillar 15 Files

Primary implementation and migration files:

```text
backend/alembic.ini
backend/alembic/env.py
backend/alembic/versions/18d3ef8f020d_baseline.py
backend/alembic/versions/4b3a1d9e7c25_add_execution_request_idempotency.py
backend/alembic/versions/9f2c6e4a1b7d_optimize_proven_index_coverage.py
backend/app/core/config.py
backend/app/core/database.py
backend/app/core/pagination.py
backend/app/core/request_context.py
backend/app/core/security.py
backend/app/db/upgrade_p15_legacy_schema.py
backend/app/integrations/partner_auth.py
backend/app/main.py
backend/app/models/domain_models.py
backend/app/services/audit_service.py
backend/app/services/evaluation_service.py
backend/app/services/execution_service.py
backend/app/services/gradebook_service.py
backend/app/services/notification_service.py
backend/app/services/reporting_service.py
backend/app/services/review_queue_service.py
backend/app/services/submission_service.py
```

Primary Pillar 15 tests:

```text
backend/tests/test_alembic_migrations.py
backend/tests/test_application_security_config.py
backend/tests/test_config.py
backend/tests/test_grade_concurrency.py
backend/tests/test_partner_auth.py
backend/tests/test_partner_execution_concurrency.py
backend/tests/test_pagination.py
backend/tests/test_request_context.py
backend/tests/test_security.py
backend/tests/test_submission_concurrency.py
backend/tests/test_system_health.py
backend/tests/test_openapi_contracts.py
backend/tests/test_classroom_openapi_contracts.py
```

Documentation:

```text
docs/ai/CURRENT_HANDOFF.md
```

Local environment files, database files, backups, caches, and virtual environments must not be committed.

---

## Verified Pillar 15 Results

The following results were explicitly observed during Pillar 15:

```text
Pagination verification: 77 passed in 9.10s
Pagination-related regression: 182 passed in 13.40s
Pagination-related regression: 179 passed in 13.42s
Submission concurrency: 1 passed
Submission-related regression: 22 passed
Grade concurrency: 1 passed
Evaluation/gradebook regression: 40 passed
Partner execution concurrency: 1 passed
Partner execution regression: 15 passed
Idempotency migration verification: 3 passed in 7.02s
Execution idempotency HTTP workflow: 11 passed in 16.04s
Execution/idempotency combined regression: 80 passed in 24.18s
Index/migration verification: 3 passed in 5.28s
Index-affected regression: 102 passed in 9.90s
Configuration/security regression: 12 passed in 1.36s
Configuration suite: 45 passed in 2.95s
System/config/security group: 56 passed in 3.63s
Application security configuration: 7 passed in 14.97s
Request-context middleware: 10 passed in 0.54s
Integrated middleware/security group: 28 passed in 20.15s
Complete configuration/request-hardening group: 73 passed in 19.00s
System health/version contract: 11 passed in 1.17s
Classroom OpenAPI contract: 11 passed in 1.06s
OpenAPI contracts: 32 passed in 2.15s
Combined version-contract group: 54 passed in 2.74s
Complete backend regression before final version contract: 699 passed in 129.88s
Final complete backend regression after version 0.15.0: 699 passed in 120.22s
```

The authoritative current review-branch regression is:

```text
699 passed in 120.22s (0:02:00)
```

Do not replace it with an estimate.

---

## Permanent Authorization, Academic, Execution, and Privacy Boundaries

- Registration accepts only `@pampangastateu.edu.ph`.
- School ID is exactly 10 digits.
- School ID is stored as a string.
- School ID is unique.
- Roles are controlled only by the backend allowlist.
- OTP verification remains required.
- Plaintext OTP values are never persisted, logged, or returned.
- Submission attempts are immutable.
- The latest accepted attempt becomes official.
- Official grades are manually controlled by instructors.
- AST, Jaccard similarity, execution, coding-session, and local LLM indicators remain review-only.
- Automated indicators never assign grades.
- Local LLM output never assigns grades.
- Automated indicators never determine plagiarism, cheating, copying, or misconduct.
- Local LLM output never determines plagiarism, cheating, copying, or misconduct.
- Reports never create automated rankings based on behavioral or review indicators.
- Paste policy remains `internal_only` or `disabled`.
- Blocked-paste telemetry stores count and timestamp only.
- Clipboard contents and pasted text are never stored.
- Browsing history is never collected.
- Screen, webcam, and microphone recording are prohibited.
- Individual keystroke collection is prohibited.
- Student Python code never executes inside React or FastAPI.
- Student code executes only through the partner-owned isolated sandbox worker.
- Partner result updates require authenticated trusted integration.
- Partner result retries remain replay-safe and idempotent.
- Student execution retries remain student-scoped and idempotent when an idempotency key is supplied.
- Reporting and exports remain ownership-safe.
- Raw source code remains excluded from gradebook CSV exports.
- Health, readiness, startup errors, OpenAPI, and request logs never expose credentials or connection details.
- Request logs never contain request bodies, response bodies, query strings, or sensitive headers.

---

## Verification Commands

From the repository root:

```powershell
git branch --show-current
```

Expected:

```text
review/backend-p15-api-hardening
```

From `backend`, run the complete regression:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Latest verified review-branch result:

```text
699 passed in 120.22s (0:02:00)
```

Verify migration state:

```powershell
.\venv\Scripts\python.exe -m alembic heads
.\venv\Scripts\python.exe -m alembic current
.\venv\Scripts\python.exe -m alembic check
```

Expected head:

```text
9f2c6e4a1b7d
```

Expected drift result:

```text
No new upgrade operations detected.
```

Verify application health and correlation response:

```powershell
.\venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from app.main import app; r=TestClient(app).get('/health'); print(r.status_code, r.headers.get('X-Correlation-ID'), r.json()['status'])"
```

Expected format:

```text
200 <generated-UUID> healthy
```

Return to the repository root:

```powershell
cd ..
```

Run repository checks:

```powershell
git diff --check
git status --short
```

Do not claim final Pillar 15 completion until:

- this handoff is committed
- the review branch remains local
- the review branch is merged locally into `dev`
- the complete regression passes again on `dev`
- only `dev` is pushed
- the working tree is clean

---

## Final Pillar 15 Git Procedure

Stage the handoff only.

Do not use:

```powershell
git add .
```

From the repository root:

```powershell
git add -- docs/ai/CURRENT_HANDOFF.md
git diff --cached --check
git diff --cached --stat
git commit -m "docs: complete pillar 15 handoff"
```

Do not push the review branch.

Merge locally into the updated `dev` branch:

```powershell
git switch dev
git fetch origin dev
git merge --ff-only origin/dev
git merge --no-ff review/backend-p15-api-hardening
```

Run the complete backend regression again on `dev`:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
cd ..
```

Do not push until the `dev` regression is green.

Push only `dev`:

```powershell
git push origin dev
```

Confirm the final repository state:

```powershell
git status --short
git log -5 --oneline
```

The review branch remains local and must not be pushed.

---

## Next Pillar

Exact roadmap entry:

```text
Pillar 16 — V-Model Verification and Release Candidate
Version: 1.0.0-rc1
Local branch: review/backend-p16-release-candidate
Status: Planned
```

Scope:

- requirements-to-test traceability matrix
- end-to-end backend acceptance scenarios
- complete authentication, classroom, activity, submission, execution, session, evaluation, grading, notification, audit, reporting, and partner-contract verification
- privacy and security negative tests
- migration verification
- OpenAPI contract freeze
- frontend and partner handoff packages
- changelog and release notes

Definition of done:

- all approved requirements map to passing tests
- zero unresolved high-severity defects
- release-candidate contracts frozen

The roadmap excerpt does not list separate Pillar 16 exclusions.

Do not infer new feature scope beyond the stated Pillar 16 verification and release-candidate work.

The roadmap states that the later final release contains no new features and is limited to release-candidate fixes, documentation, migration corrections, contract-preserving security fixes, final changelog, and approved release tagging.

Before starting Pillar 16:

1. complete the Pillar 15 merge and push through `dev`
2. confirm the `dev` regression is green
3. reread `docs/ai/PROJECT_CONTEXT.md`
4. reread `docs/ai/ROADMAP.md`
5. reread `docs/ai/WORKFLOW.md`
6. create the next local review branch from updated `dev`
7. do not push the Pillar 16 review branch

Starting sequence:

```powershell
git switch dev
git fetch origin dev
git merge --ff-only origin/dev
git switch -c review/backend-p16-release-candidate
```
