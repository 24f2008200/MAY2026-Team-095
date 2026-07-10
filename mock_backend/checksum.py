"""
checksum.py
-----------
Deterministic response selection for the mock backend.

The core idea:
  - Every endpoint declares a list of "documented" status codes, in the
    same order as they appear in the OpenAPI spec, e.g. [201, 409].
  - Given a "primary field" value from the request (e.g. email, name,
    usernameOrEmail...), we compute a checksum and use modulus arithmetic
    to deterministically pick one of the documented codes.
  - A frontend developer can also force an exact index by appending
    "#N" to the primary field value, e.g. email = "a@b.com#1" always
    selects documented[1] (409 in the example above), regardless of
    the checksum.
  - Independently, ANY endpoint can be forced to return an arbitrary
    status code (even ones not in the OpenAPI spec, like 500 or 403)
    by adding a `_status` query parameter, e.g. ?_status=500.
    This always wins over everything else.
"""

from typing import Any, List, Optional, Tuple

DEFAULT_ERROR_MESSAGES = {
    400: "Bad request",
    401: "Invalid credentials",
    403: "Forbidden",
    404: "Resource not found",
    409: "Conflict - resource already exists",
    422: "Unprocessable entity",
    429: "Too many requests",
    500: "Internal server error",
    503: "Service unavailable",
}


def checksum(value: Any) -> int:
    """Sum of character codes of the string form of `value`."""
    return sum(ord(c) for c in str(value))


def strip_force_index(value: Any) -> Tuple[str, Optional[int]]:
    """
    Given a raw field value that may end in '#N' (e.g. "pbn#1"),
    return (clean_value, forced_index) where forced_index is None
    if no '#N' suffix was present or it wasn't a valid integer.
    """
    if value is None:
        return "", None

    text = str(value)

    if "#" in text:
        base, _, suffix = text.rpartition("#")
        if suffix.isdigit():
            return base, int(suffix)

    return text, None


def pick_from_documented(primary_value: Any, documented: List[int]) -> Tuple[int, dict]:
    """
    Pick a status code from `documented` based on `primary_value`.

    Returns (status_code, debug_info) where debug_info explains how the
    pick was made (useful for logging).
    """
    if not documented:
        documented = [200]

    clean_value, forced_index = strip_force_index(primary_value)

    if forced_index is not None:
        idx = forced_index % len(documented)
        method = "forced_index"
    else:
        idx = checksum(clean_value) % len(documented)
        method = "checksum_modulus"

    status = documented[idx]

    debug_info = {
        "primary_value": clean_value,
        "checksum": checksum(clean_value),
        "documented": documented,
        "selected_index": idx,
        "method": method,
    }

    return status, debug_info


def resolve_status(
    request,
    documented: List[int],
    primary_value: Any = None,
) -> Tuple[int, dict]:
    """
    Master resolver used by every route.

    Priority order:
      1. `_status` query parameter -> force this exact status code,
         no matter what (even codes outside `documented`).
      2. `primary_value` given -> checksum/forced-index pick among
         `documented`.
      3. Otherwise -> first entry in `documented` (the "happy path").
    """
    forced_status = request.args.get("_status")

    if forced_status is not None and forced_status.strip().lstrip("-").isdigit():
        status = int(forced_status)
        debug_info = {
            "primary_value": None,
            "checksum": None,
            "documented": documented,
            "selected_index": None,
            "method": "query_override(_status)",
        }
        return status, debug_info

    if primary_value is not None and str(primary_value) != "":
        return pick_from_documented(primary_value, documented)

    status = documented[0] if documented else 200
    debug_info = {
        "primary_value": None,
        "checksum": None,
        "documented": documented,
        "selected_index": 0,
        "method": "default",
    }
    return status, debug_info


def error_body(status: int, message: Optional[str] = None) -> dict:
    return {
        "success": False,
        "status": status,
        "message": message or DEFAULT_ERROR_MESSAGES.get(status, "Error"),
    }
