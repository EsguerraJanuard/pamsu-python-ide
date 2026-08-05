# Backend Reverse-Engineering Learning Roadmap

## 1. Repository Verification Summary
- **Current Branch Inspected:** practice
- **Current Commit Inspected:** da971736973702c21b2783f1ce74166e000e6f81
- **Backend Release Baseline:** version 1.0.0 (Release Candidate verified)
- **Migration Head:** 9f2c6e4a1b7d
- **Tests Passing:** 731 tests

## 2. Learning Assumptions & Prerequisite Map
**Target Audience:** Beginner Python developer transitioning to a modern web backend architecture.

**Prerequisites to Master First (Phase 0):**
- Python 3 decorators, context managers, and type hints.
- Pydantic models vs SQLAlchemy models.
- Async vs Sync execution in Python.
- HTTP methods, status codes, and JSON payloads.
- JWT basics (Headers, Payload/Claims, Signature).

## 3. Pillars 1–16 Reconstruction Table

| Pillar | Name | Version | Objective | Prerequisites | Key Files | Migration Impact | Difficulty (1-5) | Est. Time | Focus Level |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Core Security and Domain Foundation | 0.1.0 | Establish base app, database, and JWT security. | None | `main.py`, `database.py`, `security.py`, `domain_models.py` | Baseline Schema | 3 | 4h | Line-by-line |
| 2 | OTP Registration | 0.2.0 | Secure signup with school email and OTP. | 1 | `auth.py`, `registration.py`, `otp_service.py` | OTP tables | 3 | 4h | Control-flow |
| 3 | API and OpenAPI Contracts | 0.3.0 | Define standard inputs/outputs. | 1, 2 | `user_schema.py`, `otp_schema.py` | None | 2 | 2h | Interface |
| 4 | Classrooms and Enrollment | 0.4.0 | Role-based boundaries for classrooms. | 1-3 | `classrooms.py`, `classroom_service.py` | Classrooms/Enrollment | 3 | 4h | Line-by-line |
| 5 | Activities and Test Cases | 0.5.0 | Instructor-created tasks and tests. | 4 | `activities.py`, `task_service.py` | Tasks, TestCases | 3 | 3h | Control-flow |
| 6 | Immutable Submission Workflow | 0.6.0 | Record student attempts immutably. | 5 | `submissions.py`, `submission_service.py` | Submissions | 4 | 5h | Line-by-line |
| 7 | Execution Request Workflow | 0.7.0 | Queue code for partner sandbox. | 6 | `execution.py`, `execution_service.py` | Execution Requests | 4 | 5h | Line-by-line |
| 8 | Coding Sessions and Telemetry | 0.8.0 | Privacy-safe aggregate telemetry. | 4 | `coding_session_service.py` | Sessions | 3 | 3h | Interface |
| 9 | Evaluation and Manual Grading | 0.9.0 | AST, Jaccard indicators, and manual grades. | 7 | `evaluation.py`, `ast_evaluator.py`, `jaccard.py` | Evaluations, Grades | 4 | 5h | Control-flow |
| 10 | Review Queue and Gradebook | 0.10.0 | Instructor views and grade summaries. | 9 | `instructor.py`, `review_queue_service.py` | None | 3 | 4h | Interface |
| 11 | Notifications and Academic Events | 0.11.0 | In-app event signaling. | 1-10 | `notifications.py`, `notification_service.py` | Notifications | 2 | 3h | Interface |
| 12 | Audit Trail | 0.12.0 | Immutable accountability logging. | 1-10 | `audit_records.py`, `audit_service.py` | AuditLogs | 2 | 3h | Interface |
| 13 | Reporting and CSV Export | 0.13.0 | Privacy-safe aggregation exports. | 10 | `reporting.py`, `reporting_service.py` | None | 3 | 3h | Control-flow |
| 14 | Partner Integration Contracts | 0.14.0 | Isolated worker boundaries. | 7 | `partner_auth.py`, `test_openapi_contracts.py` | Idempotency | 4 | 4h | Line-by-line |
| 15 | API Hardening and Concurrency | 0.15.0 | Idempotency, race condition handling. | 1-14 | `test_submission_concurrency.py` | Optimizations | 5 | 6h | Line-by-line |
| 16 | V-Model Verification | 1.0.0-rc1 | Final acceptance and requirements trace. | 1-15 | `test_api_workflow.py` | None | 4 | 5h | Reference |

