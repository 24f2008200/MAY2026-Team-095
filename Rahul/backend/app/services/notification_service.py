from flask import request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.notification import Notification


def _notification_response(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "complaint_id": notification.complaint_id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type,
        "channel": notification.channel,
        "is_read": notification.is_read,
        "created_at": (
            notification.created_at.isoformat()
            if notification.created_at
            else None
        ),
    }


def create_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    complaint_id: int | None = None,
    channel: str = "IN_APP",
) -> Notification | None:
    notification = Notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title=title,
        message=message,
        type=notification_type,
        channel=channel,
        is_read=False,
    )

    try:
        db.session.add(notification)
        db.session.flush()
        return notification
    except IntegrityError:
        db.session.rollback()
        return None


def get_notifications():
    user_id = int(get_jwt_identity())

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    unread_only = request.args.get("unread_only", "false").lower() == "true"

    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)

    query = Notification.query.filter_by(user_id=user_id)

    if unread_only:
        query = query.filter_by(is_read=False)

    query = query.order_by(Notification.created_at.desc())

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    unread_count = Notification.query.filter_by(
        user_id=user_id,
        is_read=False,
    ).count()

    return {
        "success": True,
        "notifications": [
            _notification_response(item)
            for item in pagination.items
        ],
        "unread_count": unread_count,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    }, 200


def mark_notification_read(notification_id: int):
    user_id = int(get_jwt_identity())

    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id,
    ).first()

    if not notification:
        return {
            "success": False,
            "message": "Notification not found.",
        }, 404

    notification.is_read = True

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to update notification.",
        }, 500

    return {
        "success": True,
        "message": "Notification marked as read.",
        "notification": _notification_response(notification),
    }, 200


def mark_all_notifications_read():
    user_id = int(get_jwt_identity())

    try:
        Notification.query.filter_by(
            user_id=user_id,
            is_read=False,
        ).update({"is_read": True})

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to update notifications.",
        }, 500

    return {
        "success": True,
        "message": "All notifications marked as read.",
    }, 200
