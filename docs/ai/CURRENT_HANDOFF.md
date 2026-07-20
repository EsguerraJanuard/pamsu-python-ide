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
review/backend-p14-partner-contracts
```

Backend version:

```text
0.14.0
```

Latest completed and merged pillar:

- Pillar 13 — Reporting and Privacy-Safe Export APIs
- merged locally into `dev`
- only `dev` pushed

Current completed implementation scope:

- Pillar 14 — Partner Integration Contracts

Current verification status:

```text
Focused Pillar 14 verification: passed
Complete backend regression on review branch: 567 passed
PostgreSQL schema verification: passed
Real readiness verification: HTTP 200 ready
```

The Pillar 14 review branch must remain local.

Do not push the review branch.

Local checkpoint commits were created during implementation. The remaining completion sequence is:

1. replace and commit this handoff
2. confirm repository checks
3. merge the review branch locally into `dev`
4. rerun the complete backend regression on `dev`
5. push only `dev`
6. confirm the working tree is clean

---

## Pillar 14 Objective

Pillar 14 defines secure, explicit contracts between the FastAPI backend and trusted partner-owned integrations without implementing the isolated execution runtime, concrete email delivery provider, or local LLM runtime.

Implemented areas:

- isolated-worker dispatch and result contracts
- authenticated partner result updates
- backend-controlled execution lifecycle transitions
- replay and idempotency protection
- correlation identifiers
- strict partner update sequencing
- bounded execution-result validation
- partner update persistence records
- OTP email-adapter interface
- local LLM assistance interface boundary
- liveness and readiness contracts
- explicit PostgreSQL-compatible schema upgrade support

Excluded implementation remains:

- Celery
- Redis
- Docker
- isolated sandbox runtime
- resource-limit enforcement runtime
- SMTP or third-party email-provider implementation
- local LLM model runtime
- model download or inference server
- background delivery or inference queues

Student Python code still never executes inside React or FastAPI.

---

## Partner Execution Schemas

Implemented in:

```text
backend/app/schemas/execution_schema.py
```

Implemented or extended contracts include:

- partner-reportable execution statuses
- allowed lifecycle transition map
- bounded worker identity and output values
- backend-generated correlation identifiers
- backend-generated dispatch idempotency identifiers
- `PartnerExecutionLimits`
- `PartnerExecutionDispatchRequest`
- `PartnerExecutionResultUpdate`
- `PartnerExecutionUpdateAcceptedResponse`
- lifecycle-transition validation helpers
- combined UTF-8 execution-output size validation

Contract behavior:

- strict Pydantic V2 validation
- extra fields forbidden
- UUID normalization
- timezone-aware partner timestamps
- bounded source, input, output, and worker identifiers
- terminal updates require completion metadata
- running updates cannot claim terminal completion
- terminal execution requests cannot be mutated by later updates
- result payloads cannot carry credentials, grades, analytics, telemetry, or misconduct verdicts

Execution limits are contract values only in Pillar 14.

FastAPI does not enforce CPU, memory, filesystem, process, or network isolation.

Those controls remain the responsibility of the future partner-owned isolated worker.

---

## Partner Execution Models

Updated in:

```text
backend/app/models/domain_models.py
```

`ExecutionRequest` now includes:

- `correlation_id`
- `dispatch_idempotency_key`
- `last_partner_sequence`
- partner lifecycle index
- unique correlation identifier
- unique dispatch idempotency identifier
- relationship to accepted partner update records

Implemented partner update model:

```text
PartnerExecutionUpdateRecord
```

Database table:

```text
partner_execution_updates
```

Stored partner update metadata:

- partner update record identifier
- globally unique update identifier
- execution identifier
- correlation identifier
- strict sequence number
- accepted status
- canonical payload digest
- acceptance timestamp

The update-record table does not store:

- source code
- standard input
- stdout or stderr
- credentials
- OTP values
- grades
- AST findings
- similarity details
- session telemetry
- clipboard contents
- pasted text
- surveillance data
- misconduct conclusions

---

## Partner Authentication Boundary

Implemented in:

```text
backend/app/integrations/partner_auth.py
```

Authentication configuration:

```text
Environment variable: PAMSU_PARTNER_EXECUTION_TOKEN
HTTP header: X-Partner-Token
Minimum configured token length: 32 characters
```

Behavior:

- missing configured token returns `503 Service Unavailable`
- configured token shorter than the minimum returns `503 Service Unavailable`
- missing partner header returns `401 Unauthorized`
- invalid partner token returns `401 Unauthorized`
- comparison uses constant-time secret comparison
- token values are never returned in responses
- token values are never included in OpenAPI
- query parameters and request bodies cannot replace the required header

The real development token belongs only in:

```text
backend/.env
```

The token must never be committed.

Production transport must use TLS.

---

## Partner Execution Service

Updated in:

```text
backend/app/services/execution_service.py
```

Implemented partner operations include:

- build a partner dispatch contract from a stored execution request
- apply an authenticated partner lifecycle or result update
- validate execution correlation identity
- validate strict partner sequence ordering
- validate worker-task identity
- enforce allowed lifecycle transitions
- reject updates after terminal completion
- compute a canonical SHA-256 payload digest
- recognize identical retries as safe replays
- reject reuse of an update identifier with different content
- persist execution state and accepted update metadata atomically
- roll back controlled persistence failures

Replay behavior:

- first accepted update returns `replayed: false`
- identical retry returns `replayed: true`
- conflicting retry returns `409 Conflict`
- stale or skipped sequence numbers return `409 Conflict`

The legacy internal worker-update service remains available for backward compatibility, but the authenticated Pillar 14 route is the trusted partner boundary.

---

## Authenticated Partner Result Endpoint

Updated router:

```text
backend/app/routers/execution.py
```

Implemented endpoint:

```text
POST /execution/internal/partner-results
```

This endpoint:

- requires `X-Partner-Token`
- accepts `PartnerExecutionResultUpdate`
- returns `PartnerExecutionUpdateAcceptedResponse`
- never executes Python code
- never accepts partner credentials in the body
- never exposes the internal partner token

Controlled HTTP mappings include:

- `200 OK` — accepted update or identical replay
- `400 Bad Request` — invalid worker lifecycle data
- `401 Unauthorized` — missing or invalid partner token
- `404 Not Found` — execution request does not exist
- `409 Conflict` — correlation, replay, sequence, worker, lifecycle, or persistence conflict
- `422 Unprocessable Content` — request-schema validation failure
- `500 Internal Server Error` — persistence failure
- `503 Service Unavailable` — partner authentication boundary not configured

Student and instructor execution routes remain protected by their existing authenticated ownership rules.

---

## OTP Email-Adapter Boundary

Implemented integration contract:

```text
backend/app/integrations/otp_email.py
```

Updated service:

```text
backend/app/services/otp_service.py
```

Implemented interface:

```text
OTPEmailAdapter.send_otp()
```

The adapter receives only:

- recipient university email
- temporary plaintext OTP
- approved delivery purpose
- expiration duration

The backend remains responsible for:

- OTP generation
- OTP hashing
- expiration
- resend cooldowns
- resend limits
- verification attempts
- challenge consumption
- account creation
- role assignment

Adapter failures are converted into:

```text
OTPDeliveryError
```

Registration and resend transactions roll back when delivery fails.

Plaintext OTP values:

- exist only temporarily in process memory
- are never stored
- are never logged
- are never returned through the API
- are never included in OpenAPI
- are never written to audit records

Pillar 14 does not implement SMTP or a third-party email provider.

---

## Local LLM Interface Boundary

Implemented in:

```text
backend/app/integrations/local_llm.py
```

Implemented assistance kinds:

- `explanation`
- `hint`
- `feedback`

Implemented contracts:

- `LocalLLMAssistanceRequest`
- `LocalLLMAssistanceResponse`
- `LocalLLMAdapter`
- adapter validation
- request and response correlation validation
- assistance-kind matching
- bounded context and response sizes
- timezone-aware response timestamps

Allowed context is limited to explicitly approved student-visible data.

The contract excludes:

- passwords
- OTP values
- JWTs
- API keys
- hidden tests
- expected outputs
- unreleased grades
- official grades
- similarity details
- surveillance telemetry
- clipboard contents
- pasted text
- browsing history
- individual keystrokes
- screen recordings
- webcam data
- microphone data

Local LLM output may draft educational explanations, hints, or feedback only.

It must never:

- assign a score
- assign an official grade
- release a grade
- determine pass or fail
- determine plagiarism
- determine cheating
- determine copying
- determine misconduct
- rank behavioral or academic risk

Pillar 14 does not implement a model runtime, inference server, provider client, prompt engine, or persistence layer.

---

## Health and Readiness Contracts

Updated:

```text
backend/app/main.py
```

Backend version:

```text
0.14.0
```

Implemented system endpoints:

```text
GET /
GET /health
GET /ready
```

### Liveness

```text
GET /health
```

Behavior:

- checks process-level application liveness only
- does not query the database
- does not contact the execution partner
- does not contact an email provider
- does not contact a local LLM runtime
- returns sanitized service, version, state, and timestamp values

### Readiness

```text
GET /ready
```

`/ready` is a public deployment probe and does not require a user JWT.

Required readiness components:

- database connection
- execution-partner authentication configuration

Optional Pillar 14 contract-only components:

- OTP email adapter
- local LLM adapter

Readiness behavior:

- returns `200 OK` with `status: ready` when required components are ready
- returns `503 Service Unavailable` with `status: not_ready` when a required component is unavailable
- reports OTP email and local LLM as `contract_only`
- does not expose tokens
- does not expose secret names
- does not expose secret lengths
- does not expose connection strings
- does not expose provider names
- does not expose raw exceptions

---

## Explicit Database Upgrade

Implemented in:

```text
backend/app/db/upgrade_p14_partner_execution.py
```

The module exists because:

```text
Base.metadata.create_all()
```

creates missing tables but does not alter existing tables.

The explicit upgrade:

- supports PostgreSQL
- supports SQLite development databases
- requires the base `execution_requests` table
- adds missing Pillar 14 execution columns
- backfills missing partner UUIDs
- initializes missing partner sequence values
- applies unique indexes
- applies the partner lifecycle index
- applies PostgreSQL not-null and sequence constraints
- creates `partner_execution_updates`
- verifies the resulting schema
- is safe to rerun
- never runs automatically during FastAPI import or startup

Run explicitly from `backend`:

```powershell
.\venv\Scripts\python.exe -m app.db.upgrade_p14_partner_execution
```

Observed PostgreSQL verification:

```text
Pillar 14 partner-execution schema upgrade completed.
Database dialect: postgresql
Execution rows backfilled: 0
Partner-update table created: False
```

`Partner-update table created: False` was correct because the fresh database schema had already created the table.

---

## PostgreSQL Verification

Configured development database dialect:

```text
postgresql
```

Sanitized configured URL:

```text
postgresql://postgres:***@localhost:5432/pamsu_ide_db
```

The database was initially empty.

The complete current metadata schema was initialized explicitly for the fresh development database.

Observed table state:

```text
Table count: 20
execution_requests exists: True
partner_execution_updates exists: True
```

Verified `execution_requests` Pillar 14 columns:

```text
correlation_id
dispatch_idempotency_key
last_partner_sequence
```

Observed real readiness verification:

```text
HTTP status: 200
Application status: ready
database: ready
execution_partner_auth: ready
otp_email_adapter: contract_only
local_llm_adapter: contract_only
```

No database password or partner token is recorded in this handoff.

---

## Main Application and OpenAPI

Updated:

```text
backend/app/main.py
backend/tests/test_openapi_contracts.py
backend/tests/test_classroom_openapi_contracts.py
```

OpenAPI requirements now include:

- version `0.14.0`
- public `/health`
- public `/ready`
- authenticated `POST /execution/internal/partner-results`
- `PartnerExecutionToken` API-key security scheme
- `X-Partner-Token` header authentication
- documented partner result responses
- no partner secret in OpenAPI
- no partner credential fields in result bodies
- health and readiness response contracts
- preserved classroom and all previous API contracts

---

## Pillar 14 Tests

Implemented or updated:

```text
backend/tests/test_schemas.py
backend/tests/test_partner_execution_models.py
backend/tests/test_execution_service.py
backend/tests/test_partner_auth.py
backend/tests/test_partner_execution_router.py
backend/tests/test_otp_service.py
backend/tests/test_local_llm.py
backend/tests/test_system_health.py
backend/tests/test_p14_schema_upgrade.py
backend/tests/test_openapi_contracts.py
backend/tests/test_classroom_openapi_contracts.py
```

Test coverage includes:

- partner dispatch and result schemas
- UUID and timestamp validation
- bounded execution limits and output
- lifecycle transitions
- terminal-state protection
- partner model constraints
- unique update identifiers
- unique per-execution sequence numbers
- update-record privacy
- authenticated partner result updates
- correlation conflicts
- worker identity conflicts
- stale and skipped sequences
- safe identical replay
- conflicting replay rejection
- persistence rollback
- partner API-key OpenAPI contract
- partner secret exclusion
- OTP adapter compatibility
- OTP delivery failures
- registration rollback
- resend rollback
- plaintext OTP privacy
- local LLM adapter compatibility
- LLM request and response correlation
- assistance-kind validation
- timezone validation
- grade and misconduct field exclusion
- health liveness
- readiness success and failure states
- database readiness rollback
- contract-only optional components
- schema upgrade backfill
- schema upgrade rerun idempotency
- source-code preservation during schema upgrade
- complete OpenAPI route and authentication boundaries

Latest confirmed selected Pillar 14 verification:

```text
passed
```

Latest confirmed complete backend regression on the review branch:

```text
567 passed in 116.87s (0:01:56)
```

This is the authoritative current regression count.

Do not replace it with an estimate.

---

## Permanent Authorization, Academic, and Privacy Boundaries

- Registration accepts only `@pampangastateu.edu.ph`.
- School ID is exactly 10 digits.
- School ID is stored as a string.
- School ID is unique.
- Roles are controlled only by the backend allowlist.
- OTP verification remains required.
- Plaintext OTP values are never persisted or returned.
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
- Partner result retries must remain replay-safe and idempotent.
- Reporting and exports remain ownership-safe.
- Raw source code remains excluded from gradebook CSV exports.
- Health and readiness responses never expose credentials or connection details.

---

## Pillar 14 Files

Implementation:

```text
backend/app/schemas/execution_schema.py
backend/app/models/domain_models.py
backend/app/services/execution_service.py
backend/app/integrations/partner_auth.py
backend/app/routers/execution.py
backend/app/integrations/otp_email.py
backend/app/services/otp_service.py
backend/app/integrations/local_llm.py
backend/app/main.py
backend/app/db/upgrade_p14_partner_execution.py
```

Tests:

```text
backend/tests/test_schemas.py
backend/tests/test_partner_execution_models.py
backend/tests/test_execution_service.py
backend/tests/test_partner_auth.py
backend/tests/test_partner_execution_router.py
backend/tests/test_otp_service.py
backend/tests/test_local_llm.py
backend/tests/test_system_health.py
backend/tests/test_p14_schema_upgrade.py
backend/tests/test_openapi_contracts.py
backend/tests/test_classroom_openapi_contracts.py
```

Documentation:

```text
docs/ai/CURRENT_HANDOFF.md
```

Local environment configuration:

```text
backend/.env
```

The `.env` file is not a Pillar 14 repository file and must not be committed.

---

## Verification Commands

From the repository root:

```powershell
git branch --show-current
```

Expected:

```text
review/backend-p14-partner-contracts
```

From `backend`, run the complete regression:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Latest verified review-branch result:

```text
567 passed in 116.87s (0:01:56)
```

Verify the sanitized database target:

```powershell
.\venv\Scripts\python.exe -c "from app.core.database import engine; print(engine.url.render_as_string(hide_password=True)); print(engine.dialect.name)"
```

Run the explicit database upgrade when required:

```powershell
.\venv\Scripts\python.exe -m app.db.upgrade_p14_partner_execution
```

Verify real readiness:

```powershell
.\venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from app.main import app; r=TestClient(app).get('/ready'); print('Status:', r.status_code); print(r.json())"
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

