import os
import uuid
from datetime import date, datetime, time, timezone

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.attachment import Attachment
from app.models.category import Category
from app.models.complaint import (
    Complaint,
    ComplaintPriority,
    ComplaintStatus,
)
from app.models.complaint_update import ComplaintUpdate
from app.models.feedback import Feedback
from app.models.user import User, UserRole
from app.schemas.complaint_schema import (
    ComplaintTimelineSchema,
    CreateComplaintSchema,
    UpdateComplaintSchema,
)
from app.schemas.feedback_schema import FeedbackSchema
from app.services.notification_service import create_notification

create_complaint_schema = CreateComplaintSchema()
update_complaint_schema = UpdateComplaintSchema()
timeline_schema = ComplaintTimelineSchema()
feedback_schema = FeedbackSchema()

RESIDENT_EDITABLE_STATUSES = {
    ComplaintStatus.OPEN,
    ComplaintStatus.REOPENED,
}

ACTIVE_COMPLAINT_STATUSES = {
    ComplaintStatus.OPEN,
    ComplaintStatus.REOPENED,
    ComplaintStatus.ASSIGNED,
    ComplaintStatus.IN_PROGRESS,
}

REOPENABLE_COMPLAINT_STATUSES = {
    ComplaintStatus.RESOLVED,
    ComplaintStatus.CLOSED,
}

CLOSEABLE_COMPLAINT_STATUSES = ACTIVE_COMPLAINT_STATUSES | {ComplaintStatus.RESOLVED}


def _current_user_id() -> int:
    return int(get_jwt_identity())


def _current_user_role() -> str:
    user = _get_user(_current_user_id())
    return user.role.value if user else ""


def _get_user(user_id: int) -> User | None:
    return User.query.get(user_id)


def _parse_date_bound(raw_value: str | None, *, end_of_day: bool = False) -> datetime | None:
    """Parse an ISO date/datetime query value into the DB's naive UTC format."""
    value = (raw_value or "").strip()
    if not value:
        return None

    try:
        if len(value) == 10:
            parsed_date = date.fromisoformat(value)
            return datetime.combine(parsed_date, time.max if end_of_day else time.min)

        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        raise ValueError("Date filters must use YYYY-MM-DD or a valid ISO datetime.")


