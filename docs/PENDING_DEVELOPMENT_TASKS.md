# PAMSU IDE: Pending System Development Tasks

This document outlines the remaining technical and engineering tasks required to bring the PAMSU Web-Based Python IDE to 100% operational completion, ready for production deployment.

## 1. Execution Infrastructure (Sandbox & Workers)
*Currently, the system relies on a local `mock_judge0` container. This must be upgraded to a real execution environment.*
- [ ] **Provision Real Sandbox Worker:** Replace `mock_judge0` with a fully operational, isolated Python execution environment (e.g., a production Judge0 instance).
- [ ] **Sandbox-to-Backend Integration:** Ensure the FastAPI execution service correctly routes payloads to the real sandbox and successfully processes the execution callbacks/webhooks.
- [ ] **Production Celery/Redis Configuration:** Validate that the Celery workers and Redis message broker are configured for a production environment to handle high-concurrency code submissions without crashing.

## 2. External API Integrations
*The backend currently defines interfaces for these, but the actual delivery mechanisms need to be hooked up.*
- [ ] **Email Provider for OTP:** Connect a real email delivery service (e.g., standard SMTP, SendGrid, Mailgun) to `app/integrations/otp_email.py` so that user registration emails are actually sent.
- [ ] **Local LLM Runtime (Optional):** If still within the system scope, finalize the implementation of the `local_llm.py` interface.

## 3. Frontend Development & UI Integration
*The React frontend scaffolding and features are in place, but they need to be perfectly wired to the completed FastAPI backend.*
- [ ] **Frontend-to-Backend API Wiring:** Connect all React feature modules (`assignments`, `auth`, `classes`, `dashboard`, `instructor`, `practice`, `submissions`, `workspace`) to their respective FastAPI endpoints.
- [ ] **Finalize Monaco Editor Integration:** Ensure the coding workspace correctly captures user input, sends the execution payload, and clearly displays both runtime errors and automated AST structural feedback to the student.
- [ ] **Finalize Instructor Dashboard:** Ensure the UI correctly parses and renders the JSON data from the backend, specifically visualizing the Jaccard code-similarity indicators and the privacy-safe telemetry logs (tab-switches and blur events).
- [ ] **Resolve Explicit TODOs:** Address any remaining inline developer notes (e.g., the `# TODO: implement the solution` inside `Workspace.jsx`).

## 4. System Testing, QA, and Deployment
- [ ] **End-to-End (E2E) Integration Testing:** Verify the complete data lifecycle: *Authentication -> Code Editing -> Blur Event Telemetry -> Submission -> Celery Queuing -> Sandbox Execution -> AST/Jaccard Analysis -> Instructor Review.*
- [ ] **Concurrency/Load Testing:** Stress test the Celery task queue to ensure the system remains stable when multiple students submit code simultaneously during a timed laboratory exam.
- [ ] **Production Deployment:** Containerize and deploy the database, backend, frontend, and worker infrastructure to a live production server (e.g., AWS, DigitalOcean, or university hosting).
