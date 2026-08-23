from typing import Any

from app.services.auth_service import (
    forgot_password,
    login,
    profile,
    register,
    reset_password_with_token,
    verify_password_reset_otp,
)


def register_user() -> tuple[dict[str, Any], int]:
    """
    Register a new resident.
    """
    return register()


def login_user() -> tuple[dict[str, Any], int]:
    """
    Authenticate a user.
    """
    return login()


def get_profile() -> tuple[dict[str, Any], int]:
    """
    Return currently authenticated user's profile.
    """
    return profile()


def forgot_password_handler() -> tuple[dict[str, Any], int]:
    """
    Accept a forgot-password request for the given email.
    """
    return forgot_password()


def verify_password_reset_otp_handler() -> tuple[dict[str, Any], int]:
    """Verify a recovery OTP and issue a password-reset token."""
    return verify_password_reset_otp()


def reset_password_handler() -> tuple[dict[str, Any], int]:
    """Set a new password using a verified recovery token."""
    return reset_password_with_token()
