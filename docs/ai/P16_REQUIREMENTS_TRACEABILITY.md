# PAMSU Python IDE - Pillar 16 Requirements Traceability Matrix

## Document Purpose

This document maps the approved PAMSU Python IDE backend requirements to their verification evidence for Pillar 16 - V-Model Verification and Release Candidate.

Target backend version:

```text
1.0.0-rc1
```

Current local review branch:

```text
review/backend-p16-release-candidate
```

The canonical requirement source is:

```text
docs/ai/PROJECT_CONTEXT.md
```

The authoritative Pillar 16 scope is:

```text
docs/ai/ROADMAP.md
```

The complete collected pytest-node inventory is stored in:

```text
docs/ai/P16_TEST_NODE_INVENTORY.txt
```

Latest inherited green backend baseline from `dev`:

```text
699 passed in 120.49s (0:02:00)
```

Current Pillar 16 review-branch regression:

```text
713 passed in 124.30s (0:02:04)
```

This matrix does not yet claim final release-candidate verification.

Requirements remain `Mapped` until their exact pytest node IDs or approved procedural evidence have been recorded and verified.

Registration, OTP, classroom, activity, and paste-policy requirements are now mapped to exact passing test nodes and marked `Verified`.

A requirement may be marked `Verified` only after:

1. its exact pytest node IDs or approved procedural evidence are recorded;
2. the mapped tests pass on the Pillar 16 review branch;
3. related privacy and authorization negative tests pass where applicable;
4. the complete backend regression remains green.

---

## Status Legend

| Status | Meaning |
|---|---|
| Mapped | Relevant test files have been identified, but exact test nodes are still being audited |
| Partially Verified | Some exact test nodes have passed, but required coverage is incomplete |
| Verified | Requirement is mapped to exact passing test nodes or completed approved procedural evidence |
| Gap | No sufficient existing automated or procedural verification has been identified |
| Not Automated | Requirement is verified through an approved repository or release procedure rather than pytest |
| Blocked | Verification cannot proceed because of an unresolved defect or missing dependency |

---

## Requirement ID Convention

| Prefix | Domain |
|---|---|
| `REG` | Registration and identity |
| `OTP` | One-time password verification |
| `CLS` | Classroom ownership and enrollment |
| `ACT` | Activities and test cases |
| `PST` | Paste policy |
| `SUB` | Submission workflow |
| `EXE` | Execution workflow and partner boundary |
| `EVA` | Evaluation and review indicators |
| `GRD` | Manual grading |
| `DAT` | Student data authorization |
| `PRV` | Privacy and prohibited collection |
| `ARC` | Architecture and transaction rules |
| `TST` | Testing conventions |
| `GIT` | Git and release workflow |
| `NTF` | Notifications |
| `AUD` | Audit trail |
| `RPT` | Reporting and exports |
| `MIG` | Database migrations |
| `SEC` | Runtime and API security |
| `API` | OpenAPI and release contracts |

---

## Verified Domain Summary

| Domain | Verified requirements | Total requirements | Status |
|---|---:|---:|---|
| Registration and identity | 7 | 7 | Verified |
| OTP verification | 7 | 7 | Verified |
| Classroom ownership and enrollment | 5 | 5 | Verified |
| Activities and test cases | 5 | 5 | Verified |
| Paste policy | 3 | 3 | Verified |
| Remaining Pillar 16 domains | 0 | Pending audit | Mapped |

---

# A. Core Domain Requirements

## Registration and Identity

| Requirement ID | Canonical requirement | Source | Exact verification evidence | Current status |
|---|---|---:|---|---|
| REG-001 | Registration accepts only email addresses under `@pampangastateu.edu.ph`. | PROJECT_CONTEXT line 17 | `tests/test_schemas.py::test_valid_user_registration_input`<br>`tests/test_schemas.py::test_user_requires_university_email[student@gmail.com]`<br>`tests/test_schemas.py::test_user_requires_university_email[student@yahoo.com]`<br>`tests/test_schemas.py::test_user_requires_university_email[student@pampangastateu.edu.com]`<br>`tests/test_schemas.py::test_user_requires_university_email[invalid-email]` | Verified |
| REG-002 | School ID is exactly 10 digits. | line 18 | `tests/test_schemas.py::test_valid_user_registration_input`<br>`tests/test_schemas.py::test_school_id_must_be_exactly_ten_digits[123456789]`<br>`tests/test_schemas.py::test_school_id_must_be_exactly_ten_digits[12345678901]`<br>`tests/test_schemas.py::test_school_id_must_be_exactly_ten_digits[12345ABCDE]`<br>`tests/test_schemas.py::test_school_id_must_be_exactly_ten_digits[12345-6789]` | Verified |
| REG-003 | School ID is stored as a string. | line 18 | `tests/test_registration_otp_release_candidate.py::test_school_id_persists_as_string` | Verified |
| REG-004 | School ID is unique. | line 18 | `tests/test_registration_otp_release_candidate.py::test_existing_school_id_blocks_registration` | Verified |
| REG-005 | Email address is unique. | line 19 | `tests/test_registration_otp_release_candidate.py::test_existing_email_blocks_registration` | Verified |
| REG-006 | Client registration cannot choose an account role. | line 20 | `tests/test_schemas.py::test_user_cannot_supply_role`<br>`tests/test_openapi_contracts.py::test_registration_contract_excludes_backend_fields` | Verified |
| REG-007 | Instructor role assignment is controlled by the backend allowlist. | line 21 | `tests/test_otp_service.py::test_allowlisted_email_becomes_instructor` | Verified |

## OTP Verification

