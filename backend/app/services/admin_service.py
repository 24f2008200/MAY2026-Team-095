from flask import request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError, Schema, fields, validate
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from typing import Any

from app.extensions import db
from app.models.category import Category
from app.models.complaint import Complaint, ComplaintPriority, ComplaintStatus
from app.models.feedback import Feedback
from app.models.user import User, UserRole
from app.services.complaint_service import (
    _add_timeline_entry,
    _complaint_response,
    _get_user,
)
from app.services.notification_service import create_notification


class AssignStaffSchema(Schema):
    staff_id = fields.Integer(required=True, strict=True)


class CreateCategorySchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
    )
    description = fields.String(
        required=False,
        validate=validate.Length(max=255),
    )


assign_staff_schema = AssignStaffSchema()
create_category_schema = CreateCategorySchema()


def get_dashboard():
    total_complaints = Complaint.query.count()

    status_counts = {
        status.value: Complaint.query.filter_by(status=status).count()
        for status in ComplaintStatus
    }

    priority_counts = {
        priority.value: Complaint.query.filter_by(priority=priority).count()
        for priority in ComplaintPriority
    }

    total_residents = User.query.filter_by(
        role=UserRole.RESIDENT,
        is_active=True,
    ).count()

    total_staff = User.query.filter_by(
        role=UserRole.STAFF,
        is_active=True,
    ).count()

    recent_complaints = (
        Complaint.query
        .order_by(Complaint.created_at.desc())
        .limit(5)
        .all()
    )

    avg_rating = db.session.query(
        func.avg(Feedback.rating)
    ).scalar()

    return {
        "success": True,
        "dashboard": {
            "total_complaints": total_complaints,
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "total_residents": total_residents,
            "total_staff": total_staff,
            "average_feedback_rating": (
                round(float(avg_rating), 2) if avg_rating else None
            ),
            "recent_complaints": [
                _complaint_response(complaint)
                for complaint in recent_complaints
            ],
        },
    }, 200


def assign_staff(complaint_id: int):
    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    try:
        data = assign_staff_schema.load(json_data)
    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages,
        }, 400

    admin_id = int(get_jwt_identity())
    complaint = Complaint.query.get(complaint_id)

    if not complaint:
        return {
            "success": False,
            "message": "Complaint not found.",
        }, 404

    if complaint.status in {
        ComplaintStatus.CLOSED,
        ComplaintStatus.RESOLVED,
    }:
        return {
            "success": False,
            "message": "Cannot assign staff to a resolved or closed complaint.",
        }, 400

    staff = User.query.filter_by(
        id=data["staff_id"],
        role=UserRole.STAFF,
        is_active=True,
    ).first()

    if not staff:
        return {
            "success": False,
            "message": "Invalid or inactive staff member.",
        }, 400

    complaint.assigned_staff_id = staff.id
    complaint.status = ComplaintStatus.ASSIGNED

    try:
        _add_timeline_entry(
            complaint=complaint,
            user_id=admin_id,
            status=ComplaintStatus.ASSIGNED.value,
            comment=f"Assigned to staff: {staff.name}",
        )

        create_notification(
            user_id=staff.id,
            complaint_id=complaint.id,
            title="New Complaint Assigned",
            message=(
                f"You have been assigned complaint "
                f"{complaint.complaint_code}: {complaint.title}"
            ),
            notification_type="COMPLAINT_ASSIGNED",
        )

        create_notification(
            user_id=complaint.resident_id,
            complaint_id=complaint.id,
            title="Staff Assigned",
            message=(
                f"Staff member {staff.name} has been assigned to your "
                f"complaint {complaint.complaint_code}."
            ),
            notification_type="STAFF_ASSIGNED",
        )

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to assign staff.",
        }, 500

    return {
        "success": True,
        "message": "Staff assigned successfully.",
        "complaint": _complaint_response(complaint),
    }, 200