## 4. Backend Dependency and Request-Flow Overview
**Standard Flow:**
1. **Entry Router:** Receives HTTP request, injects dependencies.
2. **Dependency:** Checks JWT, loads current user, validates roles.
3. **Schema:** Validates incoming JSON payload (Pydantic).
4. **Service:** Applies business logic, checks ownership/authorization.
5. **Model:** Translates logical actions into database operations (SQLAlchemy).
6. **Transaction:** Commits or rolls back.
7. **Response Schema:** Serializes database model back to JSON for the frontend.

## 5. File-Priority Matrix
*See section 6 for Top Critical Files. Detailed matrix is available upon tracing tasks.*

## 6. Files I Must Struggle to Understand (Top Critical Ranked)
1. `backend/app/main.py` (Critical) - Application startup, middleware, router registration.
2. `backend/app/core/security.py` (Critical) - JWT encoding/decoding, role verification.
3. `backend/app/core/database.py` (Critical) - Engine, sessionmaker, dependencies.
4. `backend/app/models/domain_models.py` (Critical) - All SQLAlchemy relationships.
5. `backend/app/models/user.py` (Critical) - User roles and attributes.
6. `backend/app/routers/auth.py` (Critical) - Login flow and token dispensing.
7. `backend/app/services/otp_service.py` (Critical) - Registration transaction flow.
8. `backend/app/services/classroom_service.py` (High) - Role-based authorization in practice.
9. `backend/app/services/submission_service.py` (High) - Immutable constraints on student attempts.
10. `backend/app/services/execution_service.py` (High) - Boundary between FastAPI and Partner worker.
11. `backend/app/services/evaluation_service.py` (High) - AST and Jaccard orchestration.
12. `backend/app/routers/instructor.py` (High) - Grading boundaries.
13. `backend/tests/test_api_workflow.py` (Critical) - End-to-end integration proof.
14. `backend/tests/test_submission_concurrency.py` (High) - Transaction isolation and locks.
15. `backend/alembic/env.py` (Medium) - How migrations hook into SQLAlchemy metadata.

## 7. Deferred Files (Do Not Focus Early)
- `backend/app/tasks/celery_worker.py` - Not operational in verified 1.0.0.
- `backend/app/integrations/local_llm.py` - External and non-authoritative.
- `backend/app/db/upgrade_p15_legacy_schema.py` - Legacy context.
- Generated OpenAPI JSON.

## 8. Workflow Tracing Index
1. **Registration start**: auth.py -> otp_service.py -> models
2. **OTP verification**: registration.py -> otp_service.py -> user.py
3. **Login**: auth.py -> security.py -> user.py
4. **Create classroom**: classrooms.py -> classroom_service.py -> domain_models.py
5. **Join classroom**: classrooms.py -> classroom_service.py -> domain_models.py
6. **Create activity**: activities.py -> task_service.py -> domain_models.py
7. **Publish activity**: activities.py -> task_service.py -> domain_models.py
8. **View available activity**: activities.py -> task_service.py
9. **Start coding session**: activities.py -> coding_session_service.py
10. **Update telemetry**: activities.py -> coding_session_service.py
11. **Create submission**: submissions.py -> submission_service.py
12. **Queue execution**: execution.py -> execution_service.py
13. **Receive partner result**: execution.py -> execution_service.py
14. **Evaluate submission**: evaluation.py -> evaluation_service.py
15. **View instructor queue**: instructor.py -> review_queue_service.py
16. **Set manual grade**: instructor.py -> gradebook_service.py
17. **Release grade**: instructor.py -> gradebook_service.py
18. **Student views grade**: activities.py -> gradebook_service.py
19. **Generate notification**: activities.py -> notification_service.py
20. **Generate report**: reporting.py -> reporting_service.py
21. **Retrieve audit record**: audit_records.py -> audit_service.py

## 9. Day-by-Day Schedule (Aug 1 - Sept 6, 2026)

**Five-Pass Study Method Reminder:**
1. Orientation (Identify imports/classes)
2. Call-flow tracing (Router -> Service -> DB)
3. Line-by-line prediction (Guess before reading)
4. Evidence through tests (Run safely, compare)
5. Teach-back (Explain aloud, draw)
AI Help Threshold: Struggle for at least 30 minutes, write a prediction, and read the test before asking AI for a hint (never a full answer).

