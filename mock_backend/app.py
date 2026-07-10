"""
app.py
------
Mock backend for the Smart Society Complaint Resolution System API
(Team Sputnik, MAY2026-Team-095), matching openapi.yaml v1.0.0.

Run:
    pip install -r requirements.txt
    python app.py

Server listens on http://localhost:8000/v1/...

HOW TO CONTROL RESPONSES
=========================
1. Checksum on a "primary field" (documented in each route's docstring
   below). Example - POST /auth/register uses `email`:

       email = "pbn@x.com"    -> checksum picks 201 or 409 deterministically
       email = "pbn@x.com#1"  -> forces documented[1]  (always 409)
       email = "pbn@x.com#0"  -> forces documented[0]  (always 201)

2. `_status` query parameter - forces ANY status code on ANY endpoint,
   even ones not in the OpenAPI spec (500, 403, 422...) for negative
   testing of the frontend's error handling:

       GET /v1/complaints/C-1001?_status=500

3. No control given -> the endpoint returns its "happy path" response.

Every request is logged to stdout with the selection method used.
"""

import logging

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

import fake_data as fd
from checksum import resolve_status, error_body

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("mock_backend")

API_PREFIX = "/v1"


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def log_selection(method_path: str, debug_info: dict, status: int):
    logger.info(
        "%-35s primary=%r checksum=%s documented=%s -> idx=%s method=%s status=%s",
        method_path,
        debug_info.get("primary_value"),
        debug_info.get("checksum"),
        debug_info.get("documented"),
        debug_info.get("selected_index"),
        debug_info.get("method"),
        status,
    )


def respond(route_label: str, documented: list, primary_value=None,
            success_body_fn=None, error_message: str = None):
    """
    Central response builder used by every route.

    - route_label: string like "POST /auth/register" for logging
    - documented: list of int status codes in spec order, e.g. [201, 409]
    - primary_value: the field value used for checksum selection (or None)
    - success_body_fn: zero-arg callable returning the JSON body for the
      lowest / "happy path" documented status (assumed to be the only
      2xx in the list)
    - error_message: optional override message for non-2xx responses
    """
    status, debug_info = resolve_status(request, documented, primary_value)
    log_selection(route_label, debug_info, status)

    if status < 300:
        body = success_body_fn() if success_body_fn else {"success": True}
        return jsonify(body), status

    return jsonify(error_body(status, error_message)), status


def body_json() -> dict:
    """Safely get JSON body regardless of content-type quirks."""
    return request.get_json(silent=True) or {}


def body_form() -> dict:
    """Merge form fields (multipart/form-data) into a plain dict."""
    return request.form.to_dict()


# ----------------------------------------------------------------------
# Root / index
# ----------------------------------------------------------------------

@app.route("/")
@app.route(API_PREFIX)
def index():
    routes = sorted(
        f"{','.join(r.methods - {'HEAD', 'OPTIONS'})} {r.rule}"
        for r in app.url_map.iter_rules()
        if r.rule.startswith(API_PREFIX)
    )
    return jsonify({
        "name": "Smart Society Mock Backend",
        "status": "running",
        "hint": "Add ?_status=NNN to any request to force a status code. "
                "See each route's docstring for the checksum-controlled field.",
        "routes": routes,
    })


# ----------------------------------------------------------------------
# AUTH
# ----------------------------------------------------------------------

@app.route(f"{API_PREFIX}/auth/register", methods=["POST"])
def auth_register():
    """primary field: email -> documented = [201, 409]"""
    data = body_json()
    email = data.get("email")

    def success():
        return fd.make_user(
            role=data.get("role", "Resident"),
            name=data.get("name"),
            email=email,
            mobile=data.get("mobileNumber"),
            flat=data.get("flatNumber"),
        )

    return respond("POST /auth/register", [201, 409], email, success,
                    error_message="Email already registered")


@app.route(f"{API_PREFIX}/auth/login", methods=["POST"])
def auth_login():
    """primary field: usernameOrEmail -> documented = [200, 401]"""
    data = body_json()
    username = data.get("usernameOrEmail")

    def success():
        return {
            "accessToken": "mock-jwt-token." + fd.new_id("tok"),
            "tokenType": "bearer",
            "user": fd.make_user(email=str(username or "user@example.com").split("#")[0]),
        }

    return respond("POST /auth/login", [200, 401], username, success,
                    error_message="Invalid credentials")


