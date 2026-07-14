from fastapi import FastAPI

from app.routers import (
    auth,
    evaluation,
    execution,
    instructor,
    logs,
    registration,
)


app = FastAPI(
    title="PAMSU Python IDE Backend",
    description=(
        "Backend API for the PAMSU Web-Based Python IDE with "
        "authentication, OTP registration, structural analytics, "
        "submission management, and privacy-conscious session indicators."
    ),
    version="0.2.0",
)


app.include_router(auth.router)
app.include_router(registration.router)
app.include_router(instructor.router)
app.include_router(execution.router)
app.include_router(logs.router)
app.include_router(evaluation.router)


@app.get(
    "/",
    tags=["System"],
)
def read_root() -> dict[str, str]:
    return {
        "message": "PAMSU Python IDE Backend is running.",
        "version": app.version,
    }


@app.get(
    "/health",
    tags=["System"],
)
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }
