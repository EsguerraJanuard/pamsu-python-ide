"""
A local stand-in for Judge0 CE, for development and QA only.

It speaks the part of the Judge0 API the backend uses, in the same shape:

- POST /submissions?base64_encoded=true|false[&wait=true]
  fields: source_code, language_id (71 = Python only), stdin,
  expected_output, callback_url, cpu_time_limit, wall_time_limit (others
  are accepted and ignored). Answers {"token"}, or the full result with
  wait=true.
- GET /submissions/{token}?base64_encoded=true|false
- When callback_url is set, it PUTs the finished submission there, as
  Judge0 does: stdout, stderr, compile_output, message (base64 when the
  submission was base64), status {id, description}, time, memory, token.

Status ids follow Judge0: 3 Accepted, 4 Wrong Answer (stdout differs from
expected_output), 5 Time Limit Exceeded, 11 Runtime Error (NZEC).

WARNING: the code runs as a normal Python process on this machine, with no
sandbox. Never expose this server to a network; run it on 127.0.0.1 (or in
its own container) with your own test code only. Production uses the real
Judge0 (RapidAPI), configured by JUDGE0_API_URL on Render.

    pip install -r mock_judge0/requirements.txt
    uvicorn main:app --app-dir mock_judge0 --host 127.0.0.1 --port 8001
    # backend: JUDGE0_API_URL=http://127.0.0.1:8001 and
    #          WEBHOOK_BASE_URL=<an address of the backend this server can reach>
"""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import time
import uuid

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict

app = FastAPI(title="mock Judge0 (local development only)")

PYTHON_LANGUAGE_ID = 71
MAX_WALL_SECONDS = 20.0
STATUS = {
    3: "Accepted",
    4: "Wrong Answer",
    5: "Time Limit Exceeded",
    11: "Runtime Error (NZEC)",
}
TEXT_FIELDS = ("stdout", "stderr", "compile_output", "message")

# Finished submissions, by token, stored decoded (plain text).
results: dict[str, dict] = {}


class SubmissionRequest(BaseModel):
    source_code: str
    language_id: int
    stdin: str | None = None
    expected_output: str | None = None
    callback_url: str | None = None
    cpu_time_limit: float | None = None
    wall_time_limit: float | None = None

    model_config = ConfigDict(extra="ignore")


def _decode(value: str | None, encoded: bool) -> str | None:
    if value is None or not encoded:
        return value
    try:
        return base64.b64decode(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=422, detail="Fields must be valid base64 when base64_encoded=true.") from None


def _encode(value: str | None, encoded: bool) -> str | None:
    if value is None or not encoded:
        return value
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _same_output(stdout: str, expected: str) -> bool:
    # Judge0 ignores trailing whitespace at the end of the output.
    return stdout.rstrip() == expected.rstrip()


def _text(raw: bytes | None) -> str:
    # Judge0 runs Linux: on a Windows machine, turn \r\n back into \n.
    return (raw or b"").decode("utf-8", "replace").replace("\r\n", "\n")


def run_python(source: str, stdin: str | None, expected: str | None, wall_seconds: float) -> dict:
    started = time.monotonic()
    try:
        process = subprocess.run(
            # -I: ignore PYTHON* variables and the user site; -X utf8: UTF-8 I/O on Windows too.
            [sys.executable, "-I", "-X", "utf8", "-c", source],
            input=(stdin or "").encode("utf-8"),
            capture_output=True,
            timeout=wall_seconds,
            # Plain tracebacks, as Judge0 returns them (Python 3.13 colours them when FORCE_COLOR is set).
            env={**{k: v for k, v in os.environ.items() if k != "FORCE_COLOR"}, "NO_COLOR": "1"},
        )
    except subprocess.TimeoutExpired as expired:
        status_id = 5
        stdout = _text(expired.stdout)
        stderr = _text(expired.stderr)
        exit_code = None
    else:
        stdout = _text(process.stdout)
        stderr = _text(process.stderr)
        exit_code = process.returncode
        if process.returncode != 0:
            status_id = 11
        elif expected is not None and not _same_output(stdout, expected):
            status_id = 4
        else:
            status_id = 3
    return {
        "stdout": stdout or None,
        "stderr": stderr or None,
        "compile_output": None,
        "message": "Exited with error status 1" if status_id == 11 else None,
        "status": {"id": status_id, "description": STATUS[status_id]},
        "exit_code": exit_code,
        "time": f"{time.monotonic() - started:.3f}",
        "memory": 0,
    }


def _public(token: str, encoded: bool) -> dict:
    result = dict(results[token])
    for field in TEXT_FIELDS:
        result[field] = _encode(result.get(field), encoded)
    return {"token": token, **result}


def send_callback(url: str, token: str, encoded: bool) -> None:
    try:
        response = httpx.put(url, json=_public(token, encoded), timeout=10)
        print(f"callback for {token}: {response.status_code}")
    except httpx.HTTPError as error:
        print(f"callback for {token} failed: {type(error).__name__}")


@app.post("/submissions", status_code=201)
def create_submission(
    request: SubmissionRequest,
    background_tasks: BackgroundTasks,
    base64_encoded: bool = Query(default=False),
    wait: bool = Query(default=False),
):
    if request.language_id != PYTHON_LANGUAGE_ID:
        raise HTTPException(status_code=422, detail="This mock only runs Python (language_id 71).")
    source = _decode(request.source_code, base64_encoded)
    stdin = _decode(request.stdin, base64_encoded)
    expected = _decode(request.expected_output, base64_encoded)
    wall = min(request.wall_time_limit or request.cpu_time_limit or 5.0, MAX_WALL_SECONDS)

    token = str(uuid.uuid4())
    if wait:
        results[token] = run_python(source, stdin, expected, wall)
        return _public(token, base64_encoded)

    def finish() -> None:
        results[token] = run_python(source, stdin, expected, wall)
        if request.callback_url:
            send_callback(request.callback_url, token, base64_encoded)

    background_tasks.add_task(finish)
    return {"token": token}


@app.get("/submissions/{token}")
def get_submission(token: str, base64_encoded: bool = Query(default=False)):
    if token not in results:
        # Judge0 answers "In Queue" while a submission is still running.
        return {"token": token, "status": {"id": 1, "description": "In Queue"}}
    return _public(token, base64_encoded)


@app.get("/about")
def about():
    return {"version": "mock", "note": "Local development stand-in for Judge0 CE; not a sandbox."}