| Requirement ID | Canonical requirement | Source | Exact verification evidence | Current status |
|---|---|---:|---|---|
| OTP-001 | OTP generation is backend-owned. | line 22 | `tests/test_otp_service.py::test_start_registration_stores_only_hashed_otp`<br>`tests/test_otp_service.py::test_delivery_adapter_receives_plaintext_otp_only_transiently` | Verified |
| OTP-002 | OTP values are stored only as hashes. | line 22 | `tests/test_otp_service.py::test_start_registration_stores_only_hashed_otp`<br>`tests/test_otp_service.py::test_delivery_adapter_receives_plaintext_otp_only_transiently`<br>`tests/test_otp_service.py::test_otp_models_exclude_plaintext_and_provider_credentials` | Verified |
| OTP-003 | OTP expiration is backend-controlled. | line 22 | `tests/test_registration_otp_release_candidate.py::test_expired_otp_is_rejected` | Verified |
| OTP-004 | OTP verification-attempt limits are backend-controlled. | line 22 | `tests/test_otp_service.py::test_invalid_otp_increments_attempt_count`<br>`tests/test_registration_otp_release_candidate.py::test_maximum_otp_attempts_are_enforced` | Verified |
| OTP-005 | OTP resend limits and cooldown behavior are backend-controlled. | line 22 | `tests/test_otp_service.py::test_resend_updates_challenge_and_delivers_new_email`<br>`tests/test_registration_otp_release_candidate.py::test_resend_cooldown_is_enforced`<br>`tests/test_registration_otp_release_candidate.py::test_maximum_otp_resends_are_enforced` | Verified |
| OTP-006 | Account verification depends on valid OTP verification. | line 22 | `tests/test_otp_service.py::test_valid_otp_creates_verified_student`<br>`tests/test_otp_service.py::test_allowlisted_email_becomes_instructor` | Verified |
| OTP-007 | Plaintext OTP values are never persisted, logged, returned, or exposed in OpenAPI. | permanent privacy boundary | `tests/test_openapi_contracts.py::test_otp_challenge_response_never_exposes_plaintext_code`<br>`tests/test_otp_service.py::test_start_registration_stores_only_hashed_otp`<br>`tests/test_otp_service.py::test_delivery_adapter_receives_plaintext_otp_only_transiently`<br>`tests/test_otp_service.py::test_otp_models_exclude_plaintext_and_provider_credentials` | Verified |

## Classroom Ownership and Enrollment

| Requirement ID | Canonical requirement | Source | Exact verification evidence | Current status |
|---|---|---:|---|---|
| CLS-001 | Instructors own classrooms. | line 23 | `tests/test_classroom_workflow.py::test_instructor_can_manage_own_classroom` | Verified |
| CLS-002 | Classroom codes are generated by the backend. | line 23 | `tests/test_classroom_workflow.py::test_instructor_can_manage_own_classroom`<br>`tests/test_classroom_workflow.py::test_client_cannot_supply_classroom_owner_or_code`<br>`tests/test_classroom_openapi_contracts.py::test_classroom_create_excludes_backend_fields`<br>`tests/test_classroom_openapi_contracts.py::test_classroom_response_exposes_generated_code` | Verified |
| CLS-003 | Only authorized instructors may modify their classrooms. | architecture and ownership rules | `tests/test_classroom_workflow.py::test_instructor_can_manage_own_classroom`<br>`tests/test_classroom_workflow.py::test_instructor_cannot_manage_another_instructors_class`<br>`tests/test_classroom_release_candidate.py::test_non_owner_cannot_archive_classroom` | Verified |
| CLS-004 | Students may enroll only through approved classroom workflows. | classroom domain behavior | `tests/test_classroom_workflow.py::test_student_can_join_and_view_classroom`<br>`tests/test_classroom_workflow.py::test_duplicate_enrollment_is_rejected`<br>`tests/test_classroom_workflow.py::test_inactive_classroom_rejects_new_enrollment`<br>`tests/test_classroom_openapi_contracts.py::test_join_request_accepts_only_class_code` | Verified |
| CLS-005 | Classroom archive and membership operations preserve authorization boundaries. | ownership and notification behavior | `tests/test_classroom_workflow.py::test_instructor_can_change_enrollment_status`<br>`tests/test_classroom_workflow.py::test_instructor_cannot_manage_another_instructors_class`<br>`tests/test_classroom_release_candidate.py::test_non_owner_cannot_archive_classroom`<br>`tests/test_classroom_release_candidate.py::test_non_owner_cannot_change_enrollment_status`<br>`tests/test_notification_workflow.py::test_classroom_archive_notifies_only_active_eligible_students_once`<br>`tests/test_notification_workflow.py::test_classroom_archive_succeeds_without_active_recipients`<br>`tests/test_notification_workflow.py::test_classroom_notification_failure_rolls_back_archive` | Verified |

## Activities and Test Cases

| Requirement ID | Canonical requirement | Source | Exact verification evidence | Current status |
|---|---|---:|---|---|
| ACT-001 | Activity type is restricted to `laboratory` or `homework`. | line 24 | `tests/test_task_workflow.py::test_instructor_can_create_update_filter_and_publish_tasks`<br>`tests/test_activity_release_candidate.py::test_unsupported_activity_type_is_rejected` | Verified |
| ACT-002 | Only the owning instructor may create or modify classroom activities. | authorization rule | `tests/test_task_workflow.py::test_instructor_can_create_update_filter_and_publish_tasks`<br>`tests/test_task_workflow.py::test_instructor_cannot_create_task_in_another_classroom`<br>`tests/test_api_workflow.py::test_student_cannot_create_instructor_task`<br>`tests/test_activity_release_candidate.py::test_non_owner_cannot_update_or_publish_task`<br>`tests/test_activity_release_candidate.py::test_non_owner_cannot_unpublish_task` | Verified |
| ACT-003 | Hidden test-case content is never student-visible. | line 25 | `tests/test_task_workflow.py::test_student_sample_test_cases_exclude_hidden_cases`<br>`tests/test_task_openapi_contracts.py::test_student_sample_response_excludes_hidden_case_metadata`<br>`tests/test_task_openapi_contracts.py::test_student_activity_endpoints_use_student_safe_schemas` | Verified |
| ACT-004 | Public sample tests remain distinct from hidden tests. | activity and execution contracts | `tests/test_task_workflow.py::test_instructor_can_manage_public_and_hidden_test_cases`<br>`tests/test_task_workflow.py::test_student_sample_test_cases_exclude_hidden_cases` | Verified |
| ACT-005 | Unpublished or unauthorized activity data is not exposed to students. | student authorization rule | `tests/test_task_workflow.py::test_student_sees_only_published_tasks_from_active_enrollment`<br>`tests/test_task_workflow.py::test_disabled_and_removed_enrollment_blocks_task_access`<br>`tests/test_task_workflow.py::test_inactive_classroom_blocks_student_task_access`<br>`tests/test_execution_workflow.py::test_execution_requires_published_task_and_active_enrollment` | Verified |

