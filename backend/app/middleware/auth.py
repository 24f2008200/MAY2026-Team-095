from functools import wraps

from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt,
)


def roles_required(*allowed_roles):
    """
    Restrict access to one or more user roles.

    Example:
        @roles_required("ADMIN")

        @roles_required("ADMIN", "STAFF")
    """

    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            verify_jwt_in_request()

            claims = get_jwt()

            user_role = claims.get("role")

            if user_role not in allowed_roles:
                return {
                    "success": False,
                    "message": "You are not authorized to access this resource."
                }, 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(fn):
    """
    Allow ADMIN users only.
    """
    return roles_required("ADMIN")(fn)


def staff_required(fn):
    """
    Allow STAFF users only.
    """
    return roles_required("STAFF")(fn)


def resident_required(fn):
    """
    Allow RESIDENT users only.
    """
    return roles_required("RESIDENT")(fn)


def admin_or_staff_required(fn):
    """
    Allow ADMIN and STAFF users.
    """
    return roles_required(
        "ADMIN",
        "STAFF",
    )(fn)


def authenticated_required(fn):
    """
    Allow any authenticated user.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):

        verify_jwt_in_request()

        return fn(*args, **kwargs)

    return wrapper