def _generate_complaint_code() -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"CMP-{year}-"

    last_complaint = (
        Complaint.query
        .filter(Complaint.complaint_code.like(f"{prefix}%"))
        .order_by(Complaint.id.desc())
        .first()
    )

    if last_complaint:
        last_number = int(last_complaint.complaint_code.split("-")[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    return f"{prefix}{next_number:06d}"


def _user_summary(user: User | None) -> dict | None:
    if not user:
        return None

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "flat_number": user.flat_number,
        "building": user.building,
        "trade": user.trade,
    }


def _attachment_response(attachment: Attachment) -> dict:
    filename = os.path.basename(attachment.file_path) if attachment.file_path else None
    return {
        "id": attachment.id,
        "complaint_id": attachment.complaint_id,
        "uploaded_by": attachment.uploaded_by,
        "file_name": attachment.file_name,
        "file_path": attachment.file_path,
        "file_type": attachment.file_type,
        "file_size": attachment.file_size,

        "url": f"/uploads/{filename}" if filename else None,
        "created_at": (
            attachment.created_at.isoformat()
            if attachment.created_at
            else None
        ),
    }


def _feedback_response(feedback: Feedback) -> dict:
    return {
        "id": feedback.id,
        "complaint_id": feedback.complaint_id,
        "resident_id": feedback.resident_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "created_at": (
            feedback.created_at.isoformat()
            if feedback.created_at
            else None
        ),
    }


def _timeline_response(update: ComplaintUpdate) -> dict:
    data = update.to_dict()
    data["updated_by_user"] = _user_summary(update.updated_by_user)
    return data


def _complaint_response(
    complaint: Complaint,
    include_timeline: bool = False,
) -> dict:
    data = complaint.to_dict()
    data["category"] = (
        complaint.category.to_dict()
        if complaint.category
        else None
    )
    data["resident"] = _user_summary(complaint.resident)
    data["assigned_staff"] = _user_summary(complaint.assigned_staff)
    data["attachments"] = [
        _attachment_response(attachment)
        for attachment in complaint.attachments
    ]
    data["feedback"] = (
        _feedback_response(complaint.feedback)
        if complaint.feedback
        else None
    )

    if include_timeline:
        data["timeline"] = [
            _timeline_response(update)
            for update in sorted(
                complaint.updates,
                key=lambda item: item.created_at or datetime.min,
            )
        ]

    return data


def _can_view_complaint(user: User, complaint: Complaint) -> bool:
    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.RESIDENT:
        return complaint.resident_id == user.id

    if user.role == UserRole.STAFF:
        return complaint.assigned_staff_id == user.id

    return False


def _can_upload_attachment(user: User, complaint: Complaint) -> bool:
    # Resolved/closed tickets are read-only. A resident must reopen the
    # complaint before new evidence can be added.
    if complaint.status not in ACTIVE_COMPLAINT_STATUSES:
        return False

    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.RESIDENT:
        return complaint.resident_id == user.id

    if user.role == UserRole.STAFF:
        return (
            complaint.assigned_staff_id == user.id
            and complaint.status in {
                ComplaintStatus.ASSIGNED,
                ComplaintStatus.IN_PROGRESS,
            }
        )

    return False


def _can_comment_on_complaint(user: User, complaint: Complaint) -> bool:
    # Keep completed complaints auditable: their timeline can be viewed but
    # not mutated. Reopening makes the discussion active again.
    if complaint.status not in ACTIVE_COMPLAINT_STATUSES:
        return False

    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.RESIDENT:
        return complaint.resident_id == user.id

    if user.role == UserRole.STAFF:
        return (
            complaint.assigned_staff_id == user.id
            and complaint.status in {
                ComplaintStatus.ASSIGNED,
                ComplaintStatus.IN_PROGRESS,
            }
        )

    return False


def _notify_admins(
    title: str,
    message: str,
    complaint_id: int,
    notification_type: str = "COMPLAINT_CREATED",
):
    admins = User.query.filter_by(
        role=UserRole.ADMIN,
        is_active=True,
    ).all()

    for admin in admins:
        create_notification(
            user_id=admin.id,
            complaint_id=complaint_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )


def _notify_comment_participants(complaint: Complaint, actor: User, comment: str):
    """Notify every other active participant in a complaint discussion.

    The discussion is shared by the resident, the currently assigned staff
    member, and administrators. This keeps staff/admin/resident chat symmetric
    instead of notifying only the resident for staff/admin messages.
    """
    recipient_ids: set[int] = {complaint.resident_id}

    if complaint.assigned_staff_id:
        recipient_ids.add(complaint.assigned_staff_id)

    admin_ids = (
        db.session.query(User.id)
        .filter(User.role == UserRole.ADMIN, User.is_active.is_(True))
        .all()
    )
    recipient_ids.update(row[0] for row in admin_ids)
    recipient_ids.discard(actor.id)

    for recipient_id in recipient_ids:
        create_notification(
            user_id=recipient_id,
            complaint_id=complaint.id,
            title="Complaint Message",
            message=(
                f"{actor.name} posted on {complaint.complaint_code}: {comment}"
            ),
            notification_type="TIMELINE_UPDATE",
        )


def _add_timeline_entry(
    complaint: Complaint,
    user_id: int,
    status: str,
    comment: str | None = None,
):
    update = ComplaintUpdate(
        complaint_id=complaint.id,
        updated_by=user_id,
        status=status,
        comment=comment,
    )
    db.session.add(update)
    return update


def _allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    allowed = current_app.config.get(
        "ALLOWED_EXTENSIONS",
        {"png", "jpg", "jpeg", "gif", "pdf"},
    )
    return extension in allowed


def create_complaint():
    if _current_user_role() != UserRole.RESIDENT.value:
        return {
            "success": False,
            "message": "Only residents can create complaints.",
        }, 403

    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    try:
        data = create_complaint_schema.load(json_data)
    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages,
        }, 400

    category = Category.query.filter_by(
        id=data["category_id"],
        is_active=True,
    ).first()

    if not category:
        return {
            "success": False,
            "message": "Invalid or inactive category.",
        }, 400

    user_id = _current_user_id()
    complaint_code = _generate_complaint_code()

    complaint = Complaint(
        complaint_code=complaint_code,
        resident_id=user_id,
        category_id=data["category_id"],
        title=data["title"],
        description=data["description"],
        location=data["location"],
        priority=ComplaintPriority(data["priority"]),
        status=ComplaintStatus.OPEN,
    )

    try:
        db.session.add(complaint)
        db.session.flush()

        _add_timeline_entry(
            complaint=complaint,
            user_id=user_id,
            status=ComplaintStatus.OPEN.value,
            comment="Complaint created.",
        )

        _notify_admins(
            title="New Complaint Submitted",
            message=(
                f"Complaint {complaint.complaint_code}: "
                f"{complaint.title}"
            ),
            complaint_id=complaint.id,
        )

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to create complaint.",
        }, 500

    return {
        "success": True,
        "message": "Complaint created successfully.",
        "complaint": _complaint_response(complaint),
    }, 201


