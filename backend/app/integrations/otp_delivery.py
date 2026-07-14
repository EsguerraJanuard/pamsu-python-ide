from typing import NoReturn

from app.services.otp_service import OTPDeliveryAdapter


class OTPDeliveryUnavailableError(RuntimeError):
    """Raised when no working OTP email adapter is configured."""


class UnavailableOTPDeliveryAdapter:
    """
    Safe default adapter used until the partner connects email delivery.

    It intentionally does not print, log, save, or expose the plaintext OTP.
    """

    def send_otp(
        self,
        *,
        recipient_email: str,
        otp_code: str,
        purpose: str,
        expires_in_seconds: int,
    ) -> NoReturn:
        del recipient_email
        del otp_code
        del purpose
        del expires_in_seconds

        raise OTPDeliveryUnavailableError("OTP email delivery is not configured.")


def get_otp_delivery_adapter() -> OTPDeliveryAdapter:
    """
    FastAPI dependency provider for OTP email delivery.

    The partner should replace the returned adapter with the actual
    university-email implementation while preserving the send_otp contract.
    """

    return UnavailableOTPDeliveryAdapter()


# PARTNER INTEGRATION:
# Replace UnavailableOTPDeliveryAdapter with the actual email implementation.
#
# Required method:
#
# send_otp(
#     recipient_email: str,
#     otp_code: str,
#     purpose: str,
#     expires_in_seconds: int,
# ) -> None
#
# The adapter is responsible only for delivering the email.
# It must never:
# - create or verify OTP challenges;
# - create user accounts;
# - assign student or instructor roles;
# - persist plaintext OTP codes;
# - log plaintext OTP codes;
# - return OTP codes through an API response.