Do not claim final Pillar 14 merge completion until:

- this handoff is committed
- the review branch is committed locally
- the review branch is merged locally into `dev`
- the complete regression passes again on `dev`
- only `dev` is pushed
- the working tree is clean

---

## Final Pillar 14 Git Procedure

Stage exact files only.

Do not use:

```powershell
git add .
```

From the repository root, stage the complete Pillar 14 file set:

```powershell
git add `
    backend/app/schemas/execution_schema.py `
    backend/app/models/domain_models.py `
    backend/app/services/execution_service.py `
    backend/app/integrations/partner_auth.py `
    backend/app/routers/execution.py `
    backend/app/integrations/otp_email.py `
    backend/app/services/otp_service.py `
    backend/app/integrations/local_llm.py `
    backend/app/main.py `
    backend/app/db/upgrade_p14_partner_execution.py `
    backend/tests/test_schemas.py `
    backend/tests/test_partner_execution_models.py `
    backend/tests/test_execution_service.py `
    backend/tests/test_partner_auth.py `
    backend/tests/test_partner_execution_router.py `
    backend/tests/test_otp_service.py `
    backend/tests/test_local_llm.py `
    backend/tests/test_system_health.py `
    backend/tests/test_p14_schema_upgrade.py `
    backend/tests/test_openapi_contracts.py `
    backend/tests/test_classroom_openapi_contracts.py `
    docs/ai/CURRENT_HANDOFF.md
```

