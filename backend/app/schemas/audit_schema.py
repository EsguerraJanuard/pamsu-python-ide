from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


AuditActionType = Literal[
    "user_registered",
    "login_succeeded",
    "login_failed",
    "classroom_created",
    "classroom_updated",
    "classroom_archived",
    "classroom_reactivated",
    "student_enrolled",
    "enrollment_status_changed",
    "activity_created",
    "activity_updated",
    "activity_published",
    "activity_unpublished",
    "submission_created",
    "submission_status_changed",
    "grade_created",
    "grade_updated",
    "grade_released",
    "notification_marked_read",
    "notifications_marked_read",
]

AuditResourceType = Literal[
    "user",
    "classroom",
    "enrollment",
    "task",
    "submission",
    "grade",
    "notification",
]

AuditOutcome = Literal[
    "succeeded",
    "denied",
    "failed",
]


PROHIBITED_AUDIT_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "password_digest",
        "otp",
        "otp_code",
        "otp_hash",
        "one_time_password",
        "verification_code",
        "raw_code",
        "source_code",
        "starter_code",
        "submitted_code",
        "code_snapshot",
        "standard_input",
        "stdin",
        "hidden_test",
        "hidden_tests",
        "hidden_test_case",
        "hidden_test_cases",
        "expected_output",
        "expected_outputs",
        "stdout",
        "stderr",
        "execution_output",
        "execution_result",
        "worker_task_id",
        "ast",
        "ast_details",
        "ast_findings",
        "required_ast_rules",
        "similarity",
        "similarity_score",
        "similarity_details",
        "similarity_results",
        "clipboard",
        "clipboard_content",
        "clipboard_text",
        "paste_content",
        "pasted_content",
        "pasted_text",
        "individual_keystrokes",
        "keystrokes",
        "key_events",
        "browsing_history",
        "screen_recording",
        "screen_capture",
        "webcam",
        "webcam_data",
        "microphone",
        "microphone_data",
        "misconduct_verdict",
        "cheating_verdict",
        "plagiarism_verdict",
        "automatic_verdict",
        "score",
        "max_score",
        "grade_value",
        "feedback",
        "unreleased_score",
        "unreleased_feedback",
    }
)


def _normalize_audit_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _validate_json_value(
    value: Any,
    *,
    path: str,
) -> None:
    if value is None or isinstance(
        value,
        (bool, int, float, str),
    ):
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(
                item,
                path=f"{path}[{index}]",
            )
        return

    if isinstance(value, dict):
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise ValueError("Audit metadata keys must be strings.")

            normalized_key = _normalize_audit_key(key)

            if normalized_key in PROHIBITED_AUDIT_KEYS:
                raise ValueError(
                    f"Audit metadata contains a prohibited field: {path}.{key}"
                )

            _validate_json_value(
                nested_value,
                path=f"{path}.{key}",
            )
        return

    raise ValueError("Audit metadata must contain JSON-compatible values only.")


def validate_audit_data(
    value: Any,
) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise ValueError("Audit metadata must be a JSON object.")

    _validate_json_value(
        value,
        path="audit_data",
    )

    return value


class AuditRecordCreateInternal(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    audit_key: str = Field(
        min_length=1,
        max_length=255,
    )
    actor_user_id: int | None = Field(
        default=None,
        gt=0,
    )
    action_type: AuditActionType
    resource_type: AuditResourceType
    resource_id: str = Field(
        min_length=1,
        max_length=100,
    )
    outcome: AuditOutcome = "succeeded"
    audit_data: dict[str, Any] = Field(
        default_factory=dict,
    )
    occurred_at: datetime | None = None

    @field_validator(
        "audit_key",
        "resource_id",
    )
    @classmethod
    def validate_nonblank_identifier(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("Identifier must not be blank.")

        return normalized

    @field_validator(
        "audit_data",
        mode="before",
    )
    @classmethod
    def validate_privacy_safe_audit_data(
        cls,
        value: Any,
    ) -> dict[str, Any]:
        return validate_audit_data(value)


class AuditRecordResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    audit_id: str
    actor_user_id: int | None
    action_type: AuditActionType
    resource_type: AuditResourceType
    resource_id: str
    outcome: AuditOutcome
    audit_data: dict[str, Any]
    occurred_at: datetime
    created_at: datetime

    @field_validator(
        "audit_data",
        mode="before",
    )
    @classmethod
    def validate_response_audit_data(
        cls,
        value: Any,
    ) -> dict[str, Any]:
        return validate_audit_data(value)


class AuditRecordListResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[AuditRecordResponse]
    page: int = Field(
        ge=1,
    )
    page_size: int = Field(
        ge=1,
        le=100,
    )
    total: int = Field(
        ge=0,
    )
    total_pages: int = Field(
        ge=0,
    )
