from datetime import datetime, timezone

from flask import request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError

from app.extensions import db
from app.models.complaint import Complaint, ComplaintStatus
from app.schemas.complaint_schema import ComplaintTimelineSchema
from app.services.complaint_service import (
    _add_timeline_entry,
    _complaint_response,
    _get_user,
    _notify_comment_participants,
    _timeline_response,
    get_all_complaints,
    get_complaint,
)
from app.services.notification_service import create_notification
from sqlalchemy.exc import IntegrityError

timeline_schema = ComplaintTimelineSchema()

STAFF_ALLOWED_STATUSES = {
    ComplaintStatus.IN_PROGRESS,
    ComplaintStatus.RESOLVED,
}


def get_assigned_complaints():
    return get_all_complaints()


def get_assigned_complaint(complaint_id: int):
    return get_complaint(complaint_id)


def update_complaint_status(complaint_id: int):
    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    try:
        data = timeline_schema.load(json_data)
    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages,
        }, 400

    try:
        new_status = ComplaintStatus(data["status"])
    except ValueError:
        return {
            "success": False,
            "message": "Invalid status value.",
        }, 400

    if new_status not in STAFF_ALLOWED_STATUSES:
        return {
            "success": False,
            "message": (
                "Staff can only set status to IN_PROGRESS or RESOLVED."
            ),
        }, 400

    user_id = int(get_jwt_identity())
    user = _get_user(user_id)

    if not user:
        return {
            "success": False,
            "message": "User not found.",
        }, 404

    complaint = Complaint.query.get(complaint_id)

    if not complaint:
        return {
            "success": False,
            "message": "Complaint not found.",
        }, 404

    if complaint.assigned_staff_id != user_id:
        return {
            "success": False,
            "message": "This complaint is not assigned to you.",
        }, 403

    if complaint.status not in {
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.IN_PROGRESS,
    }:
        return {
            "success": False,
            "message": "Only active assigned work orders can be updated.",
        }, 400

    if (
        new_status == ComplaintStatus.IN_PROGRESS
        and complaint.status not in {
            ComplaintStatus.ASSIGNED,
        }
    ):
        return {
            "success": False,
            "message": (
                "Complaint must be ASSIGNED before moving to IN_PROGRESS."
            ),
        }, 400

    if (
        new_status == ComplaintStatus.RESOLVED
        and complaint.status != ComplaintStatus.IN_PROGRESS
    ):
        return {
            "success": False,
            "message": (
                "Complaint must be IN_PROGRESS before marking as RESOLVED."
            ),
        }, 400

    complaint.status = new_status

    if new_status == ComplaintStatus.RESOLVED:
        complaint.resolved_at = datetime.now(timezone.utc)
        complaint.closed_at = None

    comment = data.get("comment")

    try:
        _add_timeline_entry(
            complaint=complaint,
            user_id=user_id,
            status=new_status.value,
            comment=comment,
        )

        create_notification(
            user_id=complaint.resident_id,
            complaint_id=complaint.id,
            title="Complaint Status Updated",
            message=(
                f"Your complaint {complaint.complaint_code} is now "
                f"{new_status.value}."
            ),
            notification_type="STATUS_UPDATED",
        )

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to update complaint status.",
        }, 500

    return {
        "success": True,
        "message": "Complaint status updated successfully.",
        "complaint": _complaint_response(complaint),
    }, 200


def get_dashboard_summary():
    user_id = int(get_jwt_identity())

    status_counts = {
        status: Complaint.query.filter_by(
            assigned_staff_id=user_id,
            status=status,
        ).count()
        for status in (
            ComplaintStatus.ASSIGNED,
            ComplaintStatus.IN_PROGRESS,
            ComplaintStatus.RESOLVED,
            ComplaintStatus.CLOSED,
        )
    }

    return {
        "success": True,
        "dashboard": {
            "assigned": status_counts[ComplaintStatus.ASSIGNED],
            "inProgress": status_counts[ComplaintStatus.IN_PROGRESS],
            "resolved": status_counts[ComplaintStatus.RESOLVED],
            "closed": status_counts[ComplaintStatus.CLOSED],
        },
    }, 200


def get_history():
    user_id = int(get_jwt_identity())

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    status = request.args.get("status", type=str)

    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)

    query = Complaint.query.filter(
        Complaint.assigned_staff_id == user_id,
        Complaint.status.in_(
            [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]
        ),
    )

    if status:
        try:
            status_enum = ComplaintStatus(status)
        except ValueError:
            return {
                "success": False,
                "message": "Invalid status filter.",
            }, 400

        if status_enum not in {ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED}:
            return {
                "success": False,
                "message": "History only includes RESOLVED or CLOSED complaints.",
            }, 400

        query = query.filter(Complaint.status == status_enum)

    query = query.order_by(Complaint.resolved_at.desc().nullslast())

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "success": True,
        "history": [
            _complaint_response(complaint)
            for complaint in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    }, 200


def add_timeline_update(complaint_id: int):
    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    comment = json_data.get("comment", "").strip()

    if not comment:
        return {
            "success": False,
            "message": "Comment is required.",
        }, 400

    user_id = int(get_jwt_identity())
    complaint = Complaint.query.get(complaint_id)

    if not complaint:
        return {
            "success": False,
            "message": "Complaint not found.",
        }, 404

    if complaint.assigned_staff_id != user_id:
        return {
            "success": False,
            "message": "This complaint is not assigned to you.",
        }, 403

    if complaint.status not in {ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS}:
        return {
            "success": False,
            "message": "Completed or unassigned complaints are read-only for staff.",
        }, 400

    try:
        update = _add_timeline_entry(
            complaint=complaint,
            user_id=user_id,
            status=complaint.status.value,
            comment=comment,
        )

        _notify_comment_participants(complaint, user, comment)

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to add timeline update.",
        }, 500

    return {
        "success": True,
        "message": "Timeline update added successfully.",
        "update": _timeline_response(update),
    }, 201
