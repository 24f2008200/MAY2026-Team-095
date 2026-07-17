from typing import Any

from app.services.admin_service import (
    assign_staff,
    create_category,
    get_dashboard,
    get_reports,
    list_staff,
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
