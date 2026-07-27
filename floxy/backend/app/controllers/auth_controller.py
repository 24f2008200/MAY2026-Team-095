from typing import Any

from app.services.auth_service import (
    login,
    profile,
    register,
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