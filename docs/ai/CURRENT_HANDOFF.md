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
review/backend-p13-reporting-exports
```

Backend version:

```text
0.13.0
```

Latest completed and merged pillar:

- Pillar 12 — Audit Trail and Academic Accountability
- merged locally into `dev`
- only `dev` pushed

Current implementation scope:

- Pillar 13 — Reporting and Privacy-Safe Export APIs

Current verification status:

```text
Focused Pillar 13 verification: passed
Complete backend regression on review branch: 448 passed
```

The Pillar 13 review branch must remain local.

Do not push the review branch.

After focused tests and the complete backend regression pass, commit locally, merge into `dev`, rerun the complete regression on `dev`, and push only `dev`.

---

## Pillar 13 Objective

Pillar 13 provides ownership-safe academic reports and privacy-safe gradebook exports without exposing raw student source code, execution data, telemetry, unreleased student-visible grades, or automated misconduct rankings.

Implemented reporting areas:

- classroom completion summaries
- activity completion summaries
- manual-grade distributions
- missing-submission reports
- authenticated student personal progress summaries
- gradebook CSV exports

No database model or migration change is required for the current Pillar 13 implementation.

---

## Reporting Schemas

Implemented in:

```text
backend/app/schemas/reporting_schema.py
```

Implemented contracts:

- `ReportingStudentSummary`
- `ReportingClassroomSummary`
- `ReportingActivitySummary`
- `CompletionCounts`
- `ActivityCompletionSummaryResponse`
- `ClassroomActivityCompletionItem`
- `ClassroomCompletionSummaryResponse`
- `GradeDistributionBucket`
- `GradeDistributionResponse`
- `MissingSubmissionItem`
- `MissingSubmissionListResponse`
- `StudentClassProgressItem`
- `StudentProgressSummaryResponse`
- `GradebookCSVExportMetadata`

Schema behavior:

- Pydantic V2 strict validation
- extra fields forbidden
- ten-digit student school ID validation
- bounded pagination contracts
- deterministic approved sorting values
- completion-count consistency validation
- grade-distribution bucket-count validation
- safe CSV filename validation
- privacy flags cannot be client-enabled
- no raw-source or surveillance fields

---

## Reporting Service

Implemented in:

```text
backend/app/services/reporting_service.py
```

Implemented operations:

- `get_classroom_completion_summary`
- `get_activity_completion_summary`
- `get_grade_distribution`
- `list_missing_submissions`
- `get_student_progress_summary`
- `build_gradebook_csv_export`

Implemented service errors:

- `ReportingServiceError`
- `ReportingClassroomNotFoundError`
- `ReportingTaskNotFoundError`
- `ReportingAccessDeniedError`
- `ReportingFilterConflictError`
- `ReportingTaskUnavailableError`
- `ReportingPaginationError`
- `ReportingExportError`

### Classroom Completion Summary

A classroom completion summary includes only:

- an instructor-owned classroom
- active enrollments
- active student accounts
- verified student accounts
- published graded activities
- official submission attempts
- manually created instructor grades
- released manual-grade counts

The service calculates:

- active student count
- published graded activity count
- expected student-activity completion count
- submitted count
- missing count
- manually graded count
- released grade count
- completion percentage
- per-activity completion summaries

### Activity Completion Summary

An activity completion summary requires:

- an instructor-owned activity
- an activity assigned to an instructor-owned classroom
- a published activity
- a graded activity

Only official submission attempts contribute to completion.

Only manually created `InstructorGrade` records contribute to grade counts.

### Manual-Grade Distribution

Grade distributions are based only on manual instructor grades attached to official submissions.

Implemented bands:

- `0-59.99`
- `60-69.99`
- `70-79.99`
- `80-89.99`
- `90-100`

The report includes:

- manually graded submission count
- released grade count
- average percentage
- minimum percentage
- maximum percentage
- deterministic grade bands

The report does not create:

- automatic grades
- misconduct rankings
- plagiarism rankings
- cheating scores
- behavioral risk scores

### Missing-Submission Report

The missing-submission report includes only:

- instructor-owned classrooms and activities
- active enrollments
- active student accounts
- verified student accounts
- published graded activities
- student-activity pairs without an official submission

Pagination is bounded:

```text
minimum page size: 1
maximum page size: 100
```

Approved sorting:

- student name
- school ID
- activity title
- due date
- ascending
- descending

### Student Personal Progress

The student progress service uses only the authenticated student identity.

It reports:

- active classroom count
- published graded activity count
- submitted activity count
- missing activity count
- released grade count
- average released percentage
- completion percentage
- per-classroom progress summaries

Students do not receive:

- another student's progress
- unreleased grade values
- unreleased feedback
- instructor-only review data
- source-similarity details
- AST findings
- execution output
- coding-session telemetry

### Gradebook CSV Export

CSV export is restricted to instructor-owned classrooms and optional instructor-owned activity filters.

The export includes summary fields such as:

- student name
- school ID
- classroom
- subject code
- section
- activity title
- activity type
- official attempt number
- submission status
- manual-grade presence
- score
- maximum score
- percentage
- release state
- grade update timestamp

The export excludes:

- raw source code
- standard input
- starter code
- task descriptions and instructions
- grade feedback text
- hidden test data
- AST rules and findings
- similarity details
- execution output
- worker identifiers
- coding-session telemetry
- clipboard contents
- pasted text
- browsing history
- screen, webcam, and microphone data
- automated misconduct conclusions

CSV text cells beginning with the following characters are prefixed with an apostrophe:

```text
=
+
-
@
```

This prevents spreadsheet formula injection.

A UTF-8 byte-order mark is included for spreadsheet compatibility.

---

## Reporting Endpoints

Implemented router:

```text
backend/app/routers/reporting.py
```

Implemented endpoints:

```text
GET /reports/classrooms/{class_id}/completion
GET /reports/activities/{task_id}/completion
GET /reports/classrooms/{class_id}/grade-distribution
GET /reports/missing-submissions
GET /reports/students/me/progress
GET /reports/classrooms/{class_id}/gradebook.csv
```

Instructor-only endpoints:

- classroom completion
- activity completion
- grade distribution
- missing submissions
- gradebook CSV export

Student-only endpoint:

- authenticated personal progress

Clients cannot supply:

- instructor identity
- student identity for personal progress
- another report owner
- raw-source inclusion flags
- unreleased-student-data inclusion flags
- risk-score filters
- misconduct-ranking filters

Service errors map to controlled HTTP responses:

- `400 Bad Request`
- `403 Forbidden`
- `404 Not Found`
- `409 Conflict`
- `500 Internal Server Error`
- `503 Service Unavailable`

---

## Main Application and OpenAPI

Updated:

```text
backend/app/main.py
```

Changes:

- backend version updated to `0.13.0`
- `reporting` router imported
- reporting router registered
- `Reporting` OpenAPI tag added
- API description expanded for reporting and privacy-safe exports

Updated contract tests:

```text
backend/tests/test_openapi_contracts.py
backend/tests/test_classroom_openapi_contracts.py
```

OpenAPI requirements include:

- version `0.13.0`
- `Reporting` tag
- all six reporting routes
- authenticated route protection
- GET-only reporting operations
- bounded missing-submission pagination
- approved deterministic sorting
- owner-safe query parameters
- privacy-safe response schemas
- `text/csv` binary export contract
- no client-selected source-code export
- no client-selected unreleased-grade export
- no automated misconduct-ranking contract

---

## Pillar 13 Tests

Implemented:

```text
backend/tests/test_reporting_schemas.py
backend/tests/test_reporting_service.py
backend/tests/test_reporting_router.py
```

Schema tests cover:

- strict extra-field rejection
- ten-digit school ID
- completion invariants
- grade-distribution invariants
- missing-submission contracts
- student progress invariants
- safe CSV filenames
- forced privacy flags
- prohibited sensitive fields

Service tests cover:

- owner instructor allowed
- another instructor denied
- active and verified student filtering
- official and unofficial attempt handling
- published and graded activity requirements
- completion counts
- manual-grade distribution
- released and unreleased grade handling
- missing-submission filtering
- bounded pagination
- student personal progress
- CSV privacy
- CSV formula-injection protection
- constant query-count behavior

Router tests cover:

- authenticated instructor identity
- authenticated student identity
- query validation
- role dependency denial
- HTTP error mapping
- CSV headers
- GET-only OpenAPI operations
- privacy-safe reporting schemas

Latest confirmed focused reporting suite:

```text
59 passed
```

Latest confirmed complete backend regression:

```text
448 passed
```

---

## Permanent Authorization and Privacy Boundaries

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
- Reports never create automated rankings based on behavioral or review indicators.
- Paste policy remains `internal_only` or `disabled`.
- Blocked-paste telemetry stores count and timestamp only.
- Clipboard contents and pasted text are never stored.
- Browsing history is never collected.
- Screen, webcam, and microphone recording are prohibited.
- Individual keystroke collection is prohibited.
- Student Python code never executes inside React or FastAPI.
- Student code executes only through the partner-owned isolated sandbox worker.
- Reporting and exports must remain ownership-safe.
- Raw source code is excluded from gradebook CSV exports by default and by current contract.

---

## Pillar 13 Files

Implementation:

```text
backend/app/schemas/reporting_schema.py
backend/app/services/reporting_service.py
backend/app/routers/reporting.py
backend/app/main.py
```

Tests:

```text
backend/tests/test_reporting_schemas.py
backend/tests/test_reporting_service.py
backend/tests/test_reporting_router.py
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
review/backend-p13-reporting-exports
```

From `backend`, run focused Pillar 13 tests:

```powershell
.\venv\Scripts\python.exe -m pytest `
    tests\test_reporting_schemas.py `
    tests\test_reporting_service.py `
    tests\test_reporting_router.py `
    tests\test_openapi_contracts.py `
    tests\test_classroom_openapi_contracts.py `
    -q