## Paste Policy

| Requirement ID | Canonical requirement | Source | Exact verification evidence | Current status |
|---|---|---:|---|---|
| PST-001 | Paste policy accepts only `internal_only` or `disabled`. | line 26 | `tests/test_task_workflow.py::test_instructor_can_create_update_filter_and_publish_tasks`<br>`tests/test_paste_policy_release_candidate.py::test_unsupported_paste_policy_is_rejected_during_task_creation`<br>`tests/test_paste_policy_release_candidate.py::test_unsupported_paste_policy_is_rejected_during_task_update` | Verified |
| PST-002 | Blocked-paste telemetry stores count and approved timestamp only. | privacy rules | `tests/test_coding_session_workflow.py::test_session_activity_uses_aggregate_increments_only`<br>`tests/test_session_privacy_contracts.py::test_coding_session_database_has_only_approved_fields`<br>`tests/test_session_privacy_contracts.py::test_behavioral_log_database_has_only_approved_fields`<br>`tests/test_session_privacy_contracts.py::test_activity_update_accepts_only_aggregate_increments`<br>`tests/test_session_privacy_contracts.py::test_session_response_models_are_review_only`<br>`tests/test_session_privacy_contracts.py::test_openapi_session_requests_exclude_private_fields`<br>`tests/test_session_privacy_contracts.py::test_openapi_session_responses_exclude_surveillance_fields` | Verified |
| PST-003 | Clipboard or pasted text content is never persisted. | privacy rules | `tests/test_coding_session_workflow.py::test_session_activity_uses_aggregate_increments_only`<br>`tests/test_coding_session_workflow.py::test_instructor_can_review_only_owned_coding_sessions`<br>`tests/test_session_privacy_contracts.py::test_coding_session_database_has_only_approved_fields`<br>`tests/test_session_privacy_contracts.py::test_behavioral_log_database_has_only_approved_fields`<br>`tests/test_session_privacy_contracts.py::test_activity_update_accepts_only_aggregate_increments`<br>`tests/test_session_privacy_contracts.py::test_session_response_models_are_review_only`<br>`tests/test_session_privacy_contracts.py::test_openapi_session_requests_exclude_private_fields`<br>`tests/test_session_privacy_contracts.py::test_openapi_session_responses_exclude_surveillance_fields` | Verified |

## Submission Workflow

| Requirement ID | Canonical requirement | Source | Primary verification files | Current status |
|---|---|---:|---|---|
| SUB-001 | Submission attempts are immutable. | line 27 | `test_submission_workflow.py`, `test_submission_openapi_contracts.py` | Mapped |
| SUB-002 | Attempt numbering is controlled by the backend. | line 28 | `test_submission_workflow.py`, `test_submission_concurrency.py` | Mapped |
| SUB-003 | Official-attempt state is controlled by the backend. | line 28 | `test_submission_workflow.py`, `test_submission_concurrency.py` | Mapped |
| SUB-004 | Only the latest accepted attempt may be official. | line 29 | `test_submission_workflow.py`, `test_submission_concurrency.py` | Mapped |
| SUB-005 | Concurrent submissions cannot receive the same attempt number. | transaction safety rule | `test_submission_concurrency.py` | Mapped |
| SUB-006 | Students may create and access only their own submission attempts. | line 35 | `test_submission_workflow.py`, `test_submission_openapi_contracts.py` | Mapped |
| SUB-007 | Instructor submission access is limited to owned classroom activities. | authorization rule | `test_submission_workflow.py`, `test_review_queue_workflow.py` | Mapped |

## Execution Workflow

| Requirement ID | Canonical requirement | Source | Primary verification files | Current status |
|---|---|---:|---|---|
| EXE-001 | Student Python code never executes inside React. | line 30 | architectural inspection, frontend handoff, partner contract tests | Mapped |
| EXE-002 | Student Python code never executes inside FastAPI. | line 30 | `test_execution_workflow.py`, `test_execution_service.py`, `test_execution_openapi_contracts.py` | Mapped |
| EXE-003 | Actual code execution occurs only in the partner-owned isolated worker. | line 31 | `test_execution_workflow.py`, `test_partner_execution_router.py`, `test_execution_openapi_contracts.py` | Mapped |
| EXE-004 | Execution-request lifecycle state is backend-controlled. | execution contract | `test_execution_service.py`, `test_execution_workflow.py` | Mapped |
| EXE-005 | Partner result updates require authenticated trusted integration. | partner boundary | `test_partner_auth.py`, `test_partner_execution_router.py` | Mapped |
| EXE-006 | Partner lifecycle transitions follow the approved transition map. | partner contract | `test_execution_service.py`, `test_partner_execution_models.py` | Mapped |
| EXE-007 | Partner updates use strict sequence ordering. | partner contract | `test_execution_service.py`, `test_partner_execution_router.py` | Mapped |
| EXE-008 | Identical partner retries are replay-safe. | partner contract | `test_execution_service.py`, `test_partner_execution_concurrency.py` | Mapped |
| EXE-009 | Conflicting partner retries are rejected. | partner contract | `test_execution_service.py`, `test_partner_execution_router.py` | Mapped |
| EXE-010 | Student execution requests support student-scoped idempotency. | Pillar 15 contract | `test_execution_request_idempotency.py`, `test_execution_request_idempotency_concurrency.py` | Mapped |
| EXE-011 | Concurrent identical student retries create one execution request and one run-counter increment. | Pillar 15 contract | `test_execution_request_idempotency_concurrency.py` | Mapped |
| EXE-012 | Student-safe execution responses exclude partner-only and internal idempotency metadata. | privacy and API contract | `test_execution_request_idempotency.py`, `test_execution_openapi_contracts.py` | Mapped |

