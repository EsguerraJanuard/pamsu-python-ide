# Master Project Overview: PAMSU Web-Based Python IDE

## 1. System Architecture & Tech Stack

### Frontend Architecture
* **Framework:** React 18 powered by Vite for rapid HMR (Hot Module Replacement) and highly optimized production builds.
* **Styling:** TailwindCSS for utility-first styling, featuring dynamic CSS variables to seamlessly handle Light and Dark mode themes.
* **Code Editor Integration:** Microsoft Monaco Editor (the core engine powering VS Code) embedded for rich syntax highlighting, line numbering, minimap generation, and standard IDE capabilities.
* **State & Routing:** React Router DOM for SPA (Single Page Application) navigation architectures (/dashboard, /workspace, /instructor). Custom React Context providers handle global state management (e.g., AuthContext, ThemeContext).
* **API Communication:** Axios interceptors mapped through a centralized pi.js service to automatically handle JWT attachment, authorization headers, and token refresh cycles.

### Backend Architecture
* **Core Framework:** FastAPI (Python 3.10+) utilizing Starlette for asynchronous routing and Pydantic for strict schema validation, serialization, and type-hinting.
* **ASGI Server:** Uvicorn for handling concurrent HTTP requests efficiently.
* **ORM & Database Management:** SQLAlchemy for relational data modeling and abstraction, paired with Alembic for version-controlled database schema migrations.
* **Asynchronous Task Queue:** Celery workers backed by a Redis message broker. This is heavily utilized to decouple long-running, CPU-intensive code execution requests from the main HTTP request loop.
* **Security & Authentication:** JWT (JSON Web Tokens) with a Redis-based token blacklisting mechanism to ensure secure, immediate logout capabilities. Passwords are securely hashed via bcrypt.
* **Email Delivery:** Brevo SMTP relay integrated via native Python smtplib for dispatching real-time OTP registration and account recovery emails.

### External Services & Execution Infrastructure
* **Code Sandbox Engine:** Currently operating on a custom Python-based mock_judge0 container that leverages syncio.create_subprocess_exec for local execution testing. This infrastructure is explicitly designed to be hot-swappable with a production Judge0 API for secure, isolated code evaluation in the cloud.
* **Telemetry & Cache:** Redis is utilized as a high-speed, in-memory cache for calculating Jaccard similarity matrices, enforcing rate limits, and caching live-monitoring heartbeats.

## 2. Core Modules & Features

### Authentication & Role-Based Access Control (RBAC)
* **Registration Flow:** Multi-step registration process rigorously secured by a time-sensitive OTP (One-Time Password) delivered via email.
* **Roles:** Strict segregation of authorization privileges across student, instructor, and dmin roles, enforced via robust backend dependency injection (e.g., get_current_instructor, get_current_student).

### Classroom & Roster Management
* **Class Creation:** Instructors generate virtual classrooms equipped with unique, shareable join codes.
* **Enrollment System:** Students join environments via access codes. Instructors can actively monitor class rosters, and approve, disable, or ban specific student enrollments at any time.

### Task & Activity Authoring
* **Activity Editor:** A comprehensive form for instructors to craft coding laboratories, practice sets, and timed exams.
* **AST (Abstract Syntax Tree) Rules:** Instructors can define explicit structural requirements (e.g., "Must use a or loop", "Must define a while loop"). The backend evaluates the Python AST dynamically to enforce specific coding patterns without strictly executing the code.
* **Test Case Management:** Flexible support for both public test cases (visible to students for debugging) and hidden test cases (evaluated silently upon final submission to prevent hardcoding).

### Student Coding Workspace
* **Integrated IDE Environment:** A split-pane interface featuring the Monaco editor on the right, and an instruction panel with a live terminal output window on the left.
* **Pre-submission AST Validation:** Students receive real-time, color-coded UI feedback (Passed/Missing/Syntax Error) on whether their code structure meets the instructor's AST requirements via a safe /analyze-ast endpoint.
* **Asynchronous Execution:** Students can trigger "Run" (evaluating against public test cases) without blocking the UI, while the frontend polls for execution results via background tasks.

### Evaluation & Live Telemetry
* **Behavioral Tracking:** The frontend intercepts browser events to track paste operations, tab-switches (blur events), and mouse-leaves, acting as an anti-cheat mechanism during strict exams.
* **Live Monitoring Dashboard:** Instructors have access to a live grid of active student coding sessions, tracking connectivity heartbeats and flagging suspicious tab-switching behavior in real-time.
* **Code Similarity (Jaccard):** The backend calculates Jaccard similarity indexing scores across class submissions to instantly flag potential plagiarism or excessive collaboration.
* **Manual Grading Bench:** A specialized split-pane interface for instructors to deeply review student code, analyze raw execution outputs, inspect AST structural feedback, and subsequently assign final scores and written feedback.

## 3. Database Schema Overview

### Core Entities & Relationships

