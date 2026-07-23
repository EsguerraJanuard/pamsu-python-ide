from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.integrations.local_llm import (
    LocalLLMAdapterResponseError,
    LocalLLMAdapterUnavailableError,
    LocalLLMAssistanceRequest,
    LocalLLMAssistanceResponse,
    validate_local_llm_adapter,
    validate_local_llm_response,
)


def build_request() -> LocalLLMAssistanceRequest:
    return LocalLLMAssistanceRequest(
        request_id=str(uuid4()),
        assistance_kind="hint",
        task_id=1,
        source_code="print('hello')",
        user_question="How can I improve this?",
    )


def test_local_llm_request_accepts_only_approved_context():
    request = build_request()

    assert request.task_id == 1
    assert request.assistance_kind == "hint"
    assert request.source_code == "print('hello')"


def test_local_llm_request_requires_context():
    with pytest.raises(ValidationError):
        LocalLLMAssistanceRequest(
            request_id=str(uuid4()),
            assistance_kind="hint",
            task_id=1,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "official_grade",
        "automatic_grade",
        "plagiarism_verdict",
        "misconduct_verdict",
        "risk_score",
        "hidden_tests",
        "clipboard_content",
    ],
)
def test_local_llm_request_rejects_prohibited_fields(
    field_name: str,
):
    payload = {
        "request_id": str(uuid4()),
        "assistance_kind": "feedback",
        "task_id": 1,
        "source_code": "print('safe')",
        field_name: "prohibited",
    }

    with pytest.raises(ValidationError):
        LocalLLMAssistanceRequest.model_validate(payload)


@pytest.mark.parametrize(
    "field_name",
    [
        "score",
        "grade",
        "official_grade",
        "plagiarism_verdict",
        "misconduct_verdict",
        "risk_score",
    ],
)
def test_local_llm_response_rejects_grades_and_verdicts(
    field_name: str,
):
    payload = {
        "request_id": str(uuid4()),
        "assistance_kind": "explanation",
        "content": "Draft educational assistance.",
        "generated_at": datetime.now(timezone.utc),
        field_name: "prohibited",
    }

    with pytest.raises(ValidationError):
        LocalLLMAssistanceResponse.model_validate(payload)


def test_incompatible_local_llm_adapter_is_rejected():
    with pytest.raises(LocalLLMAdapterUnavailableError):
        validate_local_llm_adapter(object())


@pytest.mark.parametrize(
    ("request_kind", "response_kind", "same_request_id"),
    [
        ("hint", "feedback", True),
        ("hint", "hint", False),
    ],
)
def test_local_llm_response_must_match_request(
    request_kind: str,
    response_kind: str,
    same_request_id: bool,
):
    request = LocalLLMAssistanceRequest(
        request_id=str(uuid4()),
        assistance_kind=request_kind,
        task_id=1,
        user_question="Help me understand.",
    )

    response = LocalLLMAssistanceResponse(
        request_id=(request.request_id if same_request_id else str(uuid4())),
        assistance_kind=response_kind,
        content="Draft assistance only.",
        generated_at=datetime.now(timezone.utc),
    )

    with pytest.raises(LocalLLMAdapterResponseError):
        validate_local_llm_response(
            request=request,
            response=response,
        )