## Evaluation and Review Indicators

| Requirement ID | Canonical requirement | Source | Primary verification files | Current status |
|---|---|---:|---|---|
| EVA-001 | AST indicators are review-only. | line 32 | `test_ast_evaluator.py`, `test_evaluation_workflow.py`, `test_evaluation_privacy_contracts.py` | Mapped |
| EVA-002 | Similarity indicators are review-only. | line 32 | `test_jaccard.py`, `test_evaluation_workflow.py`, `test_evaluation_privacy_contracts.py` | Mapped |
| EVA-003 | Execution indicators are review-only. | line 32 | `test_execution_workflow.py`, `test_evaluation_workflow.py` | Mapped |
| EVA-004 | Coding-session indicators are review-only. | line 32 | `test_coding_session_workflow.py`, `test_session_privacy_contracts.py` | Mapped |
| EVA-005 | Automated indicators never assign grades. | line 33 | `test_evaluation_privacy_contracts.py`, `test_pillar10_privacy_contracts.py`, `test_gradebook_workflow.py` | Mapped |
| EVA-006 | Automated indicators never declare plagiarism. | line 33 | `test_evaluation_privacy_contracts.py`, `test_pillar10_privacy_contracts.py` | Mapped |
| EVA-007 | Automated indicators never declare copying, cheating, misconduct, or academic dishonesty. | line 33 | `test_evaluation_privacy_contracts.py`, `test_pillar10_privacy_contracts.py` | Mapped |
| EVA-008 | Automated indicators never produce an official risk score. | line 33 | `test_evaluation_privacy_contracts.py`, `test_reporting_service.py` | Mapped |
| EVA-009 | Full AST details are instructor-only. | line 34 | `test_evaluation_workflow.py`, `test_evaluation_privacy_contracts.py`, `test_review_queue_workflow.py` | Mapped |
| EVA-010 | Full similarity details are instructor-only. | line 34 | `test_evaluation_workflow.py`, `test_evaluation_privacy_contracts.py`, `test_review_queue_workflow.py` | Mapped |
| EVA-011 | Local LLM assistance cannot assign grades or determine misconduct. | permanent boundary | `test_local_llm.py`, `test_evaluation_privacy_contracts.py` | Mapped |

## Student Data Authorization

| Requirement ID | Canonical requirement | Source | Primary verification files | Current status |
|---|---|---:|---|---|
| DAT-001 | Students see only their own permitted data. | line 35 | workflow and router tests across all student-facing domains | Mapped |
| DAT-002 | Students cannot access another student's submissions. | line 35 | `test_submission_workflow.py` | Mapped |
| DAT-003 | Students cannot access another student's coding sessions. | line 35 | `test_coding_session_workflow.py` | Mapped |
| DAT-004 | Students cannot access another student's execution requests. | line 35 | `test_execution_workflow.py` | Mapped |
| DAT-005 | Students cannot access another student's notifications. | line 35 | `test_notification_workflow.py` | Mapped |
| DAT-006 | Students cannot access another user's audit records. | line 35 | `test_audit_router.py`, `test_audit_workflow.py` | Mapped |
| DAT-007 | Students see only their own released manual grades. | lines 35 and 37 | `test_evaluation_workflow.py`, `test_gradebook_workflow.py`, `test_pillar10_privacy_contracts.py` | Mapped |
| DAT-008 | Student progress reports remain scoped to the authenticated student. | line 35 | `test_reporting_router.py`, `test_reporting_service.py` | Mapped |

## Manual Grading

| Requirement ID | Canonical requirement | Source | Primary verification files | Current status |
|---|---|---:|---|---|
| GRD-001 | Only the activity owner may assign a manual grade. | line 36 | `test_evaluation_workflow.py`, `test_gradebook_workflow.py` | Mapped |
| GRD-002 | Unreleased grades are hidden from students. | line 37 | `test_evaluation_workflow.py`, `test_pillar10_privacy_contracts.py` | Mapped |
| GRD-003 | An official grade applies only to the latest accepted official submission. | line 38 | `test_evaluation_workflow.py`, `test_gradebook_workflow.py` | Mapped |
| GRD-004 | Grade changes do not silently change submission review status. | line 39 | `test_evaluation_workflow.py` | Mapped |
| GRD-005 | Marking an evaluation as `graded` requires an existing manual grade. | line 40 | `test_evaluation_workflow.py` | Mapped |
| GRD-006 | Concurrent grade writes remain transactionally consistent. | transaction rule | `test_grade_concurrency.py` | Mapped |
| GRD-007 | Gradebook summaries exclude source code and sensitive analytics. | privacy boundary | `test_gradebook_workflow.py`, `test_pillar10_privacy_contracts.py` | Mapped |

---

# B. Privacy Requirements

## Approved Aggregate Session Data

| Requirement ID | Canonical requirement | Source | Primary verification files | Current status |
|---|---|---:|---|---|
| PRV-001 | Tab-switch count may be stored as aggregate session telemetry. | line 44 | `test_coding_session_workflow.py`, `test_session_privacy_contracts.py` | Mapped |
| PRV-002 | Blocked-paste count may be stored as aggregate session telemetry. | line 45 | `test_coding_session_workflow.py`, `test_session_privacy_contracts.py` | Mapped |
| PRV-003 | Run-attempt count may be stored as aggregate session telemetry. | line 46 | `test_coding_session_workflow.py`, `test_execution_workflow.py`, `test_session_privacy_contracts.py` | Mapped |
| PRV-004 | Idle-duration total may be stored as aggregate session telemetry. | line 47 | `test_coding_session_workflow.py`, `test_session_privacy_contracts.py` | Mapped |
| PRV-005 | Only approved timestamps may be stored with session telemetry. | line 48 | `test_coding_session_workflow.py`, `test_session_privacy_contracts.py` | Mapped |

