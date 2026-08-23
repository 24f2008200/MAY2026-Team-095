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
    _parse_date_bound,
)
from app.services.notification_service import create_notification


class AssignStaffSchema(Schema):
    staff_id = fields.Integer(required=True, strict=True)
    remarks = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )


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

    if complaint.status not in {
        ComplaintStatus.OPEN,
        ComplaintStatus.REOPENED,
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.IN_PROGRESS,
    }:
        return {
            "success": False,
            "message": "Only active complaints can be assigned or reassigned.",
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

    previous_staff = complaint.assigned_staff

    if previous_staff and previous_staff.id == staff.id and complaint.status in {
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.IN_PROGRESS,
    }:
        return {
            "success": False,
            "message": f"This complaint is already assigned to {staff.name}.",
        }, 400

    remarks = (data.get("remarks") or "").strip()
    was_reassignment = previous_staff is not None

    complaint.assigned_staff_id = staff.id
    complaint.status = ComplaintStatus.ASSIGNED
    complaint.resolved_at = None
    complaint.closed_at = None

    assignment_comment = (
        f"Reassigned from {previous_staff.name} to {staff.name}."
        if was_reassignment
        else f"Assigned to staff: {staff.name}."
    )
    if remarks:
        assignment_comment += f" Instructions: {remarks}"

    try:
        _add_timeline_entry(
            complaint=complaint,
            user_id=admin_id,
            status=ComplaintStatus.ASSIGNED.value,
            comment=assignment_comment,
        )

        if previous_staff and previous_staff.id != staff.id:
            create_notification(
                user_id=previous_staff.id,
                complaint_id=complaint.id,
                title="Complaint Reassigned",
                message=(
                    f"Complaint {complaint.complaint_code} has been reassigned "
                    f"to {staff.name} and is no longer in your active queue."
                ),
                notification_type="COMPLAINT_REASSIGNED",
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
        "message": "Staff reassigned successfully." if was_reassignment else "Staff assigned successfully.",
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
    rating_rows = (
        db.session.query(Feedback.rating, func.count(Feedback.id))
        .group_by(Feedback.rating)
        .all()
    )
    rating_distribution = {str(star): 0 for star in range(1, 6)}
    for rating, count in rating_rows:
        rating_distribution[str(rating)] = count

    feedback_eligible = Complaint.query.filter(
        Complaint.status.in_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])
    ).count()
    review_rate = (
        round((feedback_count / feedback_eligible) * 100, 1)
        if feedback_eligible
        else 0.0
    )

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
                "rating_distribution": rating_distribution,
                "eligible_complaints": feedback_eligible,
                "review_rate_percent": review_rate,
            },
            "status_overview": {
                status.value: Complaint.query.filter_by(status=status).count()
                for status in ComplaintStatus
            },
        },
    }, 200


def list_reviews():
    """Paginated admin view of resident reviews across all complaints."""
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    rating = request.args.get("rating", type=int)
    date_from_raw = request.args.get("date_from", type=str)
    date_to_raw = request.args.get("date_to", type=str)

    if rating is not None and rating not in {1, 2, 3, 4, 5}:
        return {"success": False, "message": "Rating must be between 1 and 5."}, 400

    try:
        date_from = _parse_date_bound(date_from_raw, end_of_day=False)
        date_to = _parse_date_bound(date_to_raw, end_of_day=True)
    except ValueError as exc:
        return {"success": False, "message": str(exc)}, 400

    if date_from and date_to and date_from > date_to:
        return {"success": False, "message": "The start date cannot be after the end date."}, 400

    query = Feedback.query
    if rating is not None:
        query = query.filter(Feedback.rating == rating)
    if date_from:
        query = query.filter(Feedback.created_at >= date_from)
    if date_to:
        query = query.filter(Feedback.created_at <= date_to)

    pagination = query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    reviews = []
    for feedback in pagination.items:
        complaint = feedback.complaint
        reviews.append({
            "id": feedback.id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
            "resident": {
                "id": feedback.resident.id,
                "name": feedback.resident.name,
                "flat_number": feedback.resident.flat_number,
                "building": feedback.resident.building,
            } if feedback.resident else None,
            "complaint": {
                "id": complaint.id,
                "complaint_code": complaint.complaint_code,
                "title": complaint.title,
                "priority": complaint.priority.value,
                "status": complaint.status.value,
                "category": complaint.category.name if complaint.category else None,
                "assigned_staff": complaint.assigned_staff.name if complaint.assigned_staff else None,
            } if complaint else None,
        })

    return {
        "success": True,
        "reviews": reviews,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    }, 200


def _extract_trade(member: User) -> str:
    """Return the staff member's maintenance expertise."""
    return member.trade or "General"


