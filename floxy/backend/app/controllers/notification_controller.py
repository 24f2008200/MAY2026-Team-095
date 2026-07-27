from typing import Any

from app.services.notification_service import (
    get_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)


def list_notifications_handler() -> tuple[dict[str, Any], int]:
    return get_notifications()


def mark_read_handler(notification_id: int) -> tuple[dict[str, Any], int]:
    return mark_notification_read(notification_id)


def mark_all_read_handler() -> tuple[dict[str, Any], int]:
    return mark_all_notifications_read()
