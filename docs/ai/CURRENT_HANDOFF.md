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
review/backend-p11-notification-workflow
```

Backend version:

```text
0.11.0
```

Latest completed pillar:

- Pillar 11 — In-App Notification and Academic Event Workflow

Latest verified backend regression:

```text
255 passed
```

The Pillar 11 review branch must remain local.

Do not push the review branch.

Merge it locally into `dev`, run the full regression again on `dev`, and push only `dev`.

---

## Completed Pillar 11 Scope

Pillar 11 provides backend-owned in-app notifications created only by approved academic workflows.

Implemented database models:

- `AcademicEvent`
- `Notification`
- immutable academic-event records
- unique backend-generated academic-event keys
- unique event-recipient notification pairs
- recipient-owned unread and read state
- read timestamps
- deterministic notification timestamps and ordering

Implemented notification schemas:

- internal academic-event creation contract
- internal notification creation contract
- recipient-safe notification response
- paginated notification list response
- unread-count response
- mark-all-read response
- strict schema validation
- prohibited sensitive event-data keys
- backend-controlled event and recipient fields

Implemented notification service operations:

- idempotent academic-event creation
- duplicate-safe recipient notification creation
- event-key conflict detection
- active and verified recipient validation
- recipient-owned notification listing
- deterministic pagination
- read and unread filtering
- unread-count calculation
- get one recipient-owned notification
- idempotent mark-one-read operation
- owner-scoped mark-all-read operation

Implemented notification endpoints:

- `GET /notifications/`
- `GET /notifications/unread-count`
- `GET /notifications/{notification_id}`
- `PATCH /notifications/{notification_id}/read`
- `PATCH /notifications/read-all`

Notification routes are read-state and retrieval operations only.

There is no client-facing notification-creation endpoint.

---

## Approved Academic Event Workflows

Implemented trusted academic-event templates:

- activity published
- submission created
- grade released
- classroom archived

Clients cannot submit arbitrary event types, recipients, event keys, titles, messages, or event payloads.

Recipients are resolved exclusively by trusted backend ownership and enrollment rules.

---

## Domain Integrations

### Activity Publication

Successful activity publication triggers privacy-safe notifications for eligible active enrolled students.

Behavior:

- notifications are created only for published activities
- the activity must belong to the authenticated instructor
- the classroom must be active
- publication uses the backend-controlled `published_at`
- repeated publication requests reuse the same idempotent event key
- repeated publication does not create duplicate notifications
- unpublishing does not create a notification
- notification workflow failure does not undo a successfully committed publication
- repeating publication safely retries missing notification creation
- notification failure is exposed as controlled HTTP `503 Service Unavailable`

### Submission Creation

Creating a student submission triggers a privacy-safe notification for the instructor who owns the activity.

Behavior:

- submission ownership comes from the authenticated student
- only published graded activities accept official submissions
- active enrollment is required
- source code and standard input remain immutable
- the latest accepted attempt becomes the official attempt
- the submission, academic event, and instructor notification are saved atomically
- notification workflow failure rolls back the new attempt
- retrying after failure does not consume an attempt number
- notification failure is exposed as controlled HTTP `503 Service Unavailable`

### Grade Release

A student notification is created only when a manual instructor grade changes from unreleased to released.

Behavior:

- only the owning instructor may release the grade
- only the latest accepted official submission may receive the official grade
- automated AST, similarity, execution, and behavioral indicators never populate the grade
- ordinary score or feedback edits do not create release notifications
- editing an already released grade does not create a duplicate notification
- the release transition, academic event, and student notification are saved atomically
- notification workflow failure rolls back the release transition
- notification failure is exposed as controlled HTTP `503 Service Unavailable`

### Classroom Archive

Changing an instructor-owned classroom from active to inactive triggers privacy-safe notifications for eligible active enrolled students.

Behavior:

- `archived_at` is set by the backend on the active-to-inactive transition
- reactivating a classroom clears `archived_at`
- repeated inactive updates preserve the original archive timestamp
- repeated inactive updates do not create duplicate notifications
- only active, verified, active-account students are recipients
- disabled and removed enrollments are excluded
- archiving a classroom with no eligible recipients still succeeds
- the archive transition, academic event, and notifications are saved atomically
- notification workflow failure rolls back the archive transition
- notification failure is exposed as controlled HTTP `503 Service Unavailable`

---

## OpenAPI and API Contracts

The OpenAPI contract includes:

- the `Notifications` tag
- all five notification endpoints
- authenticated access requirements
- owner-scoped notification retrieval
- owner-scoped read-state operations
- documented HTTP `503` responses for notification-dependent domain workflows
- no client-facing notification creation request body
- recipient-safe notification response fields
- backend version `0.11.0`

The public notification response includes only:

- notification identifier
- academic-event identifier
- event type
- resource type
- resource identifier
- title
- message
- read state
- read timestamp
- notification creation timestamp
- academic-event occurrence timestamp

Internal recipient identifiers, actor identifiers, event keys, and event payloads are not exposed.

---

## Verified Test Coverage

Verified full backend regression:

```text
255 passed
```

Pillar 11 tests cover:

- academic-event table registration
- notification table registration
- academic-event type and resource constraints
- unique academic-event keys
- unique event-recipient notification pairs
- multiple recipients for one event
- ORM relationships
- event creation idempotency
- event-key conflict detection
- inactive-recipient rejection
- recipient ownership
- deterministic ordering
- notification pagination
- read and unread filters
- unread counts
- owner-only notification retrieval
- idempotent mark-one-read
- owner-scoped mark-all-read
- authentication requirements
- page-size validation
- activity publication notifications
- repeated publication idempotency
- submission-created instructor notifications
- submission rollback on notification failure
- grade-release transition notifications
- no duplicate notification for later released-grade edits
- classroom archive notifications
- archive recipient filtering
- archive success with no eligible recipients
- archive rollback on notification failure
- notification privacy contracts
- OpenAPI notification route contracts
- OpenAPI notification failure-response documentation

---

## Non-Negotiable Security and Privacy Rules

- Clients cannot create academic events.
- Clients cannot create notifications.
- Clients cannot choose notification recipients.
- Clients cannot choose event keys.
- Clients cannot choose notification titles or messages.
- Notification ownership comes from the authenticated database user.
- Notification content comes only from trusted backend templates.
- Academic events and notifications never contain source code.
- Academic events and notifications never contain starter code.
- Academic events and notifications never contain standard input.
- Academic events and notifications never contain hidden test cases.
- Academic events and notifications never contain expected outputs.
- Academic events and notifications never contain AST rules or findings.
- Academic events and notifications never contain similarity details.
- Academic events and notifications never contain execution output.
- Academic events and notifications never contain worker identifiers.
- Academic events and notifications never contain coding-session telemetry.
- Clipboard contents and pasted text are never stored.
- Browsing history is never collected.
- Screen recordings are never collected.
- Webcam data is never collected.
- Microphone data is never collected.
- Individual keystrokes are never collected.
- Unreleased scores and feedback are never included.
- Grade-release notifications are created only for manually released grades.
- Automated indicators never assign grades.
- Automated indicators never determine plagiarism, cheating, copying, or misconduct.
- Pillar 11 provides in-app notifications only.
- Email, SMS, and push delivery remain outside Pillar 11.
- Student Python code never executes inside React or FastAPI.
- Student code executes only through the partner-owned isolated sandbox worker.

---

## Final Pillar 11 Git Procedure

From the repository root, verify the current branch:

```powershell
git branch --show-current
```

Expected:

```text
review/backend-p11-notification-workflow
```

Run final checks:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
cd ..
git diff --check
git status --short
```