@app.route(f"{API_PREFIX}/auth/forgot-password", methods=["POST"])
def auth_forgot_password():
    """no primary field -> documented = [200]"""
    return respond("POST /auth/forgot-password", [200], None,
                    lambda: {"message": "Reset link sent if the email exists"})


# ----------------------------------------------------------------------
# USERS
# ----------------------------------------------------------------------

@app.route(f"{API_PREFIX}/users/me", methods=["GET"])
def users_me():
    """no primary field (use ?_status=NNN to force errors) -> documented = [200]"""
    return respond("GET /users/me", [200], None, lambda: fd.make_user())


# ----------------------------------------------------------------------
# CATEGORIES
# ----------------------------------------------------------------------

@app.route(f"{API_PREFIX}/categories", methods=["GET"])
def categories():
    """documented = [200]"""
    return respond("GET /categories", [200], None, lambda: fd.CATEGORIES)


# ----------------------------------------------------------------------
# RESIDENT COMPLAINTS
# ----------------------------------------------------------------------

@app.route(f"{API_PREFIX}/complaints", methods=["POST"])
def complaints_create():
    """primary field: description -> documented = [201]"""
    data = body_form() or body_json()
    description = data.get("description")

    def success():
        return fd.make_complaint(
            category=data.get("category"),
            subCategory=data.get("subCategory"),
            priority=data.get("priority", "Medium"),
            location=data.get("location"),
            description=description,
            status="Open",
        )

    return respond("POST /complaints", [201], description, success)


@app.route(f"{API_PREFIX}/complaints", methods=["GET"])
def complaints_list():
    """documented = [200] (filters: status, category - do not affect selection)"""
    def success():
        count = 5
        return [fd.make_complaint() for _ in range(count)]

    return respond("GET /complaints", [200], None, success)


@app.route(f"{API_PREFIX}/complaints/<complaint_id>", methods=["GET"])
def complaints_detail(complaint_id):
    """primary field: complaintId (path) -> documented = [200, 404]"""
    def success():
        return fd.make_complaint(complaint_id=complaint_id.split("#")[0])

    return respond(f"GET /complaints/{complaint_id}", [200, 404], complaint_id,
                    success, error_message="Complaint not found")


@app.route(f"{API_PREFIX}/complaints/<complaint_id>/timeline", methods=["GET"])
def complaints_timeline(complaint_id):
    """documented = [200]"""
    cid = complaint_id.split("#")[0]

    def success():
        return [fd.make_complaint_update(cid, i) for i in range(4)]

    return respond(f"GET /complaints/{complaint_id}/timeline", [200], None, success)


@app.route(f"{API_PREFIX}/complaints/<complaint_id>/attachments", methods=["POST"])
def complaints_attachments(complaint_id):
    """documented = [201]"""
    def success():
        return [fd.make_attachment() for _ in range(len(request.files) or 1)]

    return respond(f"POST /complaints/{complaint_id}/attachments", [201], None, success)


@app.route(f"{API_PREFIX}/complaints/<complaint_id>/feedback", methods=["POST"])
def complaints_feedback(complaint_id):
    """primary field: rating -> documented = [200]"""
    data = body_json()
    cid = complaint_id.split("#")[0]

    def success():
        return fd.make_complaint(
            complaint_id=cid,
            status="Closed",
            rating=data.get("rating"),
            feedbackComment=data.get("comment"),
        )

    return respond(f"POST /complaints/{complaint_id}/feedback", [200], None, success)


# ----------------------------------------------------------------------
# ADMIN
# ----------------------------------------------------------------------

@app.route(f"{API_PREFIX}/admin/dashboard/summary", methods=["GET"])
def admin_dashboard_summary():
    """documented = [200]"""
    return respond("GET /admin/dashboard/summary", [200], None, fd.make_dashboard_summary)


@app.route(f"{API_PREFIX}/admin/complaints", methods=["GET"])
def admin_complaints():
    """documented = [200]"""
    return respond("GET /admin/complaints", [200], None,
                    lambda: [fd.make_complaint() for _ in range(8)])


@app.route(f"{API_PREFIX}/admin/complaints/<complaint_id>/assign", methods=["PUT"])
def admin_assign(complaint_id):
    """primary field: staffId -> documented = [200]"""
    data = body_json()
    cid = complaint_id.split("#")[0]

    def success():
        return fd.make_complaint(
            complaint_id=cid,
            status=data.get("status", "Assigned"),
            assignedStaffId=data.get("staffId"),
        )

    return respond(f"PUT /admin/complaints/{complaint_id}/assign", [200],
                    data.get("staffId"), success)


