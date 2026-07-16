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

Current local working branch: `review/backend-p11-notification-workflow`

Backend version: `0.10.0`

Last completed pillar:

- Pillar 10 — Instructor Review Queue and Gradebook APIs

Current work in progress:

- Pillar 11 — In-App Notification and Academic Event Workflow
- Target backend version: `0.11.0`

The current review branch must remain local.

Do not merge into `dev` and do not push until Pillar 11 is complete and fully verified.

---

## Pillar 11 Implemented So Far

Implemented database models:

- `AcademicEvent`
- `Notification`
- unique academic-event key
- unique event-recipient notification pair
- recipient-owned read state
- immutable academic-event records

Implemented notification schemas:

- internal academic-event creation contract
- internal notification creation contract
- recipient-safe notification response
- paginated notification list
- unread-count response
- mark-all-read response

Implemented notification service operations:

- idempotent academic-event creation
- duplicate-safe recipient notification creation
- notification listing and pagination
- unread and read filtering
- unread-count calculation
- get one recipient-owned notification
- mark one notification as read
- mark all recipient notifications as read

Implemented notification endpoints:

- `GET /notifications/`
- `GET /notifications/unread-count`
- `GET /notifications/{notification_id}`
- `PATCH /notifications/{notification_id}/read`
- `PATCH /notifications/read-all`

Implemented approved academic-event templates:

- activity published
- submission created
- grade released
- classroom archived

Implemented domain integration so far:

- successful activity publication triggers the approved activity-published notification workflow
- repeated publication requests reuse the same academic-event key
- notification failure does not undo a successfully committed publication

Implemented tests:

- notification model constraints
- duplicate academic-event prevention
- duplicate event-recipient prevention
- recipient ownership
- notification pagination
- read and unread filters
- unread counts
- mark-one-read idempotency
- mark-all-read ownership
- academic-event notification idempotency
- inactive-recipient rejection
- notification privacy contracts

Latest expected regression before this WIP commit:

- `247 passed`

---

## Pillar 11 Remaining Work

- map `TaskNotificationWorkflowError` in the instructor router
- integrate submission-created notifications into the submission workflow
- integrate grade-released notifications into the manual grading workflow
- integrate classroom-archived notifications into the classroom workflow
- add approved event workflow integration tests
- add complete privacy and OpenAPI contract tests
- bump backend version from `0.10.0` to `0.11.0`
- run final full regression
- update this handoff with the completed Pillar 11 state
- commit final Pillar 11 changes
- merge locally into `dev`
- push only `dev`

---

## Non-Negotiable Rules

- Clients cannot create academic events or notifications.
- Clients cannot choose notification recipients.
- Notification ownership comes from the authenticated database user.
- Notification content comes only from trusted backend templates.
- Academic events and notifications never contain source code.
- Academic events and notifications never contain standard input.
- Hidden test cases and expected outputs are never included.
- AST and similarity details are never included.
- Execution output and session telemetry are never included.
- Clipboard contents and pasted text are never stored.
- Unreleased scores and feedback are never included.
- Grade-release notifications are created only for manually released grades.
- Automated indicators never assign grades.
- Automated indicators never determine plagiarism, cheating, copying, or misconduct.
- Pillar 11 provides in-app notifications only.
- Email, SMS, and push delivery remain outside Pillar 11.
- Student Python code never executes inside React or FastAPI.
- Student code executes only through the partner-owned isolated sandbox worker.

---

## Resume Point

Continue with:

```text
backend/app/routers/instructor.py
```

Add controlled HTTP exception mapping for:

```text
TaskNotificationWorkflowError
```

After completing all Pillar 11 integrations and tests, update the backend version to `0.11.0`.