def get_all_complaints():
    user = _get_user(_current_user_id())

    if not user:
        return {
            "success": False,
            "message": "User not found.",
        }, 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    status = request.args.get("status", type=str)
    priority = request.args.get("priority", type=str)
    category_id = request.args.get("category_id", type=int)
    search = request.args.get("search", type=str)
    date_from_raw = request.args.get("date_from", type=str)
    date_to_raw = request.args.get("date_to", type=str)
    sort = (request.args.get("sort", "newest", type=str) or "newest").lower()

    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)

    try:
        date_from = _parse_date_bound(date_from_raw, end_of_day=False)
        date_to = _parse_date_bound(date_to_raw, end_of_day=True)
    except ValueError as exc:
        return {"success": False, "message": str(exc)}, 400

    if date_from and date_to and date_from > date_to:
        return {
            "success": False,
            "message": "The start date cannot be after the end date.",
        }, 400

    if sort not in {"newest", "oldest"}:
        return {
            "success": False,
            "message": "Sort must be either 'newest' or 'oldest'.",
        }, 400

    query = Complaint.query

    if user.role == UserRole.RESIDENT:
        query = query.filter_by(resident_id=user.id)
    elif user.role == UserRole.STAFF:
        # The live staff queue only contains work currently assigned to this
        # technician. Completed jobs belong in /staff/complaints/history.
        query = query.filter(
            Complaint.assigned_staff_id == user.id,
            Complaint.status.in_([
                ComplaintStatus.ASSIGNED,
                ComplaintStatus.IN_PROGRESS,
            ]),
        )
    elif user.role != UserRole.ADMIN:
        return {
            "success": False,
            "message": "You are not authorized to access this resource.",
        }, 403

    if status:
        try:
            query = query.filter_by(status=ComplaintStatus(status))
        except ValueError:
            return {
                "success": False,
                "message": "Invalid status filter.",
            }, 400

    if priority:
        try:
            query = query.filter_by(priority=ComplaintPriority(priority))
        except ValueError:
            return {
                "success": False,
                "message": "Invalid priority filter.",
            }, 400

    if category_id:
        query = query.filter_by(category_id=category_id)

    if date_from:
        query = query.filter(Complaint.created_at >= date_from)

    if date_to:
        query = query.filter(Complaint.created_at <= date_to)

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            db.or_(
                Complaint.title.ilike(search_term),
                Complaint.description.ilike(search_term),
                Complaint.complaint_code.ilike(search_term),
                Complaint.location.ilike(search_term),
                Complaint.resident.has(User.name.ilike(search_term)),
                Complaint.resident.has(User.email.ilike(search_term)),
                Complaint.resident.has(User.mobile_number.ilike(search_term)),
                Complaint.resident.has(User.flat_number.ilike(search_term)),
                Complaint.resident.has(User.building.ilike(search_term)),
                Complaint.assigned_staff.has(User.name.ilike(search_term)),
                Complaint.assigned_staff.has(User.email.ilike(search_term)),
                Complaint.assigned_staff.has(User.trade.ilike(search_term)),
                Complaint.category.has(Category.name.ilike(search_term)),
            )
        )

    query = query.order_by(
        Complaint.created_at.asc() if sort == "oldest" else Complaint.created_at.desc()
    )

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "success": True,
        "complaints": [
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


def get_complaint(complaint_id: int):
    user = _get_user(_current_user_id())

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

    if not _can_view_complaint(user, complaint):
        return {
            "success": False,
            "message": "You are not authorized to view this complaint.",
        }, 403

    return {
        "success": True,
        "complaint": _complaint_response(
            complaint,
            include_timeline=True,
        ),
    }, 200


def update_complaint(complaint_id: int):
    if _current_user_role() != UserRole.RESIDENT.value:
        return {
            "success": False,
            "message": "Only residents can update complaint details.",
        }, 403

    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    try:
        data = update_complaint_schema.load(json_data)
    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages,
        }, 400

    if not data:
        return {
            "success": False,
            "message": "At least one field is required to update.",
        }, 400

    user_id = _current_user_id()
    complaint = Complaint.query.get(complaint_id)

    if not complaint:
        return {
            "success": False,
            "message": "Complaint not found.",
        }, 404

    if complaint.resident_id != user_id:
        return {
            "success": False,
            "message": "You are not authorized to update this complaint.",
        }, 403

    if complaint.status not in RESIDENT_EDITABLE_STATUSES:
        return {
            "success": False,
            "message": (
                "Complaint can only be updated when status is "
                "OPEN or REOPENED."
            ),
        }, 400

    if "title" in data:
        complaint.title = data["title"]
    if "description" in data:
        complaint.description = data["description"]
    if "location" in data:
        complaint.location = data["location"]
    if "priority" in data:
        complaint.priority = ComplaintPriority(data["priority"])

    try:
        _add_timeline_entry(
            complaint=complaint,
            user_id=user_id,
            status=complaint.status.value,
            comment="Complaint details updated by resident.",
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to update complaint.",
        }, 500

    return {
        "success": True,
        "message": "Complaint updated successfully.",
        "complaint": _complaint_response(complaint),
    }, 200


