from typing import Literal, Protocol, runtime_checkable


OTPDeliveryPurpose = Literal[
    "registration",
    "email_change",
]

MIN_OTP_CODE_LENGTH = 6
MAX_OTP_CODE_LENGTH = 12
MAX_OTP_DELIVERY_REFERENCE_LENGTH = 255


class OTPEmailAdapterError(Exception):
    """Base exception raised by an OTP email-delivery adapter."""


class OTPEmailAdapterUnavailableError(
    OTPEmailAdapterError,
):
    """Raised when no usable email-delivery adapter is configured."""


class OTPEmailAdapterRejectedError(
    OTPEmailAdapterError,
):
    """Raised when the configured email provider rejects delivery."""


@runtime_checkable
class OTPEmailAdapter(Protocol):
    def send_otp(
        self,
        *,
        recipient_email: str,
        otp_code: str,
        purpose: OTPDeliveryPurpose,
        expires_in_seconds: int,
    ) -> None:
        """
        Deliver one temporary plaintext OTP to the university email address.

        The adapter must return only after the provider accepts the delivery
        request. It must not validate the OTP, persist the plaintext code,
        create users, assign roles, mutate challenge state, or return the OTP.
        """


def validate_otp_email_adapter(
    adapter: object,
) -> OTPEmailAdapter:
    """
    Validate that an injected object satisfies the runtime adapter contract.

    This provides an early, controlled failure for dependency wiring without
    implementing or selecting a concrete email provider.
    """

    if not isinstance(
        adapter,
        OTPEmailAdapter,
    ):
        raise OTPEmailAdapterUnavailableError(
            "A compatible OTP email-delivery adapter is not configured."
        )

    return adapter


# OWNERSHIP BOUNDARY:
# The backend owns OTP generation, hashing, expiration, resend limits,
# verification attempts, challenge consumption, account creation, and roles.

# PLAINTEXT BOUNDARY:
# The temporary plaintext OTP may exist only in process memory while the
# backend calls send_otp(). It must never be persisted, logged, included in
# audit records, returned through API responses, or exposed through OpenAPI.

# PARTNER BOUNDARY:
# A concrete partner adapter may deliver email only. It must not query or
# mutate users, registrations, challenges, roles, grades, submissions,
# execution data, analytics, or telemetry.

# IMPLEMENTATION BOUNDARY:
# This module defines the interface and controlled adapter errors only.
# SMTP, third-party email APIs, background workers, retries, and provider
# credentials remain outside the current implementation.