## Prohibited Collection and Exposure

| Requirement ID | Canonical requirement | Source | Primary verification files | Current status |
|---|---|---:|---|---|
| PRV-006 | Clipboard contents are never collected or stored. | line 51 | `test_session_privacy_contracts.py`, `test_evaluation_privacy_contracts.py` | Mapped |
| PRV-007 | Pasted external text is never collected or stored. | line 52 | `test_session_privacy_contracts.py`, `test_evaluation_privacy_contracts.py` | Mapped |
| PRV-008 | Browsing history is never collected. | line 53 | `test_session_privacy_contracts.py`, OpenAPI privacy checks | Mapped |
| PRV-009 | Screen recording is prohibited. | line 54 | `test_session_privacy_contracts.py`, OpenAPI privacy checks | Mapped |
| PRV-010 | Webcam collection is prohibited. | line 55 | `test_session_privacy_contracts.py`, OpenAPI privacy checks | Mapped |
| PRV-011 | Microphone collection is prohibited. | line 56 | `test_session_privacy_contracts.py`, OpenAPI privacy checks | Mapped |
| PRV-012 | Individual keystroke collection is prohibited. | line 57 | `test_session_privacy_contracts.py`, OpenAPI privacy checks | Mapped |
| PRV-013 | Request logs exclude request and response bodies. | Pillar 15 privacy contract | `test_request_context.py` | Mapped |
| PRV-014 | Request logs exclude query strings and sensitive headers. | Pillar 15 privacy contract | `test_request_context.py` | Mapped |
| PRV-015 | Request logs exclude raw exception messages and tracebacks. | Pillar 15 privacy contract | `test_request_context.py` | Mapped |
| PRV-016 | Health, readiness, startup errors, and OpenAPI exclude secret values. | security privacy contract | `test_system_health.py`, `test_application_security_config.py`, `test_openapi_contracts.py` | Mapped |
| PRV-017 | Reporting and CSV exports exclude raw source code and sensitive review analytics. | reporting privacy contract | `test_reporting_service.py`, `test_reporting_router.py`, `test_reporting_schemas.py` | Mapped |

---

# C. Architecture and Transaction Requirements

| Requirement ID | Canonical requirement | Source | Primary verification files or evidence | Current status |
|---|---|---:|---|---|
| ARC-001 | Services use domain or service exceptions. | line 60 | service tests and source inspection | Mapped |
| ARC-002 | Routers translate service exceptions into HTTP responses. | line 61 | router and workflow tests across domains | Mapped |
| ARC-003 | Database writes use guarded commit and rollback. | line 62 | service failure tests, concurrency tests, migration tests | Mapped |
| ARC-004 | Authorization is enforced in backend logic. | line 63 | workflow, router, and service negative tests | Mapped |
| ARC-005 | Frontend hiding is never treated as authorization. | line 64 | backend ownership tests and frontend handoff review | Mapped |
| ARC-006 | High-use listing workflows avoid N+1 query patterns. | line 65 | query review evidence and service tests | Mapped |
| ARC-007 | New roles, statuses, fields, endpoints, or architectural changes require roadmap and current-code review. | line 66 | roadmap review and release procedure | Not Automated |
| ARC-008 | Pagination is bounded and deterministically ordered. | Pillar 15 contract | `test_pagination.py`, listing workflow tests | Mapped |
| ARC-009 | Concurrent official-attempt allocation uses transaction-safe locking. | transaction rule | `test_submission_concurrency.py` | Mapped |
| ARC-010 | Concurrent manual grading uses transaction-safe locking. | transaction rule | `test_grade_concurrency.py` | Mapped |
| ARC-011 | Concurrent partner updates remain replay-safe. | transaction rule | `test_partner_execution_concurrency.py` | Mapped |
| ARC-012 | Concurrent student execution retries remain idempotent. | transaction rule | `test_execution_request_idempotency_concurrency.py` | Mapped |

---

# D. Notification, Audit, and Reporting Verification Domains

## Notifications

| Requirement ID | Release-candidate requirement | Primary verification files | Current status |
|---|---|---|---|
| NTF-001 | Notifications are created only by approved backend workflows. | `test_notification_workflow.py`, related classroom and grading workflows | Mapped |
| NTF-002 | Recipients may read only their own notifications. | `test_notification_workflow.py` | Mapped |
| NTF-003 | Unread-count and read-state operations are recipient-scoped. | `test_notification_workflow.py` | Mapped |
| NTF-004 | Notification payloads remain privacy-safe. | `test_notification_models.py`, `test_notification_workflow.py` | Mapped |
| NTF-005 | Notification listing uses bounded deterministic pagination. | `test_notification_workflow.py`, `test_pagination.py` | Mapped |

## Audit Trail

| Requirement ID | Release-candidate requirement | Primary verification files | Current status |
|---|---|---|---|
| AUD-001 | Audit records are created only by trusted backend workflows. | `test_audit_service.py`, `test_audit_workflow.py` | Mapped |
| AUD-002 | Audit records are immutable accountability records. | `test_audit_models.py`, `test_audit_service.py` | Mapped |
| AUD-003 | Users may access only audit records attributed to their account. | `test_audit_router.py`, `test_audit_workflow.py` | Mapped |
| AUD-004 | Audit payloads exclude source code, credentials, hidden tests, grades not approved for exposure, and surveillance data. | `test_audit_schemas.py`, `test_audit_workflow.py` | Mapped |
| AUD-005 | Audit listing uses bounded deterministic pagination. | `test_audit_router.py`, `test_pagination.py` | Mapped |

## Reporting and Exports

