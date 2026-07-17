from fastapi import FastAPI, status

from app.routers import (
    activities,
    audit_records,
    auth,
    classrooms,
    evaluation,
    execution,
    instructor,
    logs,
    notifications,
    registration,
    submissions,
)


APP_TITLE = "PAMSU Python IDE Backend"
APP_VERSION = "0.11.0"

OPENAPI_TAGS = [
    {
        "name": "System",
        "description": ("Application availability and service information."),
    },
    {
        "name": "Authentication",
        "description": ("Verified-user login and access-token operations."),
    },
    {
        "name": "Registration",
        "description": (
            "University-email registration and OTP verification. "
            "Client applications cannot assign account roles."
        ),
    },
    {
        "name": "Classrooms",
        "description": (
            "Instructor-owned classroom management, backend-generated "
            "class codes, student enrollment operations, and "
            "privacy-safe classroom archive notifications."
        ),
    },
    {
        "name": "Instructor",
        "description": (
            "Instructor-authorized activity, test-case, submission, "
            "execution-request, coding-session, evaluation, "
            "review-queue, gradebook, and manual grading operations. "
            "Review and gradebook summaries exclude source code and "
            "sensitive analytics. Automated indicators remain "
            "review-only."
        ),
    },
    {
        "name": "Activities",
        "description": (
            "Student-safe access to published laboratory and homework "
            "activities, public sample test cases, student-owned "
            "coding-session lifecycle operations, and the "
            "authenticated student's own released manual grades."
        ),
    },
    {
        "name": "Submissions",
        "description": (
            "Student-owned immutable submission attempts. Student "
            "identity, attempt numbering, official-attempt state, "
            "status, timestamps, and approved instructor "
            "notifications are controlled by the backend."
        ),
    },
    {
        "name": "Execution",
        "description": (
            "Student-owned run, check, and submit execution-request "
            "snapshots. FastAPI persists and authorizes requests only. "
            "Student Python code must execute exclusively through the "
            "partner-owned isolated sandbox worker."
        ),
    },
    {
        "name": "Behavioral Logs",
        "description": (
            "Privacy-conscious aggregate session indicators without "
            "clipboard contents, pasted text, individual keystrokes, "
            "browsing history, screen recording, webcam, or microphone "
            "collection."
        ),
    },
    {
        "name": "Evaluation",
        "description": (
            "Static AST and source-similarity indicators for "
            "authorized instructor review, student-safe "
            "released-grade viewing, explicit review-status updates, "
            "manual instructor grading, and privacy-safe grade-release "
            "notifications. Automated indicators never assign official "
            "grades or determine plagiarism, cheating, copying, or "
            "misconduct."
        ),
    },
    {
        "name": "Notifications",
        "description": (
            "Authenticated students and instructors may access only "
            "their own backend-generated in-app notifications, unread "
            "counts, and read-state operations. Notification creation, "
            "recipient selection, titles, messages, and event payloads "
            "remain exclusive to trusted academic workflows."
        ),
    },
    {
        "name": "Audit Trail",
        "description": (
            "Authenticated users may read only audit records attributed "
            "to their own account. Audit creation remains exclusive to "
            "trusted backend workflows, and records exclude source code, "
            "credentials, OTP values, hidden test data, execution output, "
            "surveillance data, unreleased grades, and automated "
            "misconduct conclusions."
        ),
    },
]


app = FastAPI(
    title=APP_TITLE,
    description=(
        "Backend API for the PAMSU Web-Based Python IDE with "
        "university-email authentication, OTP registration, classroom "
        "and enrollment management, activity and test-case management, "
        "student-owned coding sessions, privacy-safe aggregate session "
        "telemetry, immutable submission attempts, queued execution "
        "requests, backend-controlled execution-attempt counters, "
        "isolated worker integration boundaries, static structural and "
        "source-similarity analytics, instructor-owned paginated review "
        "queues, privacy-safe gradebook summaries, student-safe released "
        "manual-grade lists, explicit evaluation-status control, "
        "manual instructor grading workflows, immutable approved "
        "academic events, recipient-owned in-app notifications, "
        "notification unread counts, owner-scoped read-state operations, "
        "and immutable privacy-safe audit records for authenticated "
        "academic accountability."
    ),
    version=APP_VERSION,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.include_router(auth.router)
app.include_router(registration.router)
app.include_router(classrooms.router)
app.include_router(instructor.router)
app.include_router(activities.router)
app.include_router(submissions.router)
app.include_router(execution.router)
app.include_router(logs.router)
app.include_router(evaluation.router)
app.include_router(notifications.router)
app.include_router(audit_records.router)


@app.get(
    "/",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Read API information",
)
def read_root() -> dict[str, str]:
    return {
        "message": f"{APP_TITLE} is running.",
        "version": APP_VERSION,
        "documentation": "/docs",
    }


@app.get(
    "/health",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Check service health",
)
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "version": APP_VERSION,
    }