* **User**
  * Attributes: id, email, password_hash, ole (enum), ull_name, created_at.
  * Relationships: Has many Classrooms (if instructor), Enrollments, and CodingSessions.

* **Classroom**
  * Attributes: id, 
ame, section, join_code, instructor_id, is_active.
  * Relationships: Belongs to User (instructor). Has many Enrollments and Tasks.

* **Enrollment**
  * Attributes: id, student_id, class_id, status (active/disabled).
  * Relationships: Serves as the junction bridging User and Classroom.

* **Task (Activity)**
  * Attributes: id, class_id, 	itle, description, instructions, expected_output, equired_ast_rules (JSON mapping), starter_code, is_published, llow_paste.
  * Relationships: Belongs to Classroom. Has many TaskTestCases and CodingSessions.

* **TaskTestCase**
  * Attributes: id, 	ask_id, input_data, expected_output, is_hidden.
  * Relationships: Belongs to Task.

* **CodingSession**
  * Attributes: id, student_id, 	ask_id, paste_count, 	ab_switches, mouseleave_count, is_active, last_heartbeat.
  * Relationships: Belongs to User and Task. Has many Submissions.

* **Submission**
  * Attributes: id, session_id, aw_code, status (pending, graded), grade_score, eedback_text, submitted_at.
  * Relationships: Belongs to CodingSession. Has many ExecutionRequests.

* **ExecutionRequest**
  * Attributes: id, submission_id, status (running, completed, runtime_error, timed_out), stdout, stderr, exit_code, idempotency_key.
  * Relationships: Belongs to Submission.

## 4. API & Routing Structure

### Authentication & Identity
* POST /auth/register - Initiates user registration and dispatches the OTP email.
* POST /auth/verify-otp - Validates the submitted OTP and finalizes account creation.
* POST /auth/login - Authenticates credentials and issues JWT access tokens.
* GET /users/me - Retrieves the currently authenticated user's profile and preferences.

### Classrooms & Management
* POST /classrooms/ - Instructor provisions a new class.
* GET /classrooms/ - Context-aware retrieval of classes based on user role (Instructor's owned classes vs Student's enrolled classes).
* POST /classrooms/join - Student registers to a class via an access code.
* PATCH /classrooms/{class_id}/enrollments/{student_id} - Instructor manages specific student access constraints.

### Activities & Execution
* POST /instructors/tasks/ - Author and parameterize a new coding activity.
* POST /instructors/tasks/{task_id}/test-cases - Define input/output assertions for a specific task.
* GET /activities/{task_id} - Student fetches task details, starter code, and public requirements.
* POST /activities/{task_id}/analyze-ast - Secure, non-executing endpoint to validate student code against instructor-defined AST structural rules.
* POST /execution/requests - Dispatches source code to the Celery worker queue / Judge0 sandbox.
* GET /execution/requests/{execution_id} - Polls the system for the asynchronous resolution of an execution task.

### Monitoring & Grading
* POST /logs/coding-session - Telemetry webhook for processing frontend tracking metrics (blur, paste, mouseleave).
* GET /instructors/tasks/{task_id}/coding-sessions - Aggregates live heartbeat and behavioral data for the monitoring dashboard.
* GET /instructors/review-queue - Compiles a list of pending student submissions requiring manual instructor grading.
* PATCH /evaluation/submissions/{submission_id}/grade - Commits the final quantitative grade and qualitative instructor feedback.

## 5. Current Development Status

* **Completed Phases (1 to 3):**
  * Backend API endpoints and Pydantic schemas are strictly defined, validated, and stable.
  * The React frontend is fully wired to the backend API, seamlessly handling complex UI states such as the dynamic Workspace AST checklist and the comprehensive Instructor Grading Bench.
  * The local sandbox (mock_judge0) has been successfully refactored to execute actual Python subprocesses securely and maps terminal exit codes flawlessly back to backend schema enums (e.g., untime_error, 	imed_out).
  * Repository cleanliness has been rigorously enforced (removed orphaned scripts, untracked local SQLite databases to prevent merge conflicts, and purged unused placeholder assets).

* **Pending Next Steps (Phase 4):**
  * **Sandbox Migration:** Transitioning execution logic from the local mock_judge0 script to a production-ready Judge0 environment (via RapidAPI or a self-hosted Docker cluster).
  * **Infrastructure Provisioning:** Deploying the FastAPI backend, Uvicorn servers, and Celery workers to a cloud provider (e.g., Render) while provisioning a managed PostgreSQL database (e.g., Supabase) and a Redis message broker (e.g., Upstash).
  * **Frontend Deployment:** Hosting the Vite React application on a global edge network (e.g., Vercel) and updating backend CORS origins to accept production traffic.
  * **End-to-End Stress Testing:** Conducting rigorous load tests on the Celery workers and Redis queues to ensure high-concurrency stability during simulated, live-exam conditions.