| Requirement ID | Release-candidate requirement | Primary verification files | Current status |
|---|---|---|---|
| RPT-001 | Classroom and activity reports are limited to the owning instructor. | `test_reporting_router.py`, `test_reporting_service.py` | Mapped |
| RPT-002 | Student progress is limited to the authenticated student. | `test_reporting_router.py`, `test_reporting_service.py` | Mapped |
| RPT-003 | Missing-submission reports preserve classroom ownership. | `test_reporting_router.py`, `test_reporting_service.py` | Mapped |
| RPT-004 | Grade distributions use approved manual-grade data only. | `test_reporting_service.py`, `test_reporting_schemas.py` | Mapped |
| RPT-005 | Reports do not create automated misconduct or risk rankings. | `test_reporting_service.py`, `test_reporting_schemas.py` | Mapped |
| RPT-006 | Gradebook CSV exports exclude raw source code and sensitive analytics. | `test_reporting_router.py`, `test_reporting_service.py` | Mapped |
| RPT-007 | Reporting lists use bounded deterministic pagination and ordering where applicable. | `test_reporting_service.py`, `test_pagination.py` | Mapped |

---

# E. Migration and Database Verification

| Requirement ID | Release-candidate requirement | Primary verification files or evidence | Current status |
|---|---|---|---|
| MIG-001 | Alembic has one valid migration head. | `test_alembic_migrations.py`, `alembic heads` | Mapped |
| MIG-002 | A clean database upgrades from the baseline to the current head. | `test_alembic_migrations.py` | Mapped |
| MIG-003 | Migration downgrade and upgrade smoke checks preserve migration-chain validity. | `test_alembic_migrations.py` | Mapped |
| MIG-004 | SQLAlchemy metadata and Alembic migrations have no detected drift. | `alembic check` | Not Automated |
| MIG-005 | Legacy Pillar 14 schema upgrade remains idempotent and privacy-safe. | `test_p14_schema_upgrade.py` | Mapped |
| MIG-006 | Pillar 15 legacy-schema alignment is explicit and does not run during application import. | source inspection and migration procedure | Mapped |
| MIG-007 | Migration operations do not expose database credentials. | migration tests and release procedure | Mapped |
| MIG-008 | Current migration head is `9f2c6e4a1b7d`. | `test_alembic_migrations.py`, `alembic heads` | Mapped |

---

# F. Runtime and API Security Verification

| Requirement ID | Release-candidate requirement | Primary verification files | Current status |
|---|---|---|---|
| SEC-001 | Required database configuration fails fast when missing. | `test_config.py` | Mapped |
| SEC-002 | JWT secret length and algorithm are validated. | `test_config.py`, `test_security.py` | Mapped |
| SEC-003 | JWT expiration configuration is positive and bounded. | `test_config.py`, `test_security.py` | Mapped |
| SEC-004 | Partner authentication rejects missing or invalid request tokens. | `test_partner_auth.py`, `test_partner_execution_router.py` | Mapped |
| SEC-005 | Missing or short configured partner token returns service unavailable at the integration boundary. | `test_partner_auth.py`, `test_system_health.py` | Mapped |
| SEC-006 | CORS permits only explicitly configured origins. | `test_application_security_config.py`, `test_config.py` | Mapped |
| SEC-007 | Wildcard CORS origins are rejected. | `test_application_security_config.py`, `test_config.py` | Mapped |
| SEC-008 | Production CORS origins require HTTPS. | `test_config.py` | Mapped |
| SEC-009 | Trusted-host enforcement rejects unapproved hosts when configured. | `test_application_security_config.py` | Mapped |
| SEC-010 | Production wildcard trusted hosts are rejected. | `test_application_security_config.py`, `test_config.py` | Mapped |
| SEC-011 | Production API documentation defaults to disabled. | `test_application_security_config.py`, `test_config.py` | Mapped |
| SEC-012 | Correlation IDs are UUIDs and malformed client values are replaced. | `test_request_context.py` | Mapped |
| SEC-013 | The response correlation ID matches request-local structured logging context. | `test_request_context.py`, system smoke verification | Mapped |
| SEC-014 | Configuration representations do not disclose secret values. | `test_config.py` | Mapped |
| SEC-015 | Security and startup errors do not expose secret values. | `test_application_security_config.py`, `test_system_health.py` | Mapped |

---

# G. OpenAPI and Contract Freeze Verification

| Requirement ID | Release-candidate requirement | Primary verification files | Current status |
|---|---|---|---|
| API-001 | OpenAPI reports the release-candidate version. | `test_openapi_contracts.py`, `test_classroom_openapi_contracts.py`, domain OpenAPI tests | Gap pending `1.0.0-rc1` version bump |
| API-002 | All approved backend routes remain documented. | `test_openapi_contracts.py`, domain OpenAPI tests | Mapped |
| API-003 | Authentication schemes remain documented correctly. | `test_openapi_contracts.py`, `test_execution_openapi_contracts.py` | Mapped |
| API-004 | Secret configuration values are absent from OpenAPI. | `test_openapi_contracts.py`, `test_system_health.py` | Mapped |
| API-005 | Hidden tests and instructor-only analytics are absent from student-facing response contracts. | domain OpenAPI and privacy-contract tests | Mapped |
| API-006 | No unapproved role, status, endpoint, or response field is introduced during release-candidate verification. | complete OpenAPI snapshot audit | Gap pending contract freeze |
| API-007 | Final release-candidate OpenAPI is frozen after all approved fixes. | generated OpenAPI artifact and checksum | Gap pending freeze procedure |

---

# H. Testing and Git Requirements

