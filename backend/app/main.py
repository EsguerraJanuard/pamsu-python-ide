from fastapi import FastAPI, status

from app.routers import (
    activities,
    auth,
    classrooms,
    evaluation,
    execution,
    instructor,
    logs,
    registration,
    submissions,
)


APP_TITLE = "PAMSU Python IDE Backend"
APP_VERSION = "0.8.0"

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
            "class codes, and student enrollment operations."
        ),
    },
    {
        "name": "Instructor",
        "description": (
            "Instructor-authorized activity, test-case, submission, "
            "execution-request, and coding-session review operations. "
            "Automated indicators remain review-only."
        ),
    },
    {
        "name": "Activities",
        "description": (
            "Student-safe access to published laboratory and homework "
            "activities, public sample test cases, and student-owned "
            "coding-session lifecycle operations."
        ),
    },
    {
        "name": "Submissions",
        "description": (
            "Student-owned immutable submission attempts. Student "
            "identity, attempt numbering, official-attempt state, "
            "status, and timestamps are controlled by the backend."
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
            "AST and similarity indicators intended only for instructor "
            "review. These indicators do not automatically assign grades "
            "or misconduct verdicts."
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
        "isolated worker integration boundaries, automated structural "
        "analytics, and instructor review workflows."
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
