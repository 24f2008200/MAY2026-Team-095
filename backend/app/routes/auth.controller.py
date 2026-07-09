from app.services.auth_service import (
    register,
    login,
    profile
)


def register_user():
    return register()


def login_user():
    return login()


def get_profile():
    return profile()