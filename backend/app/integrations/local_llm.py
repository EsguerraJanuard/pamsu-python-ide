from datetime import datetime, timezone
from typing import Annotated, Literal, Protocol, Self, runtime_checkable
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


LocalLLMAssistanceKind = Literal[
    "explanation",
    "hint",
    "feedback",
]

MAX_LOCAL_LLM_ACTIVITY_TITLE_LENGTH = 200
MAX_LOCAL_LLM_PUBLIC_INSTRUCTIONS_LENGTH = 5_000
MAX_LOCAL_LLM_SOURCE_CODE_LENGTH = 100_000
MAX_LOCAL_LLM_USER_QUESTION_LENGTH = 2_000
MAX_LOCAL_LLM_CONTEXT_ITEM_LENGTH = 500
MAX_LOCAL_LLM_CONTEXT_ITEMS = 50
MAX_LOCAL_LLM_RESPONSE_LENGTH = 10_000
MAX_LOCAL_LLM_MODEL_LABEL_LENGTH = 100

LocalLLMContextItem = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=MAX_LOCAL_LLM_CONTEXT_ITEM_LENGTH,
    ),
]


class LocalLLMAdapterError(Exception):
    """Base exception raised by a local LLM integration adapter."""


class LocalLLMAdapterUnavailableError(
    LocalLLMAdapterError,
):
    """Raised when no compatible local LLM adapter is configured."""


class LocalLLMAdapterRejectedError(
    LocalLLMAdapterError,
):
    """Raised when the local LLM runtime rejects a request."""


class LocalLLMAdapterResponseError(
    LocalLLMAdapterError,
):
    """Raised when the local LLM runtime returns an invalid response."""


def _normalize_uuid(
    value: str,
    *,
    field_label: str,
) -> str:
    try:
        parsed_value = UUID(value)
    except (
        TypeError,
        ValueError,
        AttributeError,
    ) as error:
        raise ValueError(f"{field_label} must be a valid UUID.") from error

    return str(parsed_value)


def _normalize_timezone_aware_datetime(
    value: datetime,
) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Local LLM timestamps must include a timezone.")

    return value.astimezone(timezone.utc)