def get_timeline(complaint_id: int):
    user = _get_user(_current_user_id())

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

    if not _can_view_complaint(user, complaint):
        return {
            "success": False,
            "message": "You are not authorized to view this timeline.",
        }, 403

    timeline = sorted(
        complaint.updates,
        key=lambda item: item.created_at or datetime.min,
    )

    return {
        "success": True,
        "complaint_id": complaint.id,
        "complaint_code": complaint.complaint_code,
        "timeline": [_timeline_response(item) for item in timeline],
    }, 200


def add_timeline_comment(complaint_id: int):
    user = _get_user(_current_user_id())

    if not user:
        return {
            "success": False,
            "message": "User not found.",
        }, 404

    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    comment = (json_data.get("comment") or "").strip()

    if not comment:
        return {
            "success": False,
            "message": "Comment is required.",
        }, 400

    complaint = Complaint.query.get(complaint_id)

    if not complaint:
        return {
            "success": False,
            "message": "Complaint not found.",
        }, 404

    if not _can_view_complaint(user, complaint):
        return {
            "success": False,
            "message": "You are not authorized to comment on this complaint.",
        }, 403

    if not _can_comment_on_complaint(user, complaint):
        return {
            "success": False,
            "message": (
                "This complaint is read-only because it has been resolved or closed. "
                "The resident can reopen it if the issue still needs attention."
            ),
        }, 400

    try:
        update = _add_timeline_entry(
            complaint=complaint,
            user_id=user.id,
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
        "message": "Comment added successfully.",
        "update": _timeline_response(update),
    }, 201