Stage only exact Pillar 11 files.

Do not use:

```powershell
git add .
```

Commit the completed review branch locally:

```powershell
git commit -m "feat: complete in-app notification workflows"
```

Do not push the review branch.

Merge locally into `dev`:

```powershell
git switch dev
git merge --no-ff review/backend-p11-notification-workflow
```

Run the full backend regression again on `dev`:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
cd ..
```

Expected:

```text
255 passed
```

Push only `dev`:

```powershell
git push origin dev
```

---

## Next Pillar

Continue with:

- Pillar 12 — Audit Trail and Academic Accountability
- Target backend version: `0.12.0`

Create the next local review branch from the updated `dev` branch:

```powershell
git switch dev
git pull --ff-only origin dev
git switch -c review/backend-p12-audit-trail
```

Do not push the Pillar 12 review branch.

---

## Pillar 12 Starting Direction

Begin by designing backend-owned audit records for security-sensitive and academically accountable actions.

Initial audit scope should consider:

- authentication-relevant account actions
- classroom creation and archive transitions
- enrollment status changes
- activity publication changes
- immutable submission creation
- manual grade creation and updates
- grade release transitions
- notification read-state changes only when academically necessary
- authenticated actor identity
- target resource identity
- action type
- timestamp
- privacy-safe structured metadata

Audit records must not contain:

- passwords
- password hashes
- OTP values
- source code
- standard input
- hidden test data
- execution output
- clipboard contents
- pasted text
- browsing history
- individual keystrokes
- webcam or microphone data
- automatic misconduct conclusions

The audit trail must support accountability and authorized review without becoming a surveillance system.