def get_reports():
    category_report = (
        db.session.query(
            Category.name,
            func.count(Complaint.id).label("count"),
        )
        .outerjoin(Complaint, Complaint.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )

    resolved_complaints = Complaint.query.filter(
        Complaint.resolved_at.isnot(None)
    ).all()

    resolution_times = []

    for complaint in resolved_complaints:
        if complaint.created_at and complaint.resolved_at:
            delta = complaint.resolved_at - complaint.created_at
            resolution_times.append(delta.total_seconds())

    avg_resolution_hours = None

    if resolution_times:
        avg_seconds = sum(resolution_times) / len(resolution_times)
        avg_resolution_hours = round(avg_seconds / 3600, 2)

    feedback_stats = (
        db.session.query(
            func.count(Feedback.id),
            func.avg(Feedback.rating),
        )
        .first()
    )

    feedback_count = feedback_stats[0] or 0
    avg_feedback = feedback_stats[1]

    return {
        "success": True,
        "reports": {
            "complaints_by_category": [
                {"category": name, "count": count}
                for name, count in category_report
            ],
            "average_resolution_hours": avg_resolution_hours,
            "feedback_summary": {
                "total_feedback": feedback_count,
                "average_rating": (
                    round(float(avg_feedback), 2)
                    if avg_feedback
                    else None
                ),
            },
            "status_overview": {
                status.value: Complaint.query.filter_by(status=status).count()
                for status in ComplaintStatus
            },
        },
    }, 200


def _extract_trade(member: User) -> str:
    """
    Derive trade from user record.
    """
    if member.building:
        return member.building
    return "General"


def list_staff():
    trade = request.args.get("trade", type=str)

    query = User.query.filter_by(role=UserRole.STAFF, is_active=True)

    if trade:
        query = query.filter(User.building == trade)

    staff_members = query.order_by(User.name.asc()).all()

    return {
        "success": True,
        "staff": [
            {
                "id": member.id,
                "name": member.name,
                "email": member.email,
                "mobile_number": member.mobile_number,
                "flat_number": member.flat_number,
                "building": member.building,
                "trade": _extract_trade(member),
                "username": member.email.split("@")[0] if member.email else member.name,
                "assigned_complaints_count": Complaint.query.filter_by(
                    assigned_staff_id=member.id,
                    status=ComplaintStatus.ASSIGNED,
                ).count()
                + Complaint.query.filter_by(
                    assigned_staff_id=member.id,
                    status=ComplaintStatus.IN_PROGRESS,
                ).count(),
            }
            for member in staff_members
        ],
    }, 200


def create_staff(json_data: dict) -> tuple[dict[str, Any], int]:
    """
    Create a new maintenance staff account.
    Only accessible by administrators.
    """
    if not json_data:
        return {"success": False, "message": "Request body is required."}, 400

    # Extract and validate staff fields
    name = json_data.get("name", "").strip()
    email = json_data.get("email", "").strip().lower()
    mobile_number = json_data.get("mobile_number", "").strip()
    flat_number = json_data.get("flat_number", "").strip()
    building = json_data.get("building", "").strip()
    password = json_data.get("password", "")
    trade = json_data.get("trade", "").strip()

    if not name:
        return {"success": False, "message": "Name is required."}, 400

    if not email or "@" not in email:
        return {"success": False, "message": "Valid email is required."}, 400

    if not mobile_number:

        existing_mobile = True
        counter = 0
        while existing_mobile:
            candidate = "9" + str((hash(name + email + str(counter)) % 900000000) + 100000000)
            candidate = candidate[:10]
            if candidate[0] not in "6789":
                candidate = "9" + candidate[1:]
            if not User.query.filter_by(mobile_number=candidate).first():
                mobile_number = candidate
                existing_mobile = False
            counter += 1
            if counter > 100:
                return {"success": False, "message": "Unable to generate unique mobile number."}, 500
    elif len(mobile_number) != 10 or not mobile_number.isdigit():
        return {"success": False, "message": "Mobile number must be 10 digits."}, 400

    if not flat_number:
        flat_number = "N/A"

    if not building:
        building = trade or "General"

    if not password or len(password) < 8:
        return {"success": False, "message": "Password must be at least 8 characters."}, 400

    if not trade:
        return {"success": False, "message": "Trade is required."}, 400

    # Check for existing email or mobile
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return {"success": False, "message": "Email already registered."}, 409

    existing_mobile = User.query.filter_by(mobile_number=mobile_number).first()
    if existing_mobile:
        return {"success": False, "message": "Mobile number already registered."}, 409

    # Create the staff user
    password_hash = generate_password_hash(password)

    new_staff = User(
        name=name,
        email=email,
        mobile_number=mobile_number,
        password_hash=password_hash,
        role=UserRole.STAFF,
        flat_number=flat_number,
        building=building,
        is_active=True,
    )


    try:
        db.session.add(new_staff)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "message": "Unable to create staff account."}, 500

    create_notification(
        user_id=new_staff.id,
        complaint_id=None,
        title="Staff Account Created",
        message=f"Your maintenance staff account has been created. Your trade is: {trade}.",
        notification_type="STAFF_CREATED",
    )

    return {
        "success": True,
        "message": "Staff account created successfully.",
        "staff": {
            "id": new_staff.id,
            "name": new_staff.name,
            "email": new_staff.email,
            "mobile_number": new_staff.mobile_number,
            "trade": trade,
            "flat_number": new_staff.flat_number,
            "building": new_staff.building,
        },
    }, 201