def upload_attachment(complaint_id: int):
    user = _get_user(_current_user_id())

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

    if not _can_upload_attachment(user, complaint):
        return {
            "success": False,
            "message": "You are not authorized to upload attachments.",
        }, 403

    if "file" not in request.files:
        return {
            "success": False,
            "message": "No file provided.",
        }, 400

    file = request.files["file"]

    if not file or not file.filename:
        return {
            "success": False,
            "message": "No file selected.",
        }, 400

    if not _allowed_file(file.filename):
        return {
            "success": False,
            "message": "File type not allowed.",
        }, 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = os.path.join(upload_folder, unique_name)

    try:
        file.save(file_path)
        file_size = os.path.getsize(file_path)
    except OSError:
        return {
            "success": False,
            "message": "Unable to save file.",
        }, 500

    attachment = Attachment(
        complaint_id=complaint.id,
        uploaded_by=user.id,
        file_name=original_name,
        file_path=unique_name,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
    )

    try:
        db.session.add(attachment)
        _add_timeline_entry(
            complaint=complaint,
            user_id=user.id,
            status=complaint.status.value,
            comment=f"Attachment uploaded: {original_name}",
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        return {
            "success": False,
            "message": "Unable to save attachment record.",
        }, 500

    return {
        "success": True,
        "message": "Attachment uploaded successfully.",
        "attachment": _attachment_response(attachment),
    }, 201


def submit_feedback(complaint_id: int):
    if _current_user_role() != UserRole.RESIDENT.value:
        return {
            "success": False,
            "message": "Only residents can submit feedback.",
        }, 403

    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    try:
        data = feedback_schema.load(json_data)
    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages,
        }, 400

    user_id = _current_user_id()
    complaint = Complaint.query.get(complaint_id)

    if not complaint:
        return {
            "success": False,
            "message": "Complaint not found.",
        }, 404

    if complaint.resident_id != user_id:
        return {
            "success": False,
            "message": "You are not authorized to submit feedback.",
        }, 403

    if complaint.status not in {
        ComplaintStatus.RESOLVED,
        ComplaintStatus.CLOSED,
    }:
        return {
            "success": False,
            "message": (
                "Feedback can only be submitted for resolved "
                "or closed complaints."
            ),
        }, 400

    if complaint.feedback:
        # Allow updating existing feedback for the same resident
        if complaint.feedback.resident_id != user_id:
            return {
                "success": False,
                "message": "Feedback already submitted by another resident.",
            }, 409
        # Update existing feedback
        try:
            complaint.feedback.rating = data["rating"]
            complaint.feedback.comment = data.get("comment")
            db.session.commit()
            return {
                "success": True,
                "message": "Feedback updated successfully.",
                "feedback": _feedback_response(complaint.feedback),
                "complaint": _complaint_response(complaint),
            }, 200
        except Exception:
            db.session.rollback()
            return {
                "success": False,
                "message": "Unable to update feedback.",
            }, 500

    feedback = Feedback(
        complaint_id=complaint.id,
        resident_id=user_id,
        rating=data["rating"],
        comment=data.get("comment"),
    )

    try:
        db.session.add(feedback)

        if complaint.status == ComplaintStatus.RESOLVED:
            complaint.status = ComplaintStatus.CLOSED
            complaint.closed_at = datetime.now(timezone.utc)
        elif complaint.status == ComplaintStatus.CLOSED and complaint.closed_at is None:
            # Backward-compatible safeguard for legacy rows created before
            # closed_at existed.
            complaint.closed_at = datetime.now(timezone.utc)

        _add_timeline_entry(
            complaint=complaint,
            user_id=user_id,
            status=complaint.status.value,
            comment=f"Feedback submitted with rating {data['rating']}.",
        )

        create_notification(
            user_id=complaint.resident_id,
            complaint_id=complaint.id,
            title="Feedback Recorded",
            message=(
                f"Thank you for your feedback on "
                f"{complaint.complaint_code}."
            ),
            notification_type="FEEDBACK_SUBMITTED",
        )

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to submit feedback.",
        }, 500

    return {
        "success": True,
        "message": "Feedback submitted successfully.",
        "feedback": _feedback_response(feedback),
        "complaint": _complaint_response(complaint),
    }, 201


def close_complaint(complaint_id: int):
    """Close an active complaint. Only an admin or the owning resident may do so."""
    user = _get_user(_current_user_id())

    if not user:
        return {"success": False, "message": "User not found."}, 404

    complaint = Complaint.query.get(complaint_id)

    if not complaint:
        return {"success": False, "message": "Complaint not found."}, 404

    if user.role not in {UserRole.ADMIN, UserRole.RESIDENT}:
        return {
            "success": False,
            "message": "Only an administrator or the resident who created this complaint can close it.",
        }, 403

    if user.role == UserRole.RESIDENT and complaint.resident_id != user.id:
        return {
            "success": False,
            "message": "You can only close your own complaints.",
        }, 403

    if complaint.status not in CLOSEABLE_COMPLAINT_STATUSES:
        return {
            "success": False,
            "message": "Only active or resolved complaints can be closed.",
        }, 400

    complaint.status = ComplaintStatus.CLOSED
    complaint.closed_at = datetime.now(timezone.utc)

    try:
        _add_timeline_entry(
            complaint=complaint,
            user_id=user.id,
            status=ComplaintStatus.CLOSED.value,
            comment=f"Ticket closed by {user.name}.",
        )

        # Inform the resident when management closes the case.
        if user.role == UserRole.ADMIN:
            create_notification(
                user_id=complaint.resident_id,
                complaint_id=complaint.id,
                title="Complaint Closed",
                message=f"Complaint {complaint.complaint_code} was closed by management.",
                notification_type="COMPLAINT_CLOSED",
            )
        else:
            _notify_admins(
                title="Complaint Closed by Resident",
                message=(
                    f"{user.name} closed complaint {complaint.complaint_code}."
                ),
                complaint_id=complaint.id,
                notification_type="COMPLAINT_CLOSED",
            )

        # A technician should not discover that a job disappeared only by
        # refreshing their queue. Notify the current assignee when applicable.
        if complaint.assigned_staff_id and complaint.assigned_staff_id != user.id:
            create_notification(
                user_id=complaint.assigned_staff_id,
                complaint_id=complaint.id,
                title="Complaint Closed",
                message=(
                    f"Complaint {complaint.complaint_code} was closed by "
                    f"{user.name} and has left your active queue."
                ),
                notification_type="COMPLAINT_CLOSED",
            )

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "message": "Unable to close complaint."}, 500

    return {
        "success": True,
        "message": "Complaint closed successfully.",
        "complaint": _complaint_response(complaint),
    }, 200