```

Run the complete backend regression:

```powershell
.\venv\Scripts\python.exe -m pytest -q
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

Pillar 13 review-branch verification is complete:

- focused Pillar 13 tests passed
- complete backend regression passed
- exact full regression count recorded: `448 passed`

Remaining completion steps:

- commit the review branch locally
- merge the review branch locally into `dev`
- rerun the complete regression on `dev`
- push only `dev`
- confirm the working tree is clean

---

## Final Pillar 13 Git Procedure

Stage exact files only.

Do not use:

```powershell
git add .
```

Stage:

```powershell
git add `
    backend/app/schemas/reporting_schema.py `
    backend/app/services/reporting_service.py `
    backend/app/routers/reporting.py `
    backend/app/main.py `
    backend/tests/test_reporting_schemas.py `
    backend/tests/test_reporting_service.py `
    backend/tests/test_reporting_router.py `
    backend/tests/test_openapi_contracts.py `
    backend/tests/test_classroom_openapi_contracts.py `
    docs/ai/CURRENT_HANDOFF.md
```

Commit locally after the focused and complete regressions pass:

```powershell
git commit -m "feat: add privacy-safe reporting and gradebook exports"
```

Do not push the review branch.

Merge locally into `dev`:

```powershell
git switch dev
git pull --ff-only origin dev
git merge --no-ff review/backend-p13-reporting-exports
```

Run the complete backend regression again on `dev`:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
cd ..
```

Push only `dev` after the regression passes:

```powershell
git push origin dev
```

Confirm the working tree is clean:

```powershell
git status --short
```

---

## Next Pillar

After Pillar 13 is verified, merged, and pushed:

### Pillar 14 — Partner Integration Contracts

Version:

```text
0.14.0
```

Local branch:

```text
review/backend-p14-partner-contracts
```

Authoritative scope from `docs/ai/ROADMAP.md`:

- isolated-worker request/result contracts
- authenticated result updates
- allowed execution lifecycle transitions
- replay and idempotency protection
- correlation IDs
- result-size validation
- OTP email-adapter interface
- local LLM interface boundary
- health and readiness contracts

Excluded implementation:

- Celery
- Redis
- Docker
- sandbox runtime
- resource-limit enforcement runtime
- email-provider implementation
- LLM runtime implementation

The local LLM may draft explanations, hints, or feedback, but it must never set grades or determine plagiarism or misconduct.