@app.route(f"{API_PREFIX}/admin/complaints/report", methods=["GET"])
def admin_report():
    """documented = [200]; supports ?format=csv"""
    fmt = request.args.get("format", "json")
    complaints = [fd.make_complaint() for _ in range(6)]

    if fmt == "csv":
        header = "id,category,priority,status,residentName\n"
        rows = "\n".join(
            f"{c['id']},{c['category']},{c['priority']},{c['status']},{c['residentName']}"
            for c in complaints
        )
        return Response(header + rows, mimetype="text/csv")

    return respond("GET /admin/complaints/report", [200], None, lambda: complaints)


# ----------------------------------------------------------------------
# MAINTENANCE STAFF
# ----------------------------------------------------------------------

@app.route(f"{API_PREFIX}/staff/dashboard/summary", methods=["GET"])
def staff_dashboard_summary():
    """documented = [200]"""
    return respond("GET /staff/dashboard/summary", [200], None, fd.make_dashboard_summary)


@app.route(f"{API_PREFIX}/staff/complaints", methods=["GET"])
def staff_complaints():
    """documented = [200]"""
    return respond("GET /staff/complaints", [200], None,
                    lambda: [fd.make_complaint(status="Assigned") for _ in range(5)])


@app.route(f"{API_PREFIX}/staff/complaints/<complaint_id>/status", methods=["PUT"])
def staff_update_status(complaint_id):
    """primary field: status -> documented = [200]"""
    data = body_form() or body_json()
    cid = complaint_id.split("#")[0]
    new_status = data.get("status", "In Progress")

    def success():
        return fd.make_complaint(complaint_id=cid, status=new_status)

    return respond(f"PUT /staff/complaints/{complaint_id}/status", [200],
                    new_status, success)


@app.route(f"{API_PREFIX}/staff/complaints/history", methods=["GET"])
def staff_history():
    """documented = [200]"""
    return respond("GET /staff/complaints/history", [200], None,
                    lambda: [fd.make_complaint(status="Closed") for _ in range(4)])


@app.route(f"{API_PREFIX}/staff/notification-preferences", methods=["GET"])
def staff_prefs_get():
    """documented = [200]"""
    return respond("GET /staff/notification-preferences", [200], None,
                    fd.make_staff_notification_preferences)


@app.route(f"{API_PREFIX}/staff/notification-preferences", methods=["PUT"])
def staff_prefs_put():
    """documented = [200]"""
    data = body_json()

    def success():
        prefs = fd.make_staff_notification_preferences()
        prefs.update(data)
        return prefs

    return respond("PUT /staff/notification-preferences", [200], None, success)


# ----------------------------------------------------------------------
# NOTIFICATIONS (shared)
# ----------------------------------------------------------------------

@app.route(f"{API_PREFIX}/notifications", methods=["GET"])
def notifications_list():
    """documented = [200]; supports ?channel=All|Email|SMS|InApp"""
    return respond("GET /notifications", [200], None,
                    lambda: [fd.make_notification() for _ in range(6)])


@app.route(f"{API_PREFIX}/notifications/<notification_id>/read", methods=["PUT"])
def notifications_mark_read(notification_id):
    """documented = [200]"""
    return respond(f"PUT /notifications/{notification_id}/read", [200], None,
                    lambda: {"success": True, "id": notification_id.split("#")[0]})


@app.route(f"{API_PREFIX}/notifications/read-all", methods=["PUT"])
def notifications_read_all():
    """documented = [200]"""
    return respond("PUT /notifications/read-all", [200], None,
                    lambda: {"success": True})


@app.route(f"{API_PREFIX}/notifications/settings", methods=["GET"])
def notification_settings_get():
    """documented = [200]"""
    return respond("GET /notifications/settings", [200], None,
                    fd.make_notification_settings)


@app.route(f"{API_PREFIX}/notifications/settings", methods=["PUT"])
def notification_settings_put():
    """documented = [200]"""
    data = body_json()

    def success():
        settings = fd.make_notification_settings()
        settings.update(data)
        return settings

    return respond("PUT /notifications/settings", [200], None, success)


# ----------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