Review the staged set:

```powershell
git diff --cached --name-only
git diff --cached --check
```

Confirm the local environment file is not staged:

```powershell
git status --short | Select-String "\.env|\.db|__pycache__|\.pyc"
```

Create the final local Pillar 14 commit:

```powershell
git commit -m "feat: complete partner integration contracts"
```

Do not push the review branch.

Merge locally into the updated `dev` branch:

```powershell
git switch dev
git fetch origin dev
git merge --ff-only origin/dev
git merge --no-ff review/backend-p14-partner-contracts
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

Confirm the working tree:

```powershell
git status --short
git log -3 --oneline
```

The review branch remains local and must not be pushed.

---

## Next Pillar

Before starting the next pillar:

1. confirm Pillar 14 is merged and pushed through `dev`
2. read `docs/ai/ROADMAP.md`
3. copy the exact next pillar title, version, branch name, scope, and exclusions into this handoff
4. create the next local review branch from the updated `dev`
5. do not infer the next scope from Pillar 14 exclusions
6. do not push the next review branch

The currently supplied handoff identifies Pillar 14 as the latest roadmap entry but does not contain the authoritative Pillar 15 title or scope.

Do not invent the next pillar.

Use this starting sequence after reading the roadmap:

```powershell
git switch dev
git fetch origin dev
git merge --ff-only origin/dev
git switch -c <exact-next-review-branch-from-roadmap>
```