| Requirement ID | Canonical requirement | Source | Verification method | Current status |
|---|---|---:|---|---|
| TST-001 | Canonical schema tests use `backend/tests/test_schemas.py`. | line 69 | repository inspection and pytest collection | Not Automated |
| TST-002 | `backend/tests/test_schema.py` must not exist or be used. | line 70 | repository file check | Not Automated |
| TST-003 | Focused tests must pass before broader regression. | line 74 | Pillar workflow evidence | Not Automated |
| TST-004 | Complete backend regression must pass before release-candidate completion. | Pillar completion gate | complete `pytest -q` | Mapped |
| TST-005 | All approved requirements must map to passing tests. | Pillar 16 definition of done | this traceability matrix | Partially Verified |
| TST-006 | Zero unresolved high-severity defects may remain. | Pillar 16 definition of done | defect register and release checklist | Gap |
| GIT-001 | Feature, review, and fix branches remain local. | line 71 | `git branch -vv` and remote branch check | Not Automated |
| GIT-002 | Review work merges locally into `dev`. | line 72 | Git history inspection | Not Automated |
| GIT-003 | Only `dev` is pushed. | line 73 | remote branch verification | Not Automated |
| GIT-004 | Commits are not created while focused or full regression tests fail. | line 74 | workflow evidence | Not Automated |
| GIT-005 | Pillar 16 review branch is `review/backend-p16-release-candidate`. | roadmap | `git branch --show-current` | Not Automated |
| GIT-006 | Release-candidate work must be merged and retested on `dev` before pushing. | completion gate | final release procedure | Not Automated |

---

# I. End-to-End Acceptance Scenario Inventory

The following acceptance scenarios are required by the Pillar 16 roadmap.

Exact consolidated end-to-end pytest-node mappings are still pending.

| Scenario ID | Acceptance scenario | Existing candidate coverage | Current status |
|---|---|---|---|
| E2E-001 | Register a permitted university user, complete OTP verification, and authenticate. | `test_api_workflow.py`, `test_otp_service.py`, `test_registration_otp_release_candidate.py`, `test_security.py` | Mapped |
| E2E-002 | Reject registration with a non-university email, invalid school ID, duplicate email, duplicate school ID, or client-assigned role. | `test_schemas.py`, `test_openapi_contracts.py`, `test_registration_otp_release_candidate.py` | Mapped |
| E2E-003 | Instructor creates a classroom and backend-generated class code; student enrolls through the approved flow. | `test_classroom_workflow.py`, `test_classroom_release_candidate.py` | Mapped |
| E2E-004 | Instructor creates a laboratory or homework activity with public and hidden test cases. | `test_task_workflow.py`, `test_activity_release_candidate.py`, `test_paste_policy_release_candidate.py` | Mapped |
| E2E-005 | Student sees the published activity without hidden test content. | `test_task_workflow.py`, `test_task_openapi_contracts.py` | Mapped |
| E2E-006 | Student opens a coding session and submits only approved aggregate telemetry. | `test_coding_session_workflow.py`, `test_session_privacy_contracts.py`, `test_paste_policy_release_candidate.py` | Mapped |
| E2E-007 | Student creates immutable submission attempts and the latest accepted attempt becomes official. | `test_submission_workflow.py`, `test_submission_concurrency.py` | Mapped |
| E2E-008 | Student requests execution and FastAPI queues the request without executing Python. | `test_execution_workflow.py`, `test_execution_service.py` | Mapped |
| E2E-009 | Trusted partner reports ordered execution lifecycle updates with replay-safe behavior. | `test_partner_execution_router.py`, `test_partner_execution_concurrency.py` | Mapped |
| E2E-010 | Instructor reviews execution, AST, similarity, and session indicators without automatic misconduct conclusions. | `test_review_queue_workflow.py`, `test_evaluation_privacy_contracts.py` | Mapped |
| E2E-011 | Activity owner assigns and releases a manual grade for the latest accepted official submission. | `test_evaluation_workflow.py`, `test_gradebook_workflow.py`, `test_grade_concurrency.py` | Mapped |
| E2E-012 | Student sees only the student's own released grade. | `test_evaluation_workflow.py`, `test_pillar10_privacy_contracts.py` | Mapped |
| E2E-013 | Approved classroom, submission, and grading events create privacy-safe notifications. | `test_notification_workflow.py` and related workflow tests | Mapped |
| E2E-014 | Approved academic changes create immutable privacy-safe audit records. | `test_audit_workflow.py` and related workflow tests | Mapped |
| E2E-015 | Instructor retrieves ownership-safe reports and gradebook CSV without source code. | `test_reporting_router.py`, `test_reporting_service.py` | Mapped |
| E2E-016 | Student retrieves only the student's own progress report. | `test_reporting_router.py`, `test_reporting_service.py` | Mapped |
| E2E-017 | Invalid authorization attempts across all domains return controlled HTTP errors without data leakage. | domain workflow and router negative tests | Mapped |
| E2E-018 | Application starts with valid production settings, restrictive CORS and trusted hosts, disabled docs, and privacy-safe request logging. | `test_application_security_config.py`, `test_request_context.py` | Mapped |
| E2E-019 | Clean PostgreSQL schema migrates to the current head without drift. | `test_alembic_migrations.py`, migration commands | Mapped |
| E2E-020 | Frozen release-candidate OpenAPI matches the approved backend contract. | OpenAPI tests and planned freeze artifact | Gap |

---

# J. Known Pillar 16 Verification Gaps

The following work remains before the release candidate can be declared complete:

| Gap ID | Required work | Related requirements |
|---|---|---|
| GAP-001 | Continue extracting exact pytest node IDs for all remaining mapped requirements. Registration, OTP, classroom, activity, and paste-policy mapping are complete. | all remaining `Mapped` rows |
| GAP-002 | Identify remaining requirements that rely only on broad workflow files and add focused negative tests where needed. | authorization and privacy rows |
| GAP-003 | Create consolidated end-to-end backend acceptance scenarios. | E2E-001 through E2E-020 |
| GAP-004 | Bump backend and OpenAPI version to `1.0.0-rc1`. | API-001 |
| GAP-005 | Generate and freeze the approved OpenAPI release-candidate contract. | API-006, API-007, E2E-020 |
| GAP-006 | Verify the migration chain against a clean PostgreSQL database. | MIG-001 through MIG-008 |
| GAP-007 | Create a high-severity defect register and confirm zero unresolved high-severity defects. | TST-006 |
| GAP-008 | Create the frontend handoff package. | Pillar 16 roadmap |
| GAP-009 | Create the isolated-worker partner handoff package. | Pillar 16 roadmap |
| GAP-010 | Create the changelog and release notes. | Pillar 16 roadmap |
| GAP-011 | Run the final complete regression on the review branch and again after local merge into `dev`. | TST-004, GIT-006 |

