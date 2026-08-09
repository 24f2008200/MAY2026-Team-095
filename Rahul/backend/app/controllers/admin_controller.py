from typing import Any

from flask import request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError, Schema, fields, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.category import Category
from app.models.complaint import Complaint, ComplaintPriority, ComplaintStatus
from app.models.feedback import Feedback
from app.models.user import User, UserRole
from app.services.complaint_service import (
    _add_timeline_entry,
    _complaint_response,
    _get_user,
    get_all_complaints,
)
from app.services.notification_service import create_notification
from app.services.admin_service import (
    get_dashboard,
    get_reports,
    list_staff,
    create_staff,
    remove_staff,
    assign_staff,
    create_category,
    list_pending_residents,
    approve_resident,
    reject_resident,
)


def dashboard_handler() -> tuple[dict[str, Any], int]:
    return get_dashboard()


def assign_staff_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return assign_staff(complaint_id)


def reports_handler() -> tuple[dict[str, Any], int]:
    return get_reports()


def list_staff_handler() -> tuple[dict[str, Any], int]:
    return list_staff()


def create_category_handler() -> tuple[dict[str, Any], int]:
    return create_category()


def create_staff_handler() -> tuple[dict[str, Any], int]:
    """
    Create a new maintenance staff account.
    Only accessible by administrators.
    #i added it: delegates to admin_service.create_staff.
    """
    json_data = request.get_json(silent=True)
    return create_staff(json_data)


def remove_staff_handler(staff_id: int) -> tuple[dict[str, Any], int]:
    """
    Deactivate a staff account.
    #i added it: delegates to admin_service.remove_staff.
    """
    admin_id = int(get_jwt_identity())
    return remove_staff(staff_id, admin_id)


def list_complaints_handler() -> tuple[dict[str, Any], int]:
    """
    List all complaints for admin dashboard.
    #i added it: returns all complaints with full details.
    """
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return {
        "success": True,
        "complaints": [_complaint_response(c) for c in complaints],
    }, 200


def list_pending_residents_handler() -> tuple[dict[str, Any], int]:
    return list_pending_residents()


def approve_resident_handler(resident_id: int) -> tuple[dict[str, Any], int]:
    return approve_resident(resident_id)


def reject_resident_handler(resident_id: int) -> tuple[dict[str, Any], int]:
    return reject_resident(resident_id)