def list_staff():
    """Return active staff with workload and resident-review performance metrics."""
    trade = request.args.get("trade", type=str)

    query = User.query.filter_by(role=UserRole.STAFF, is_active=True)

    if trade:
        query = query.filter(User.trade == trade)

    staff_members = query.order_by(User.name.asc()).all()
    staff_rows = []

    for member in staff_members:
        active_count = Complaint.query.filter(
            Complaint.assigned_staff_id == member.id,
            Complaint.status.in_([
                ComplaintStatus.ASSIGNED,
                ComplaintStatus.IN_PROGRESS,
            ]),
        ).count()

        completed_count = Complaint.query.filter(
            Complaint.assigned_staff_id == member.id,
            Complaint.status.in_([
                ComplaintStatus.RESOLVED,
                ComplaintStatus.CLOSED,
            ]),
        ).count()

        review_count, average_rating = (
            db.session.query(
                func.count(Feedback.id),
                func.avg(Feedback.rating),
            )
            .join(Complaint, Feedback.complaint_id == Complaint.id)
            .filter(Complaint.assigned_staff_id == member.id)
            .first()
        )

        five_star_reviews = (
            db.session.query(func.count(Feedback.id))
            .join(Complaint, Feedback.complaint_id == Complaint.id)
            .filter(
                Complaint.assigned_staff_id == member.id,
                Feedback.rating == 5,
            )
            .scalar()
            or 0
        )

        staff_rows.append({
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "mobile_number": member.mobile_number,
            "flat_number": member.flat_number,
            "building": member.building,
            "trade": _extract_trade(member),
            "username": member.email.split("@")[0] if member.email else member.name,
            "is_active": bool(member.is_active),
            "assigned_complaints_count": active_count,
            "completed_complaints_count": completed_count,
            "review_count": int(review_count or 0),
            "average_rating": (
                round(float(average_rating), 2)
                if average_rating is not None
                else None
            ),
            "five_star_reviews": int(five_star_reviews),
        })

    # Rank only technicians who have at least one resident review. New/unrated
    # staff remain fully assignable; they simply show as "Unrated" until a
    # resident reviews completed work.
    ranked = sorted(
        (row for row in staff_rows if row["review_count"] > 0),
        key=lambda row: (
            -(row["average_rating"] or 0),
            -row["review_count"],
            -row["completed_complaints_count"],
            row["name"].lower(),
        ),
    )
    rank_by_id = {row["id"]: index for index, row in enumerate(ranked, start=1)}

    for row in staff_rows:
        row["performance_rank"] = rank_by_id.get(row["id"])

    return {
        "success": True,
        "staff": staff_rows,
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
        trade=trade,
        is_active=True,
    )


    try:
        db.session.add(new_staff)
        db.session.flush()

        create_notification(
            user_id=new_staff.id,
            complaint_id=None,
            title="Staff Account Created",
            message=f"Your maintenance staff account has been created. Your trade is: {trade}.",
            notification_type="STAFF_CREATED",
        )

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "message": "Unable to create staff account."}, 500

    return {
        "success": True,
        "message": "Staff account created successfully.",
        "staff": {
            "id": new_staff.id,
            "name": new_staff.name,
            "email": new_staff.email,
            "mobile_number": new_staff.mobile_number,
            "trade": new_staff.trade,
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

    # Return live work to admin triage before deactivating the technician.
    # Otherwise complaints remain assigned to an account that can no longer
    # sign in and effectively become stranded.
    active_complaints = Complaint.query.filter(
        Complaint.assigned_staff_id == staff.id,
        Complaint.status.in_([ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS]),
    ).all()

    for complaint in active_complaints:
        complaint.assigned_staff_id = None
        complaint.status = ComplaintStatus.OPEN
        complaint.resolved_at = None
        complaint.closed_at = None
        _add_timeline_entry(
            complaint=complaint,
            user_id=admin_id,
            status=ComplaintStatus.OPEN.value,
            comment=(
                f"{staff.name} was deactivated; complaint returned to admin "
                "triage for reassignment."
            ),
        )
        create_notification(
            user_id=complaint.resident_id,
            complaint_id=complaint.id,
            title="Complaint Awaiting Reassignment",
            message=(
                f"Complaint {complaint.complaint_code} is awaiting a new staff "
                "assignment because the previous technician is no longer active."
            ),
            notification_type="COMPLAINT_UNASSIGNED",
        )

    staff.is_active = False

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "message": "Unable to remove staff member."}, 500

    returned_count = len(active_complaints)
    suffix = (
        f" {returned_count} active complaint{'s' if returned_count != 1 else ''} "
        "returned to the unassigned queue."
        if returned_count
        else ""
    )
    return {
        "success": True,
        "message": f"Staff member '{staff.name}' has been deactivated.{suffix}",
        "returned_to_triage": returned_count,
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