def reopen_complaint(complaint_id: int):
    """
    Reopen a RESOLVED/CLOSED complaint within seven days. Reopening returns
    the case to admin triage and deliberately removes the previous technician
    assignment so staff cannot keep accessing a newly reopened complaint.
    """
    user = _get_user(_current_user_id())

    if not user:
        return {"success": False, "message": "User not found."}, 404

    complaint = Complaint.query.get(complaint_id)

    if not complaint:
        return {"success": False, "message": "Complaint not found."}, 404

    if user.role != UserRole.RESIDENT:
        return {
            "success": False,
            "message": "Only the resident who created this complaint can reopen it.",
        }, 403

    if complaint.resident_id != user.id:
        return {
            "success": False,
            "message": "You can only reopen your own complaints.",
        }, 403

    if complaint.status not in REOPENABLE_COMPLAINT_STATUSES:
        return {
            "success": False,
            "message": "Only RESOLVED or CLOSED complaints can be reopened.",
        }, 400

    # Feedback is the resident's acceptance of the completed work. Once it is
    # submitted, the case is final instead of entering a contradictory
    # REOPENED + feedback state.
    if complaint.feedback:
        return {
            "success": False,
            "message": "This complaint cannot be reopened after feedback has been submitted.",
        }, 400

    reference_time = (
        complaint.closed_at
        if complaint.status == ComplaintStatus.CLOSED
        else complaint.resolved_at
    )
    # Legacy CLOSED rows may predate the closed_at column; old versions used
    # resolved_at as both timestamps, so keep that as a fallback.
    if reference_time is None and complaint.status == ComplaintStatus.CLOSED:
        reference_time = complaint.resolved_at

    if reference_time is None:
        return {
            "success": False,
            "message": "Cannot reopen this complaint because no resolution/closure time was recorded.",
        }, 400

    now = datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    if (now - reference_time).total_seconds() > 7 * 24 * 60 * 60:
        return {
            "success": False,
            "message": "Complaint can only be reopened within 7 days of resolution or closure.",
        }, 400

    previous_staff_id = complaint.assigned_staff_id
    complaint.status = ComplaintStatus.REOPENED
    complaint.assigned_staff_id = None
    complaint.resolved_at = None
    complaint.closed_at = None

    try:
        _add_timeline_entry(
            complaint=complaint,
            user_id=user.id,
            status=ComplaintStatus.REOPENED.value,
            comment=f"Ticket reopened by {user.name}; returned to admin triage for reassignment.",
        )

        _notify_admins(
            title="Complaint Reopened",
            message=(
                f"Complaint {complaint.complaint_code} was reopened by {user.name} "
                "and needs to be assigned again."
            ),
            complaint_id=complaint.id,
            notification_type="COMPLAINT_REOPENED",
        )

        if previous_staff_id:
            create_notification(
                user_id=previous_staff_id,
                complaint_id=complaint.id,
                title="Complaint Returned to Triage",
                message=(
                    f"Complaint {complaint.complaint_code} was reopened by the resident. "
                    "It has been removed from your queue pending a new admin assignment."
                ),
                notification_type="COMPLAINT_REOPENED",
            )

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "message": "Unable to reopen complaint."}, 500

    return {
        "success": True,
        "message": "Complaint reopened and returned to admin triage.",
        "complaint": _complaint_response(complaint),
    }, 200

