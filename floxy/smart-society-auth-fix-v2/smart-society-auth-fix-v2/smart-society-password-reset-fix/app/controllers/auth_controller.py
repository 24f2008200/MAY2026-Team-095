from typing import Any

from app.services.auth_service import (
    forgot_password,
    login,
    profile,
    register,
    reset_password,
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

def reset_password_handler() -> tuple[dict[str, Any], int]:
    """Validate a reset token and save the user's new password."""
    return reset_password()
