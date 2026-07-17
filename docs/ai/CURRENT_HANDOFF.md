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
review/backend-p12-audit-trail
```

Backend version:

```text
0.12.0
```

Latest completed implementation scope:

- Pillar 12 — Audit Trail and Academic Accountability

Current verification status:

```text
Latest observed full regression: 380 passed, 1 failed
```

The remaining observed failure was a stale version assertion in:

```text
backend/tests/test_classroom_openapi_contracts.py
```

Required assertion:

```python
assert APP_VERSION == "0.12.0"
```

A final green full-regression rerun was not yet supplied when this handoff was updated.

The Pillar 12 review branch must remain local.

Do not push the review branch.

After the final full regression passes, merge it locally into `dev`, rerun the full regression on `dev`, and push only `dev`.

---

## Completed Pillar 12 Scope

Pillar 12 provides backend-owned, immutable, privacy-safe audit records for accountable academic actions.

Implemented database model:

- `AuditRecord`
- UUID audit identifier
- unique backend-generated audit key
- authenticated actor identity
- action type
- resource type
- resource identifier
- outcome
- privacy-safe structured metadata
- occurrence timestamp
- creation timestamp
- actor, action, and resource indexes

Implemented audit action types:

- `user_registered`
- `login_succeeded`
- `login_failed`
- `classroom_created`
- `classroom_updated`
- `classroom_archived`
- `classroom_reactivated`
- `student_enrolled`
- `enrollment_status_changed`
- `activity_created`
- `activity_updated`
- `activity_published`
- `activity_unpublished`
- `submission_created`
- `submission_status_changed`
- `grade_created`
- `grade_updated`
- `grade_released`
- `notification_marked_read`
- `notifications_marked_read`

The current Pillar 12 domain integrations cover classroom, enrollment, activity, submission, and manual-grade accountability workflows.

Authentication and notification read-state action types remain reserved for trusted future integration unless explicitly implemented and tested.

Implemented resource types:

- `user`
- `classroom`
- `enrollment`
- `task`
- `submission`
- `grade`
- `notification`

Implemented outcomes:

- `succeeded`
- `denied`
- `failed`

---

## Audit Schemas and Validation

Implemented audit schemas:

- `AuditActionType`
- `AuditResourceType`
- `AuditOutcome`
- `AuditRecordCreateInternal`
- `AuditRecordResponse`
- `AuditRecordListResponse`

Schema behavior:

- strict Pydantic validation
- extra fields are forbidden
- audit creation is internal-only
- public responses exclude the internal audit key
- recursive metadata privacy validation
- metadata size limit
- actor identity is backend-controlled
- occurrence timestamp is backend-controlled
- resource identity is backend-controlled by trusted workflows

Prohibited audit metadata includes:

- passwords
- password hashes
- OTP values
- source code
- starter code
- standard input
- hidden test data
- expected output
- AST rules or findings
- similarity details
- execution output
- worker identifiers
- coding-session telemetry details
- clipboard contents
- pasted text
- browsing history
- individual keystrokes
- screen recordings
- webcam data
- microphone data
- score values
- maximum-score values
- feedback text
- automated plagiarism verdicts
- automated cheating verdicts
- automated misconduct conclusions

---

## Audit Service

Implemented service operations:

- idempotent audit creation by unique `audit_key`
- internal atomic mode using `commit=False`
- metadata-size enforcement
- audit-key conflict handling
- actor-owned audit retrieval
- actor-owned audit listing
- action-type filtering
- resource-type filtering
- outcome filtering
- deterministic pagination
- owner-scoped authorization

Audit records are append-only through the application API.

There are no client-facing create, update, patch, or delete operations.

---

## Audit Endpoints

Implemented endpoints:

- `GET /audit-records/`
- `GET /audit-records/{audit_id}`

Behavior:

- authentication is required
- users may read only audit records attributed to their own account
- clients cannot select another actor
- clients cannot create audit records
- clients cannot update audit records
- clients cannot delete audit records
- internal audit keys are not exposed
- audit metadata is privacy-filtered before persistence

---

## Domain Integrations

### Classroom Creation

Creating an instructor-owned classroom creates a `classroom_created` audit record.

Behavior:

- instructor identity comes from the authenticated account
- class codes are generated only by the backend
- class-code values are never stored in audit metadata
- classroom creation and the audit record are committed together
- audit failure rolls back classroom creation
- audit failure is exposed as controlled HTTP `503 Service Unavailable`

### Classroom Update

Meaningful classroom field changes create a `classroom_updated` audit record.

Behavior:

- only changed field names are recorded
- no-op updates do not create duplicate audit rows
- classroom changes and their audit records are committed together
- audit failure rolls back the classroom update

### Classroom Archive and Reactivation

An active-to-inactive transition creates `classroom_archived`.

An inactive-to-active transition creates `classroom_reactivated`.

Behavior:

- `archived_at` is backend-controlled
- repeated inactive updates preserve the original archive timestamp
- repeated no-op archive requests do not create duplicate audit rows
- reactivation clears `archived_at`
- archive audit, academic event, and eligible student notifications participate in the accountable workflow
- notification failure rolls back the archive transition
- audit failure rolls back the archive transition
- failures are exposed as controlled HTTP `503 Service Unavailable`

### Class-Code Regeneration

Regenerating a class code creates a `classroom_updated` audit record.

Behavior:

- the generated code is never stored in audit metadata
- metadata records only that the backend regenerated the code
- code regeneration and its audit record are committed together

### Student Enrollment

Joining a classroom creates a `student_enrolled` audit record.

Behavior:

- student identity comes from the authenticated account
- class ownership is resolved by the backend
- enrollment and its audit record are committed together
- audit failure rolls back enrollment creation
- failure is exposed as controlled HTTP `503 Service Unavailable`

### Enrollment Status Change

A meaningful enrollment-state transition creates `enrollment_status_changed`.

Behavior:

- only the owning instructor may change enrollment status
- previous and new status values are recorded
- repeated no-op status requests do not create duplicate audit rows
- enrollment changes and audit records are committed together
- audit failure rolls back the status transition

### Activity Creation

Creating an instructor activity creates `activity_created`.

Behavior:

- instructor identity is backend-controlled
- publication state begins as draft
- activity creation and its audit record are committed together
- titles, descriptions, instructions, starter code, AST rules, and test data are excluded from audit metadata

### Activity Update

Meaningful activity changes create `activity_updated`.

Behavior:

- only changed field names are recorded
- no-op updates do not create duplicate audit rows
- activity changes and audit records are committed together
- source-bearing or evaluator-sensitive fields are not copied into metadata

### Activity Publication and Unpublication

Publishing creates `activity_published`.

Returning an activity to draft creates `activity_unpublished`.

Behavior:

- publication requires an active instructor-owned classroom
- publication requires a future deadline when a deadline is configured
- publication timestamp is backend-controlled
- publication or unpublication and the audit record are committed together
- repeated no-op publication does not duplicate audit rows
- repeated publication may safely retry a previously incomplete notification workflow
- audit failure rolls back the publication-state transition
- notification failure remains exposed as controlled HTTP `503 Service Unavailable`

### Submission Creation

Creating an immutable official attempt creates `submission_created`.

Behavior:

- student identity is backend-controlled
- attempt number is backend-controlled
- latest accepted attempt becomes official
- source code and standard input remain immutable
- audit metadata contains only approved identifiers, attempt number, workflow status, and official-attempt state
- source code and standard input are never stored in the audit record
- submission, audit record, academic event, and instructor notification are saved atomically
- audit failure rolls back the new attempt and restores the previous official attempt
- notification failure rolls back the entire submission workflow
- retrying after failure does not consume an attempt number
- failures are exposed as controlled HTTP `503 Service Unavailable`

### Manual Grade Creation

Creating a manual instructor grade creates `grade_created`.

Behavior:

- only the owning instructor may create the grade
- only the latest accepted official submission of a graded activity may receive a grade
- grade creation and its audit record are committed together
- audit metadata contains field names and release state, not grade values
- score, maximum score, and feedback are never copied into audit metadata

### Manual Grade Update

A meaningful grade edit creates `grade_updated`.

Behavior:

- no-op grade updates do not create duplicate audit rows
- changed field names are recorded
- score values, maximum-score values, and feedback text are excluded
- grade changes and audit records are committed together
- audit failure rolls back the grade change

### Grade Release

An unreleased-to-released transition creates `grade_released`.

Behavior:

- a separate release audit record is created in addition to the grade write audit
- repeated writes to an already released grade do not duplicate release audits
- grade release, audit records, academic event, and student notification are saved atomically
- audit or notification failure rolls back the release transition
- failures are exposed as controlled HTTP `503 Service Unavailable`

---

## OpenAPI and API Contracts

The OpenAPI contract includes:

- backend version `0.12.0`
- the `Audit Trail` tag
- both owner-scoped audit endpoints
- authenticated access requirements
- read-only audit route enforcement
- no audit-creation request body
- no actor-selection input
- privacy-safe audit responses
- documented HTTP `503` responses for accountable workflow failures

Documented accountable failure responses include:

- classroom creation
- classroom update
- classroom archive
- classroom reactivation
- class-code regeneration
- student enrollment
- enrollment status transition
- activity creation
- activity update
- activity publication
- activity unpublication
- submission creation
- manual grade creation
- manual grade update
- grade release

---

## Audit Privacy and Non-Surveillance Rules

- Clients cannot create audit records.
- Clients cannot choose audit actors.
- Clients cannot choose audit keys.
- Clients cannot alter audit timestamps.
- Clients cannot update audit records.
- Clients cannot delete audit records.
- Users may read only records attributed to their own account.
- Audit records never contain passwords.
- Audit records never contain password hashes.
- Audit records never contain OTP values.
- Audit records never contain source code.
- Audit records never contain starter code.
- Audit records never contain standard input.
- Audit records never contain hidden test data.
- Audit records never contain expected outputs.
- Audit records never contain AST rules.
- Audit records never contain AST findings.
- Audit records never contain similarity details.
- Audit records never contain execution output.
- Audit records never contain worker identifiers.
- Audit records never contain score values.
- Audit records never contain maximum-score values.
- Audit records never contain feedback text.
- Audit records never contain clipboard contents.
- Audit records never contain pasted text.
- Browsing history is never collected.
- Individual keystrokes are never collected.
- Screen recordings are never collected.
- Webcam data is never collected.
- Microphone data is never collected.
- Audit records never contain automated misconduct conclusions.
- Audit records support accountability and authorized review only.
- The audit trail must not become a surveillance system.

---

## Existing System Boundaries That Remain Mandatory

- Registration accepts only `@pampangastateu.edu.ph`.
- School ID is exactly 10 digits.
- School ID is stored as a string.
- School ID is unique.
- Roles are controlled only by the backend allowlist.
- OTP verification remains required.
- Submission attempts are immutable.
- The latest accepted attempt becomes official.
- Official grades are manually controlled by instructors.
- AST, Jaccard similarity, execution, and coding-session indicators remain review-only.
- Automated indicators never assign grades.
- Automated indicators never determine plagiarism, cheating, copying, or misconduct.
- Paste policy remains `internal_only` or `disabled`.
- Blocked-paste telemetry stores count and timestamp only.
- Clipboard contents and pasted text are never stored.
- Browsing history is never collected.
- Screen, webcam, and microphone recording are prohibited.
- Individual keystroke collection is prohibited.
- Student Python code never executes inside React or FastAPI.
- Student code executes only through the partner-owned isolated sandbox worker.

---

## Pillar 12 Files

Primary implementation files:

```text
backend/app/models/domain_models.py
backend/app/schemas/audit_schema.py
backend/app/services/audit_service.py
backend/app/routers/audit_records.py
backend/app/services/classroom_service.py
backend/app/routers/classrooms.py
backend/app/services/task_service.py
backend/app/routers/instructor.py
backend/app/services/submission_service.py
backend/app/routers/submissions.py
backend/app/services/evaluation_service.py
backend/app/routers/evaluation.py
backend/app/main.py
```

Primary test files:

```text
backend/tests/test_audit_models.py
backend/tests/test_audit_schemas.py
backend/tests/test_audit_service.py
backend/tests/test_audit_router.py
backend/tests/test_audit_workflow.py
backend/tests/test_openapi_contracts.py
backend/tests/test_classroom_openapi_contracts.py
```

Documentation:

```text
docs/ai/CURRENT_HANDOFF.md
```

---

## Verification Commands

From the repository root:

```powershell
git branch --show-current
```

Expected:

```text
review/backend-p12-audit-trail
```

Run focused Pillar 12 verification:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest `
    tests\test_audit_models.py `
    tests\test_audit_schemas.py `
    tests\test_audit_service.py `
    tests\test_audit_router.py `
    tests\test_audit_workflow.py `
    tests\test_openapi_contracts.py `
    tests\test_classroom_openapi_contracts.py `
    -q
```

