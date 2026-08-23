from typing import Any

from app.services.complaint_service import (
    add_timeline_comment,
    create_complaint,
    get_all_complaints,
    get_complaint,
    get_timeline,
    submit_feedback,
    update_complaint,
    upload_attachment,
    close_complaint,
    reopen_complaint,
)


def create_complaint_handler() -> tuple[dict[str, Any], int]:
    return create_complaint()


def list_complaints_handler() -> tuple[dict[str, Any], int]:
    return get_all_complaints()


def get_complaint_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return get_complaint(complaint_id)


def update_complaint_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return update_complaint(complaint_id)


def get_timeline_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return get_timeline(complaint_id)


def add_timeline_comment_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return add_timeline_comment(complaint_id)


def upload_attachment_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return upload_attachment(complaint_id)


def submit_feedback_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return submit_feedback(complaint_id)


def close_complaint_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return close_complaint(complaint_id)


def reopen_complaint_handler(complaint_id: int) -> tuple[dict[str, Any], int]:
    return reopen_complaint(complaint_id)