### Week 1: Application Boot & Core Identity
* **Day 1 (Aug 1): Repository Orientation & Python Boot** - Review file structure, `main.py`, FastAPI instantiation. Q: How does uvicorn invoke this app?
* **Day 2 (Aug 2): Configuration & Database Init** - Read `config.py` & `database.py`. Q: How is the database session yielded to the router?
* **Day 3 (Aug 3): Authentication Foundations** - Read `security.py`. Q: What claims are packed into the JWT? How are passwords hashed?
* **Day 4 (Aug 4): Registration Flow (Part 1)** - Read `routers/auth.py` & `routers/registration.py`. Q: Why is OTP generated but not stored in plaintext?
* **Day 5 (Aug 5): Registration Flow (Part 2)** - Read `services/otp_service.py`. Trace the transaction. Q: What happens if OTP verification fails midway?
* **Day 6 (Aug 6): User Models & Relationships** - Read `models/user.py`. Draw the ERD for Users and Roles.
* **Day 7 (Aug 7): Catch-up & Weekly Checkpoint 1**

### Week 2: Classrooms, Enrollment & Tasks
* **Day 8 (Aug 8): Classroom Routing** - Read `routers/classrooms.py`. Q: How are roles enforced at the router level?
* **Day 9 (Aug 9): Classroom Services** - Read `services/classroom_service.py`. Q: Where is ownership actually checked?
* **Day 10 (Aug 10): Domain Models (Part 1)** - Read `models/domain_models.py` (Classroom, Enrollment). Q: How does SQLAlchemy handle the many-to-many relationship?
* **Day 11 (Aug 11): Task and Activity Routing** - Read `routers/activities.py`. Q: How do students and instructors get different data?
* **Day 12 (Aug 12): Task Service** - Read `services/task_service.py`. Q: How are hidden test cases protected?
* **Day 13 (Aug 13): Domain Models (Part 2)** - Read `models/domain_models.py` (Tasks, TestCases). Draw the ERD.
* **Day 14 (Aug 14): Catch-up & Weekly Checkpoint 2**

### Week 3: Submissions & Executions
* **Day 15 (Aug 15): Submission Workflow** - Read `routers/submissions.py`. Q: Why are submissions immutable?
* **Day 16 (Aug 16): Submission Service** - Read `services/submission_service.py`. Q: How is the "latest attempt" tracked?
* **Day 17 (Aug 17): Coding Sessions** - Read `services/coding_session_service.py`. Q: How does privacy-safe counting work?
* **Day 18 (Aug 18): Execution Boundaries** - Read `routers/execution.py`. Q: Why is student code NOT executed here?
* **Day 19 (Aug 19): Partner Sandbox Contracts** - Read `services/execution_service.py`. Q: How does the system handle duplicate partner updates?
* **Day 20 (Aug 20): Concurrency & Idempotency** - Read `tests/test_execution_request_idempotency.py`. Q: What prevents race conditions?
* **Day 21 (Aug 21): Catch-up & Weekly Checkpoint 3**

### Week 4: Evaluation, Review, and Grading
* **Day 22 (Aug 22): AST and Similarity** - Read `services/ast_evaluator.py`, `services/jaccard.py`. Q: Why are these indicators only, not grades?
* **Day 23 (Aug 23): Evaluation Orchestration** - Read `services/evaluation_service.py`.
* **Day 24 (Aug 24): Instructor Review Queue** - Read `routers/instructor.py`, `services/review_queue_service.py`. Q: How are N+1 queries avoided here?
* **Day 25 (Aug 25): Manual Grading** - Read `services/gradebook_service.py`. Q: Where is the rule that only humans assign grades?
* **Day 26 (Aug 26): Notifications** - Read `services/notification_service.py`.
* **Day 27 (Aug 27): Audit Trails** - Read `services/audit_service.py`. Q: What makes an audit record immutable?
* **Day 28 (Aug 28): Catch-up & Weekly Checkpoint 4**