---

# K. Pillar 16 Completion Evidence

This section must be updated only with observed results.

## Current Branch

```text
review/backend-p16-release-candidate
```

## Current Release-Candidate Version

```text
Not yet bumped
Target: 1.0.0-rc1
```

## Latest Inherited Baseline

```text
699 passed in 120.49s (0:02:00)
```

This result was verified on `dev` after Pillar 15 was merged.

It must not be represented as the final Pillar 16 review-branch regression.

## Current Test-Node Inventory

```text
713 collected pytest nodes
```

Inventory file:

```text
docs/ai/P16_TEST_NODE_INVENTORY.txt
```

## Registration and OTP Focused Verification

```text
7 passed in 2.89s
```

Exact release-candidate test nodes:

```text
tests/test_registration_otp_release_candidate.py::test_school_id_persists_as_string
tests/test_registration_otp_release_candidate.py::test_existing_email_blocks_registration
tests/test_registration_otp_release_candidate.py::test_existing_school_id_blocks_registration
tests/test_registration_otp_release_candidate.py::test_expired_otp_is_rejected
tests/test_registration_otp_release_candidate.py::test_maximum_otp_attempts_are_enforced
tests/test_registration_otp_release_candidate.py::test_resend_cooldown_is_enforced
tests/test_registration_otp_release_candidate.py::test_maximum_otp_resends_are_enforced
```

## Registration and OTP Related Regression

```text
114 passed in 13.51s
```

Files included:

```text
tests/test_registration_otp_release_candidate.py
tests/test_otp_service.py
tests/test_schemas.py
tests/test_openapi_contracts.py
tests/test_api_workflow.py
```

## Classroom Focused Verification

```text
2 passed in 3.38s
```

Exact release-candidate test nodes:

```text
tests/test_classroom_release_candidate.py::test_non_owner_cannot_archive_classroom
tests/test_classroom_release_candidate.py::test_non_owner_cannot_change_enrollment_status
```

## Classroom Related Regression

```text
51 passed in 12.79s
```

Files included:

```text
tests/test_classroom_release_candidate.py
tests/test_classroom_workflow.py
tests/test_classroom_openapi_contracts.py
tests/test_notification_workflow.py
tests/test_audit_workflow.py
```

## Activity Focused Verification

```text
3 passed in 3.10s
```

Exact release-candidate test nodes:

```text
tests/test_activity_release_candidate.py::test_unsupported_activity_type_is_rejected
tests/test_activity_release_candidate.py::test_non_owner_cannot_update_or_publish_task
tests/test_activity_release_candidate.py::test_non_owner_cannot_unpublish_task
```

## Activity Related Regression

```text
94 passed in 30.82s
```

Files included:

```text
tests/test_activity_release_candidate.py
tests/test_task_workflow.py
tests/test_task_openapi_contracts.py
tests/test_schemas.py
tests/test_api_workflow.py
tests/test_execution_workflow.py
```

## Paste-Policy Focused Verification

```text
2 passed in 3.75s
```

Exact release-candidate test nodes:

```text
tests/test_paste_policy_release_candidate.py::test_unsupported_paste_policy_is_rejected_during_task_creation
tests/test_paste_policy_release_candidate.py::test_unsupported_paste_policy_is_rejected_during_task_update
```

## Paste-Policy and Privacy Related Regression

```text
88 passed in 20.83s
```

Files included:

```text
tests/test_paste_policy_release_candidate.py
tests/test_task_workflow.py
tests/test_coding_session_workflow.py
tests/test_session_privacy_contracts.py
tests/test_evaluation_privacy_contracts.py
tests/test_schemas.py
```

## Current Review-Branch Regression

```text
713 passed in 124.30s (0:02:04)
```

This is the current Pillar 16 regression after Registration, OTP, classroom, activity, and paste-policy verification additions.

It is not yet the final release-candidate review-branch regression because the remaining Pillar 16 work is still pending.

## Exact Test-Node Mapping

```text
Completed:
REG-001 through REG-007
OTP-001 through OTP-007
CLS-001 through CLS-005
ACT-001 through ACT-005
PST-001 through PST-003

Pending:
All remaining mapped Pillar 16 requirements
```

## Privacy and Security Negative Verification

```text
Registration and OTP privacy verification passed as part of:
114 passed in 13.51s

Classroom ownership and authorization verification passed as part of:
51 passed in 12.79s

Activity authorization and hidden-test privacy verification passed as part of:
94 passed in 30.82s

Paste-policy and coding-session privacy verification passed as part of:
88 passed in 20.83s

Consolidated Pillar 16 privacy and security negative verification:
Pending
```

## Migration Verification

```text
Pending Pillar 16 clean-database verification
```

## OpenAPI Contract Freeze

```text
Pending
```

## High-Severity Defects

```text
Pending defect-register creation and review
```

## Final Review-Branch Regression

```text
Pending
```

## Post-Merge `dev` Regression

```text
Pending
```

---

# L. Required Next Action

The next action is to extract exact pytest node IDs for:

```text
SUB-001 through SUB-007
```

The submission audit must determine whether the existing tests provide sufficient verification for:

1. immutable submission attempts;
2. backend-controlled attempt numbering;
3. backend-controlled official-attempt state;
4. latest accepted attempt becoming the only official attempt;
5. concurrency-safe attempt-number allocation;
6. student ownership of submission creation and access;
7. instructor access limited to submissions under owned classroom activities.

Do not change application behavior during the exact-node audit.

Add focused release-candidate tests only when a real verification gap is confirmed.

Do not bump the version until:

1. the remaining requirement-to-test coverage is audited;
2. identified verification gaps are recorded;
3. required release-candidate test additions are completed;
4. the existing full regression remains green;
5. release-candidate contracts are ready to freeze.

Do not push:

```text
review/backend-p16-release-candidate
```
