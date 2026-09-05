# PAMSU IDE Backend Architecture and Verified File Inventory

This is an architectural inventory rather than a byte-for-byte repository listing. Package initialization files, caches, local secrets, virtual environments, generated artifacts, and grouped test filenames may be omitted for readability.

This document describes the files currently present in the Backend 1.0.0 repository and their verified architectural roles. The presence of a file does not necessarily mean that an external provider or runtime integration is operational. Celery, Redis, Judge0, the isolated sandbox worker, production email delivery, and a local LLM runtime are not part of the verified Backend 1.0.0 implementation.

This inventory lists files that exist in the repository. Some integration files define contracts or inactive boundaries only and do not represent completed external runtime implementations.

## Root Configuration
* `backend\.env.example` - Template for required environment variables. Actual .env is local and must not be shared or committed.
* `backend\alembic.ini` - Database migration configuration settings.
* `backend\main.py` - Secondary application entry-point file. The verified FastAPI application entry point is `backend\app\main.py`.
* `backend\requirements.txt` - Python package dependencies.

## Alembic Migrations (`backend\alembic\`)
* `env.py` - Alembic environment execution script.
* `README` - Alembic instructions.
* `script.py.mako` - Template for generating new migration scripts.
* `versions\18d3ef8f020d_baseline_schema.py` - Baseline database schema migration.
* `versions\4b3a1d9e7c25_add_execution_request_idempotency.py` - Schema migration for execution idempotency.
* `versions\9f2c6e4a1b7d_optimize_proven_index_coverage.py` - Schema migration for index optimization.

## Core Application (`backend\app\`)
* `main.py` - Verified FastAPI application initialization and router inclusion.

### Core Utilities (`backend\app\core\`)
* `config.py` - Application settings and environment parsing.
* `database.py` - Verified runtime database configuration, core connection engine, and session logic.
* `pagination.py` - Pagination utilities for API endpoints.
* `request_context.py` - Context variables for request tracing and logging.
* `security.py` - JWT authentication, password hashing, and role-based dependency enforcement. CORS configuration is validated through config.py and installed in app/main.py.

### Database Operations (`backend\app\db\`)
* `database.py` - Database helper module. The verified runtime database configuration is located in `app\core\database.py`.
* `upgrade_p14_partner_execution.py` - Schema logic for partner execution integrations.
* `upgrade_p15_legacy_schema.py` - Schema logic for legacy data support.

### Integrations (`backend\app\integrations\`)
* `local_llm.py` - Logic interface for eventual local LLM runtime support (currently inactive/contract only).
* `otp_delivery.py` - Interface for managing OTP delivery mechanisms.
* `otp_email.py` - Provider adapter boundary for email-based OTP delivery. A production email provider is not yet connected.
* `partner_auth.py` - Validation logic for external partner sandbox authentication.

### Database Models (`backend\app\models\`)
* `activity_log.py` - ORM model for telemetry and activity logs.
* `domain_models.py` - Main ORM definitions (Submissions, Classrooms, Tasks, etc.).
* `user.py` - ORM model for user accounts.

### API Routers (`backend\app\routers\`)
* `activities.py` - Endpoints for managing coding tasks.
* `audit_records.py` - Endpoints for retrieving immutable audit trails.
* `auth.py` - Endpoints for login and JWT generation.
* `classrooms.py` - Endpoints for course/classroom management.
* `evaluation.py` - Instructor-authorized static evaluation review, submission status, and manual-grade endpoints. Automated indicators remain review-only.
* `execution.py` - Endpoints for handling execution payloads and partner callbacks.
* `instructor.py` - Specialized endpoints for instructor dashboards and grading.
* `logs.py` - Endpoints for system and behavioral telemetry logs.
* `notifications.py` - Endpoints for academic event notifications.
* `registration.py` - Endpoints for user signup and OTP verification.
* `reporting.py` - Endpoints for performance summaries and CSV exports.
* `submissions.py` - Endpoints for handling student code submissions.

### API Schemas (`backend\app\schemas\`)
Pydantic contracts used for request validation and response serialization.
* `audit_schema.py`
* `classroom_schema.py`
* `coding_session_schema.py`
* `enrollment_schema.py`
* `evaluation_schema.py`
* `execution_schema.py`
* `gradebook_schema.py`
* `log_schema.py`
* `notification_schema.py`
* `otp_schema.py`
* `reporting_schema.py`
* `review_queue_schema.py`
* `submission_schema.py`
* `task_schema.py`
* `task_test_case_schema.py`
* `user_schema.py`