def remove_staff(staff_id: int, admin_id: int) -> tuple[dict[str, Any], int]:
    """
    Deactivate a staff account by setting is_active to False.
    Admin cannot deactivate their own account.
    """
    if admin_id == staff_id:
        return {"success": False, "message": "You cannot deactivate your own account."}, 403

    staff = User.query.filter_by(
        id=staff_id,
        role=UserRole.STAFF,
    ).first()

    if not staff:
        return {"success": False, "message": "Staff member not found."}, 404

    staff.is_active = False

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "message": "Unable to remove staff member."}, 500

    return {
        "success": True,
        "message": f"Staff member '{staff.name}' has been deactivated.",
    }, 200


def create_category():
    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    try:
        data = create_category_schema.load(json_data)
    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages,
        }, 400

    name = data["name"].strip()

    existing = Category.query.filter(
        func.lower(Category.name) == name.lower()
    ).first()

    if existing:
        return {
            "success": False,
            "message": "Category already exists.",
        }, 409

    category = Category(
        name=name,
        description=data.get("description", "").strip() or None,
        is_active=True,
    )

    try:
        db.session.add(category)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to create category.",
        }, 500

    return {
        "success": True,
        "message": "Category created successfully.",
        "category": category.to_dict(),
    }, 201


def list_all_categories():
    """
    All categories (active and inactive) for the admin management view.
    The public /categories endpoint only returns active ones.
    """
    categories = Category.query.order_by(Category.name.asc()).all()

    return {
        "success": True,
        "categories": [category.to_dict() for category in categories],
    }, 200


def set_category_status(category_id: int, is_active: bool):
    category = Category.query.get(category_id)

    if not category:
        return {
            "success": False,
            "message": "Category not found.",
        }, 404

    category.is_active = is_active

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to update category.",
        }, 500

    return {
        "success": True,
        "message": f"Category {'activated' if is_active else 'deactivated'} successfully.",
        "category": category.to_dict(),
    }, 200


def _resident_summary(resident: User) -> dict:
    return {
        "id": resident.id,
        "name": resident.name,
        "email": resident.email,
        "mobile_number": resident.mobile_number,
        "flat_number": resident.flat_number,
        "building": resident.building,
        "is_active": resident.is_active,
        "created_at": (
            resident.created_at.isoformat()
            if resident.created_at
            else None
        ),
    }


def list_pending_residents():
    """
    Residents who have registered but not yet been approved by an admin.
    """
    pending = (
        User.query
        .filter_by(role=UserRole.RESIDENT, is_active=False)
        .order_by(User.created_at.asc())
        .all()
    )

    return {
        "success": True,
        "residents": [_resident_summary(r) for r in pending],
    }, 200


def approve_resident(resident_id: int):
    resident = User.query.filter_by(
        id=resident_id,
        role=UserRole.RESIDENT,
    ).first()

    if not resident:
        return {
            "success": False,
            "message": "Resident not found.",
        }, 404

    if resident.is_active:
        return {
            "success": False,
            "message": "This account is already approved.",
        }, 409

    resident.is_active = True
    db.session.commit()

    create_notification(
        user_id=resident.id,
        complaint_id=None,
        title="Account Approved",
        message=(
            "Your resident account has been approved. You can now log "
            "in and start raising complaints."
        ),
        notification_type="ACCOUNT_APPROVED",
    )
    db.session.commit()

    return {
        "success": True,
        "message": "Resident approved successfully.",
        "resident": _resident_summary(resident),
    }, 200


def reject_resident(resident_id: int):
    """
    Rejects (deletes) a pending resident registration. Only allowed while
    the account is still pending - once approved, use staff-style
    deactivation instead of deleting real account history.
    """
    resident = User.query.filter_by(
        id=resident_id,
        role=UserRole.RESIDENT,
    ).first()

    if not resident:
        return {
            "success": False,
            "message": "Resident not found.",
        }, 404

    if resident.is_active:
        return {
            "success": False,
            "message": (
                "This account is already approved and active - it can't "
                "be rejected, only deactivated by other means."
            ),
        }, 409

    db.session.delete(resident)
    db.session.commit()

    return {
        "success": True,
        "message": "Registration rejected and removed.",
    }, 200
