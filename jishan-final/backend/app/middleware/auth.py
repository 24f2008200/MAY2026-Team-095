from functools import wraps

from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt_identity,
)


def _load_active_user():
    """Resolve the JWT identity against the database on every protected request.

    This prevents a deactivated/deleted account from continuing to use an old JWT
    until its normal expiry and avoids trusting a stale role claim for authorization.
    """
    from app.models.user import User

    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None

    user = User.query.get(user_id)
    if not user or not user.is_active:
        return None
    return user


def roles_required(*allowed_roles):
    """Restrict access to one or more active user roles."""

    allowed = {str(role).upper() for role in allowed_roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            user = _load_active_user()
            if not user:
                return {
                    "success": False,
                    "message": "Your session is no longer valid. Please sign in again.",
                }, 401

            if user.role.value.upper() not in allowed:
                return {
                    "success": False,
                    "message": "You are not authorized to access this resource.",
                }, 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(fn):
    return roles_required("ADMIN")(fn)


def staff_required(fn):
    return roles_required("STAFF")(fn)


def resident_required(fn):
    return roles_required("RESIDENT")(fn)


def admin_or_staff_required(fn):
    return roles_required("ADMIN", "STAFF")(fn)


def authenticated_required(fn):
    """Allow any authenticated user whose account is still active."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()

        if not _load_active_user():
            return {
                "success": False,
                "message": "Your session is no longer valid. Please sign in again.",
            }, 401

        return fn(*args, **kwargs)

    return wrapper
