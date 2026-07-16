# PAMSU Python IDE — Canonical Backend Roadmap

## Authority
This is the canonical backend sequence. AI assistants must not rename, reorder, skip, or invent pillars without explicit user approval recorded here.

## Permanent Rules
- Backend: FastAPI, PostgreSQL, SQLAlchemy, Pydantic V2, JWT.
- Frontend: React, Vite, Tailwind CSS.
- Student Python executes only in the partner-owned isolated sandbox, never in React or FastAPI.
- AST, similarity, execution, and session indicators are review-only.
- No automated grade, plagiarism, cheating, copying, misconduct, or risk verdict.
- Students see only their own permitted data and released grades.
- Feature/review/fix branches remain local; merge locally into `dev`; push only `dev`.
- Canonical schema test: `backend/tests/test_schemas.py`.

## Completed Pillars
1. Core Security and Domain Foundation — `0.1.0` — Completed
2. OTP Registration — `0.2.0` — Completed
3. API and OpenAPI Contracts — `0.3.0` — Completed
4. Classrooms and Enrollment — `0.4.0` — Completed
5. Activities and Test Cases — `0.5.0` — Completed
6. Immutable Submission Workflow — `0.6.0` — Completed
7. Execution Request Workflow — `0.7.0` — Completed
8. Coding Sessions and Privacy-Safe Telemetry — `0.8.0` — Completed
9. Structural Evaluation Review and Manual Grading — `0.9.0` — Completed and hardened

Pillar 9 verified regression: `185 passed`.

---

## Pillar 10 — Instructor Review Queue and Gradebook APIs
**Status:** Next  
**Version:** `0.10.0`  
**Local branch:** `review/backend-p10-review-queue-gradebook`

Scope:
- instructor-owned review queues by classroom/activity;
- bounded pagination, deterministic sorting, and filters;
- states: submitted, awaiting review, graded, rejected;
- official/unofficial attempt filtering;
- classroom/activity gradebook summaries;
- authenticated student released-grade list;
- counts for awaiting review, graded, rejected, and unreleased grades;
- no raw source code in summary endpoints;
- no automated risk or misconduct priority score;
- avoid N+1 queries.

Required tests:
- owner instructor allowed;
- another instructor denied;
- students denied from instructor endpoints;
- released/unreleased visibility;
- official/unofficial filtering;
- pagination/filter/sort contracts;
- OpenAPI and full regression.

Definition of done:
- role-safe review queue and gradebook APIs;
- version `0.10.0`;
- focused and full tests pass;
- local branch merged to `dev`;
- only `dev` pushed.

## Pillar 11 — In-App Notification and Academic Event Workflow
**Status:** Planned  
**Version:** `0.11.0`  
**Local branch:** `review/backend-p11-notification-workflow`

Scope:
- in-app notifications for activity published, due-date events, accepted/rejected submission, and grade release;
- unread/read state;
- pagination;
- idempotent event creation;
- users access only their own notifications;
- no source code, similarity verdict, or unreleased-grade leak.

Excluded:
- SMTP/provider implementation;
- background scheduler infrastructure;
- push infrastructure.

## Pillar 12 — Audit Trail and Academic Accountability
**Status:** Planned  
**Version:** `0.12.0`  
**Local branch:** `review/backend-p12-audit-trail`

Scope:
- immutable audit events for grade changes/releases, status changes, classroom archive, enrollment changes, and activity publishing;
- actor, action, resource, timestamp, correlation ID, and minimal metadata;
- no source code, OTPs, passwords, JWTs, clipboard text, or surveillance data;
- no audit event when the main transaction fails.

## Pillar 13 — Reporting and Privacy-Safe Export APIs
**Status:** Planned  
**Version:** `0.13.0`  
**Local branch:** `review/backend-p13-reporting-exports`

Scope:
- classroom and activity completion summaries;
- grade distributions based on manual grades;
- missing-submission reports;
- gradebook CSV export;
- student personal progress summary;
- ownership-safe exports;
- no raw source export by default;
- no automated misconduct ranking.

## Pillar 14 — Partner Integration Contracts
**Status:** Planned  
**Version:** `0.14.0`  
**Local branch:** `review/backend-p14-partner-contracts`

Scope:
- isolated-worker request/result contracts;
- authenticated result updates;
- allowed execution lifecycle transitions;
- replay/idempotency protection;
- correlation IDs and result-size validation;
- OTP email-adapter interface;
- local LLM interface boundary;
- health/readiness contracts.

Excluded:
- Celery, Redis, Docker, sandbox, resource-limit, email-provider, and LLM-runtime implementation.

Local LLM may draft explanations, hints, or feedback, but must never set grades or determine plagiarism/misconduct.

## Pillar 15 — API Hardening, Concurrency, and Database Readiness
**Status:** Planned  
**Version:** `0.15.0`  
**Local branch:** `review/backend-p15-api-hardening`

Scope:
- common bounded pagination and deterministic ordering;
- idempotency for retry-prone writes;
- row-locking and transaction review;
- concurrent official-attempt and grade-write tests;
- N+1 and index review;
- Alembic baseline and migration smoke tests;
- configuration validation;
- privacy-safe structured logging and correlation IDs;
- safe CORS/security configuration.

## Pillar 16 — V-Model Verification and Release Candidate
**Status:** Planned  
**Version:** `1.0.0-rc1`  
**Local branch:** `review/backend-p16-release-candidate`

Scope:
- requirements-to-test traceability matrix;
- end-to-end backend acceptance scenarios;
- complete authentication, classroom, activity, submission, execution, session, evaluation, grading, notification, audit, reporting, and partner-contract verification;
- privacy and security negative tests;
- migration verification;
- OpenAPI contract freeze;
- frontend and partner handoff packages;
- changelog and release notes.

Definition of done:
- all approved requirements map to passing tests;
- zero unresolved high-severity defects;
- release-candidate contracts frozen.

## Final Release — Backend 1.0.0
**Status:** Planned after release-candidate acceptance  
**Version:** `1.0.0`

No new features. Only release-candidate fixes, documentation, migration corrections, contract-preserving security fixes, final changelog, and approved release tagging.

---

## Pillar Completion Gate
A pillar is complete only when:
1. requirements and contracts are confirmed;
2. authorization, privacy, immutability, and execution boundaries remain intact;
3. database transactions are safe;
4. compile/import checks pass;
5. focused tests pass;
6. pillar tests pass;
7. full regression passes;
8. OpenAPI and version are updated;
9. handoff is updated;
10. work is committed on a local branch;
11. merged locally into `dev`;
12. only `dev` is pushed;
13. working tree is clean.
