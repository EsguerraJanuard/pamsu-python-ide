# PAMSU Python IDE — Canonical Project Context

## Project
PAMSU Web-Based Python IDE with Automated Structural Analytics, developed using the V-Model.

Backend: FastAPI, PostgreSQL, SQLAlchemy, Pydantic V2, JWT.  
Frontend: React, Vite, Tailwind CSS.

## Ownership
User/backend lead owns core models, schemas, services, routers, authorization, OTP workflow, classrooms, enrollments, activities, test cases, submissions, AST/Jaccard integration, evaluation, grading, reporting, and API contracts.

Partner owns Celery, Redis, Docker sandbox, execution resource limits, execution infrastructure, OTP email delivery adapter, and local LLM runtime/integration.

FastAPI must not absorb partner-owned infrastructure.

## Core Domain Rules
- Registration only accepts `@pampangastateu.edu.ph`.
- School ID is exactly 10 digits, stored as a string, and unique.
- Email is unique.
- Client registration never chooses role.
- Instructor role is backend-controlled through the allowlist.
- OTP generation, hashing, expiry, attempt limits, resend limits, and verification are backend-owned.
- Instructors own classrooms; class codes are backend-generated.
- Activities are `laboratory` or `homework`.
- Hidden test-case content is never student-visible.
- Paste policy is `internal_only` or `disabled`.
- Submission attempts are immutable.
- Attempt numbering and official-attempt state are backend-controlled.
- Only the latest accepted attempt may be official.
- Student Python never executes in React or FastAPI.
- Actual execution occurs only in the partner-owned isolated worker.
- AST, similarity, execution, and session indicators are review-only.
- Automated indicators never assign grades or declare plagiarism, copying, cheating, misconduct, academic dishonesty, or a risk score.
- Full AST and similarity details are instructor-only.
- Students see only their own permitted data.
- Only the activity owner may assign a manual grade.
- Unreleased grades are hidden from students.
- Official grade only for the latest accepted official submission.
- Grade changes do not silently change submission review status.
- Marking `graded` requires an existing manual grade.

## Privacy Rules
Allowed aggregate telemetry:
- tab-switch count;
- blocked-paste count;
- run-attempt count;
- idle-duration total;
- approved timestamps.

Never collect/store:
- clipboard contents;
- pasted external text;
- browsing history;
- screen recording;
- webcam;
- microphone;
- every keystroke.

## Architecture Rules
- Services use domain/service exceptions.
- Routers translate service exceptions into HTTP responses.
- Database writes use guarded commit/rollback.
- Authorization is enforced in backend logic.
- Frontend hiding is not authorization.
- Avoid N+1 queries.
- Do not introduce roles, statuses, fields, endpoints, or architectural changes without checking the roadmap and current code.

## Testing and Git
- Canonical schema test: `backend/tests/test_schemas.py`.
- Never use `backend/tests/test_schema.py`.
- Feature/review/fix branches are local only.
- Merge locally into `dev`.
- Push only `dev`.
- Do not commit while focused or full regression tests fail.

## Current Verified State
Completed Pillars 1–9.  
Backend version: `0.9.0`.  
Latest verified regression: `185 passed`.
