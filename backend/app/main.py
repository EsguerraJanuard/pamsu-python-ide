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
)


APP_TITLE = "PAMSU Python IDE Backend"
APP_VERSION = "0.5.0"

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
            "Instructor-authorized activity, test-case, and academic "
            "management operations."
        ),
    },
    {
        "name": "Activities",
        "description": (
            "Student-safe access to published laboratory and homework "
            "activities from active classroom enrollments."
        ),
    },
    {
        "name": "Execution",
        "description": (
            "Submission records and execution-request operations. "
            "Student code must run only through the isolated sandbox "
            "service."
        ),
    },
    {
        "name": "Behavioral Logs",
        "description": (
            "Privacy-conscious session indicators without clipboard "
            "contents, screen capture, webcam, microphone, browsing "
            "history, or individual keystroke collection."
        ),
    },
    {
        "name": "Evaluation",
        "description": (
            "AST and similarity indicators intended only for instructor "
            "review. These indicators do not automatically assign grades."
        ),
    },
]


app = FastAPI(
    title=APP_TITLE,
    description=(
        "Backend API for the PAMSU Web-Based Python IDE with "
        "university-email authentication, OTP registration, classroom "
        "and enrollment management, activity and test-case management, "
        "submission management, isolated execution integration boundaries, "
        "automated structural analytics, and privacy-conscious session "
        "indicators."
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