### Week 5: Reporting, Migrations, and Contracts
* **Day 29 (Aug 29): Reporting & CSV** - Read `services/reporting_service.py`. Q: How is data anonymized for exports?
* **Day 30 (Aug 30): Alembic Migrations** - Read `alembic/env.py` and `baseline_schema.py`. Q: How does schema evolution track model changes?
* **Day 31 (Aug 31): OpenAPI Contracts** - Inspect `OPENAPI_1_0_0.json`. Q: How does the frontend know the exact types?
* **Day 32 (Sept 1): Concurrency Tests** - Read `test_submission_concurrency.py`.
* **Day 33 (Sept 2): End-to-End Workflow** - Read `test_api_workflow.py`. Trace the entire lifecycle of one student.
* **Day 34 (Sept 3): Catch-up & Final Review Prep**

### Week 6: Thesis Defense Synthesis
* **Day 35 (Sept 4): Security & Privacy Boundaries** - Re-read `CURRENT_HANDOFF.md`. Practice explaining boundaries aloud.
* **Day 36 (Sept 5): Architecture & Scaling** - Draw the entire system architecture on a whiteboard.
* **Day 37 (Sept 6): Final Mastery Checkpoint**

## 10. Weekly Checkpoints (Example Structure)
1. **Knowledge Checklist:** Check off all completed concepts.
2. **Oral Defense Questions:** 5 questions to answer aloud without notes.
3. **Architecture Drawing:** 1 diagram requirement.
4. **Workflow Tracing:** 1 specific workflow to trace end-to-end.
5. **Database Exercise:** Explain 1 ERD relationship.
6. **Security/Privacy:** Explain 1 boundary.
7. **Test-Reading:** Predict the outcome of 1 test file.
8. **Self-Rating (1-5):** Honest assessment.
9. **Remediation Plan:** If < 4, repeat the weakest topic.

## 11. Study-Question Bank (No Answers Provided)
- What is the difference between authentication and authorization in this backend?
- Why do we have both Pydantic schemas and SQLAlchemy models?
- What happens if the database connection drops during an execution request?
- How does the system prevent a student from seeing another student's hidden test cases?
- Why is an AST evaluation stored but never automatically applied as a final grade?

## 12. Common Misconception Checklist
* [ ] Python module vs package
* [ ] FastAPI app vs Uvicorn server
* [ ] Route vs Router
* [ ] Request schema vs ORM model
* [ ] ORM model vs actual database row
* [ ] Authentication vs Authorization
* [ ] JWT decoding vs authoritative backend permission
* [ ] Dependency injection vs normal function calls
* [ ] Database engine vs session
* [ ] Flush vs commit vs refresh vs rollback
* [ ] Application validation vs database constraint
* [ ] Submission vs execution request
* [ ] Coding session vs behavioral log
* [ ] Official attempt vs latest attempt
* [ ] AST indicator vs grade
* [ ] Similarity indicator vs plagiarism verdict
* [ ] Hidden test vs public sample test
* [ ] Manual grade vs released grade
* [ ] Idempotency vs concurrency locking
* [ ] Unit test vs workflow test vs contract test

## 13. Thesis-Defense Preparation Checklist
* [ ] I can trace a request from router to database without AI.
* [ ] I can explain the exact JWT claims used.
* [ ] I can defend why the sandbox is isolated.
* [ ] I can map the 16 pillars to the current architecture.
* [ ] I can point to the exact file where ownership is checked.

## 14. Progress Tracker
* [ ] Week 1
* [ ] Week 2
* [ ] Week 3
* [ ] Week 4
* [ ] Week 5
* [ ] Week 6

## 15. Catch-Up Strategy
- Do not skip foundational weeks (Weeks 1-2). If behind, push the schedule back.
- Skip Tier C (Deferred Files) if time is short.
- Focus strictly on Top Critical Files if the defense date is moved up.

## 16. Final Mastery Rubric
- **Level 1 (Failing):** Relies on AI to trace workflows.
- **Level 3 (Passing):** Can trace workflows and explain security boundaries.
- **Level 5 (Mastery):** Can identify exact line numbers for business rules, explain race condition protections, and draw the full ERD from memory.

## 17. Recommended Order for Future Interactive Study Chats
1. Phase 1: Core App & Identity (Ask me to quiz you on `main.py` and `security.py`).
2. Phase 2: Domain Models (Ask me to verify your handwritten ERD).
3. Phase 3: The Execution Boundary (Ask me to act as the Partner Sandbox sending malicious payloads).
4. Phase 4: Workflow Tracing (Ask me to present a broken workflow and you identify the missing authorization check).
