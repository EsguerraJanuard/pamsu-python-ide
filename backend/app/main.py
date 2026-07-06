from fastapi import FastAPI

from app.routers import execution, instructor, logs


app = FastAPI(
    title="PAMSU Python IDE Backend",
    description="Backend API for the Web-Based Python IDE with AST feedback and behavioral tracking.",
    version="0.1.0",
)


app.include_router(instructor.router)
app.include_router(execution.router)
app.include_router(logs.router)


@app.get("/")
def read_root():
    return {"message": "PAMSU Python IDE Backend is running."}