class LocalLLMAssistanceRequest(BaseModel):
    request_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
        description=("Backend-generated correlation UUID for one local LLM request."),
    )
    assistance_kind: LocalLLMAssistanceKind
    task_id: int = Field(
        ...,
        gt=0,
    )
    submission_id: int | None = Field(
        default=None,
        gt=0,
    )
    activity_title: str | None = Field(
        default=None,
        max_length=MAX_LOCAL_LLM_ACTIVITY_TITLE_LENGTH,
    )
    public_instructions: str | None = Field(
        default=None,
        max_length=MAX_LOCAL_LLM_PUBLIC_INSTRUCTIONS_LENGTH,
        description=("Only student-visible activity instructions may be supplied."),
    )
    source_code: str | None = Field(
        default=None,
        max_length=MAX_LOCAL_LLM_SOURCE_CODE_LENGTH,
        description=(
            "Optional student source snapshot supplied only for the "
            "requested explanation, hint, or feedback."
        ),
    )
    user_question: str | None = Field(
        default=None,
        max_length=MAX_LOCAL_LLM_USER_QUESTION_LENGTH,
    )
    public_review_context: list[LocalLLMContextItem] = Field(
        default_factory=list,
        max_length=MAX_LOCAL_LLM_CONTEXT_ITEMS,
        description=(
            "Privacy-safe, student-visible review context only. Hidden "
            "tests, expected outputs, similarity details, and surveillance "
            "telemetry are prohibited."
        ),
    )

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("request_id")
    @classmethod
    def validate_request_id(
        cls,
        value: str,
    ) -> str:
        return _normalize_uuid(
            value,
            field_label="Request ID",
        )

    @field_validator(
        "activity_title",
        "public_instructions",
        "source_code",
        "user_question",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if "\x00" in value:
            raise ValueError("Local LLM request text cannot contain null bytes.")

        if not value.strip():
            return None

        return value

    @model_validator(mode="after")
    def validate_context_present(
        self,
    ) -> Self:
        if not any(
            (
                self.activity_title,
                self.public_instructions,
                self.source_code,
                self.user_question,
                self.public_review_context,
            )
        ):
            raise ValueError("At least one assistance context field is required.")

        return self

    # INPUT BOUNDARY:
    # This request intentionally excludes passwords, OTPs, JWTs, API keys,
    # hidden test data, expected outputs, unreleased grades, grade feedback,
    # similarity details, behavioral telemetry, clipboard contents, pasted
    # text, browsing history, individual keystrokes, screen recordings,
    # webcam data, microphone data, and misconduct conclusions.


class LocalLLMAssistanceResponse(BaseModel):
    request_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
    )
    assistance_kind: LocalLLMAssistanceKind
    content: str = Field(
        ...,
        min_length=1,
        max_length=MAX_LOCAL_LLM_RESPONSE_LENGTH,
    )
    model_label: str | None = Field(
        default=None,
        max_length=MAX_LOCAL_LLM_MODEL_LABEL_LENGTH,
    )
    generated_at: datetime

    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("request_id")
    @classmethod
    def validate_response_request_id(
        cls,
        value: str,
    ) -> str:
        return _normalize_uuid(
            value,
            field_label="Request ID",
        )

    @field_validator(
        "content",
        "model_label",
    )
    @classmethod
    def validate_response_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if "\x00" in value:
            raise ValueError("Local LLM response text cannot contain null bytes.")

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("Local LLM response text cannot be empty.")

        return normalized_value

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(
        cls,
        value: datetime,
    ) -> datetime:
        return _normalize_timezone_aware_datetime(value)

    # OUTPUT BOUNDARY:
    # The response contains draft assistance text only. It has no score,
    # maximum score, pass/fail result, grade, release decision, plagiarism
    # verdict, cheating verdict, misconduct verdict, or risk ranking.


@runtime_checkable
class LocalLLMAdapter(Protocol):
    def generate_assistance(
        self,
        *,
        request: LocalLLMAssistanceRequest,
    ) -> LocalLLMAssistanceResponse:
        """
        Generate draft educational assistance using a local LLM runtime.

        The adapter must not persist credentials, assign official grades,
        release grades, or determine plagiarism, cheating, or misconduct.
        """


def validate_local_llm_adapter(
    adapter: object,
) -> LocalLLMAdapter:
    if not isinstance(
        adapter,
        LocalLLMAdapter,
    ):
        raise LocalLLMAdapterUnavailableError(
            "A compatible local LLM adapter is not configured."
        )

    return adapter


def validate_local_llm_response(
    *,
    request: LocalLLMAssistanceRequest,
    response: LocalLLMAssistanceResponse,
) -> LocalLLMAssistanceResponse:
    if response.request_id != request.request_id:
        raise LocalLLMAdapterResponseError(
            "The local LLM response request ID does not match."
        )

    if response.assistance_kind != request.assistance_kind:
        raise LocalLLMAdapterResponseError(
            "The local LLM response assistance kind does not match."
        )

    return response


# LOCAL-RUNTIME BOUNDARY:
# Pillar 14 defines contracts only. It does not implement a model runtime,
# model download, inference server, provider client, prompt template,
# background queue, or persistence layer.

# GRADING BOUNDARY:
# Local LLM output may draft explanations, hints, or feedback only.
# Authorized instructors remain the sole source of official grades.

# MISCONDUCT BOUNDARY:
# Local LLM output must never determine or rank plagiarism, cheating,
# copying, misconduct, or behavioral risk.

# PRIVACY BOUNDARY:
# Only explicitly approved student-visible context may be supplied.
# Hidden tests, expected outputs, credentials, unreleased grades,
# similarity details, surveillance data, and clipboard content are excluded.
