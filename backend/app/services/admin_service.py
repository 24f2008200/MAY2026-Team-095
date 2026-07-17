from flask import request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError, Schema, fields, validate
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

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


def list_staff():
    staff_members = (
        User.query
        .filter_by(role=UserRole.STAFF, is_active=True)
        .order_by(User.name.asc())
        .all()
    )

    return {
        "success": True,
        "staff": [
            {
                "id": member.id,
                "name": member.name,
                "email": member.email,
                "mobile_number": member.mobile_number,
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
