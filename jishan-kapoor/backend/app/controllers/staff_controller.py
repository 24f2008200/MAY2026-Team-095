from typing import Any

from app.services.staff_service import (
    add_timeline_update,
    get_assigned_complaint,
    get_assigned_complaints,
    get_dashboard_summary,
    get_history,
    update_complaint_status,
)


def list_assigned_complaints_handler() -> tuple[dict[str, Any], int]:
    return get_assigned_complaints()


def get_assigned_complaint_handler(
    complaint_id: int,
) -> tuple[dict[str, Any], int]:
    return get_assigned_complaint(complaint_id)


def update_status_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return update_complaint_status(complaint_id)


def add_timeline_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return add_timeline_update(complaint_id)


def dashboard_summary_handler() -> tuple[dict[str, Any], int]:
    return get_dashboard_summary()


def history_handler() -> tuple[dict[str, Any], int]:
    return get_history()