### Business Logic Services (`backend\app\services\`)
* `academic_event_service.py` - Handles generation of academic event triggers.
* `ast_evaluator.py` - Evaluates Python syntax trees for required constructs.
* `audit_service.py` - Manages immutable recording of critical actions.
* `classroom_service.py` - Business logic for classroom/enrollment actions.
* `coding_session_service.py` - Processes privacy-safe telemetry (aggregate blocked-paste counts and approved timestamps only; clipboard contents and pasted text are never stored).
* `evaluation_service.py` - Produces instructor-review AST and similarity indicators and manages authorized manual grading. It does not automatically assign grades or misconduct verdicts.
* `execution_service.py` - Prepares execution requests for partner sandbox processing.
* `gradebook_service.py` - Aggregates scores for instructor gradebooks.
* `jaccard.py` - Calculates normalized code-similarity indicators for instructor review. It does not automatically determine plagiarism or misconduct.
* `notification_service.py` - Manages dispatching of system notifications.
* `otp_service.py` - Generates and validates One-Time Passwords.
* `reporting_service.py` - Compiles analytical reports and CSV datasets.
* `review_queue_service.py` - Manages instructor workflows for manual code review.
* `submission_service.py` - Handles the lifecycle of code submission attempts.
* `task_service.py` - Business logic for creating and updating programming tasks.

### Legacy or Inactive Task Integration
* `backend\app\tasks\celery_worker.py` - Legacy, experimental, or inactive worker file; Celery and Redis are not part of the verified Backend 1.0.0 runtime.

## Backend 1.0.0 Verification Summary

* Final Backend 1.0.0 release commit: `b2e24b1`
* Automated regression result: `731 passed in 126.48 seconds`
* Current Alembic migration head: `9f2c6e4a1b7d`
* Migration drift result: No new upgrade operations detected
* Final OpenAPI checksum: `c962d2ce3924bc2bb3e064941715a4c21803dfffa2256839b6da153679aa0560`
* Deployment status: The internal FastAPI backend is release-verified, but production deployment and external runtime integration remain pending.

## Test Suite (`backend\tests\`)
At the final Backend 1.0.0 verification checkpoint, the complete suite collected and passed 731 pytest test cases.
* `conftest.py` - Pytest configuration and fixtures.
* `test_activity_release_candidate.py`
* `test_alembic_migrations.py`
* `test_api_workflow.py`
* `test_application_security_config.py`
* `test_ast_evaluator.py`
* `test_audit_models.py`, `test_audit_router.py`, `test_audit_schemas.py`, `test_audit_service.py`, `test_audit_workflow.py`
* `test_classroom_openapi_contracts.py`, `test_classroom_release_candidate.py`, `test_classroom_workflow.py`
* `test_coding_session_workflow.py`
* `test_config.py`
* `test_evaluation_privacy_contracts.py`, `test_evaluation_workflow.py`
* `test_execution_openapi_contracts.py`, `test_execution_request_idempotency.py`, `test_execution_request_idempotency_concurrency.py`, `test_execution_service.py`, `test_execution_workflow.py`
* `test_gradebook_workflow.py`, `test_grade_concurrency.py`
* `test_jaccard.py`
* `test_local_llm.py`
* `test_notification_models.py`, `test_notification_workflow.py`
* `test_openapi_contracts.py`
* `test_otp_service.py`
* `test_p14_schema_upgrade.py`
* `test_pagination.py`
* `test_partner_auth.py`, `test_partner_execution_concurrency.py`, `test_partner_execution_models.py`, `test_partner_execution_router.py`
* `test_paste_policy_release_candidate.py`
* `test_pillar10_privacy_contracts.py`
* `test_registration_otp_release_candidate.py`
* `test_reporting_router.py`, `test_reporting_schemas.py`, `test_reporting_service.py`
* `test_request_context.py`
* `test_review_queue_workflow.py`
* `test_schemas.py`
* `test_security.py`
* `test_session_privacy_contracts.py`
* `test_submission_concurrency.py`, `test_submission_openapi_contracts.py`, `test_submission_workflow.py`
* `test_system_health.py`
* `test_task_openapi_contracts.py`, `test_task_workflow.py`