Run the complete backend regression:

```powershell
.\venv\Scripts\python.exe -m pytest -q
cd ..
```

Run repository checks:

```powershell
git diff --check
git status --short
```

Do not claim final Pillar 12 verification until the complete backend regression is green.

---

## Final Pillar 12 Git Procedure

Stage exact files only.

Do not use:

```powershell
git add .
```

Suggested exact staging command:

```powershell
git add `
    backend/app/models/domain_models.py `
    backend/app/schemas/audit_schema.py `
    backend/app/services/audit_service.py `
    backend/app/routers/audit_records.py `
    backend/app/services/classroom_service.py `
    backend/app/routers/classrooms.py `
    backend/app/services/task_service.py `
    backend/app/routers/instructor.py `
    backend/app/services/submission_service.py `
    backend/app/routers/submissions.py `
    backend/app/services/evaluation_service.py `
    backend/app/routers/evaluation.py `
    backend/app/main.py `
    backend/tests/test_audit_models.py `
    backend/tests/test_audit_schemas.py `
    backend/tests/test_audit_service.py `
    backend/tests/test_audit_router.py `
    backend/tests/test_audit_workflow.py `
    backend/tests/test_openapi_contracts.py `
    backend/tests/test_classroom_openapi_contracts.py `
    docs/ai/CURRENT_HANDOFF.md
```

Commit locally after all tests pass:

```powershell
git commit -m "feat: complete audit trail and academic accountability"
```

Do not push the review branch.

Merge locally into `dev`:

```powershell
git switch dev
git merge --no-ff review/backend-p12-audit-trail
```

Run the complete backend regression again on `dev`:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
cd ..
```

Push only `dev`:

```powershell
git push origin dev
```

---

## Next Work

After Pillar 12 is fully verified and merged:

1. Read `docs/ai/ROADMAP.md`.
2. Confirm the next incomplete pillar and target backend version.
3. Create the next local review branch from updated `dev`.
4. Do not push the review branch.
5. Continue one module at a time.
6. Preserve all security, privacy, grading, execution, and non-surveillance boundaries documented above.
