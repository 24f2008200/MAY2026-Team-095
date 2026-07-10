"""
fake_data.py
------------
Builders for realistic-looking JSON payloads matching the schemas in
Smart Society Complaint Resolution System API (MAY2026-Team-095).
"""

import random
import uuid
from datetime import datetime, timedelta

CATEGORIES = [
    {"category": "Water Leakage", "subCategories": ["Tap Leakage", "Pipe Burst", "Overhead Tank"]},
    {"category": "Electrical", "subCategories": ["Power Outage", "Short Circuit", "Faulty Wiring"]},
    {"category": "Plumbing", "subCategories": ["Blocked Drain", "Low Water Pressure"]},
    {"category": "Cleanliness", "subCategories": ["Common Area", "Garbage Disposal"]},
    {"category": "Security", "subCategories": ["Gate Malfunction", "CCTV Issue", "Unauthorized Entry"]},
    {"category": "Parking", "subCategories": ["Unauthorized Vehicle", "Damaged Slot Marking"]},
    {"category": "Lift/Elevator", "subCategories": ["Not Working", "Stuck", "Noise"]},
]

STAFF_NAMES = ["Ramesh (Plumber)", "Suresh (Electrician)", "Anita (Housekeeping)", "Vikram (Security)"]
RESIDENT_NAMES = ["Mr. Abcde (B-101)", "Mrs Pqrst (A-204)", "Mr. Sharma (C-305)", "Ms. Iyer (D-102)"]
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Open", "Assigned", "In Progress", "Resolved", "Closed", "Reopened"]


def _now(offset_minutes: int = 0) -> str:
    return (datetime.utcnow() + timedelta(minutes=offset_minutes)).isoformat() + "Z"


def new_id(prefix: str) -> str:
    return f"{prefix}-{random.randint(1000, 9999)}"


def make_user(role: str = "Resident", name: str = None, email: str = None,
              mobile: str = None, flat: str = None) -> dict:
    return {
        "id": str(uuid.uuid4())[:8],
        "name": name or random.choice(RESIDENT_NAMES),
        "email": email or "user@example.com",
        "mobileNumber": mobile or "9876543210",
        "role": role,
        "flatNumber": flat or "B-101",
    }


def make_attachment() -> dict:
    fid = new_id("ATT")
    return {
        "id": fid,
        "url": f"https://cdn.smartsociety.example.com/attachments/{fid}.jpg",
        "filename": f"{fid}.jpg",
        "uploadedAt": _now(),
    }


def make_complaint_update(complaint_id: str, index: int = 0) -> dict:
    actions = ["Complaint registered", "Assigned to staff", "Started working",
               "Site visited", "Marked resolved"]
    action = actions[index % len(actions)]
    return {
        "id": new_id("U"),
        "complaintId": complaint_id,
        "timestamp": _now(offset_minutes=-30 * (5 - index)),
        "actor": random.choice(STAFF_NAMES + RESIDENT_NAMES),
        "action": action,
        "comment": f"{action}.",
    }


def make_complaint(complaint_id: str = None, **overrides) -> dict:
    complaint_id = complaint_id or new_id("C")
    cat = random.choice(CATEGORIES)
    status = overrides.get("status", random.choice(STATUSES))

    complaint = {
        "id": complaint_id,
        "category": overrides.get("category", cat["category"]),
        "subCategory": overrides.get("subCategory", random.choice(cat["subCategories"])),
        "priority": overrides.get("priority", random.choice(PRIORITIES)),
        "status": status,
        "location": overrides.get("location", "Bathroom / Lobby"),
        "description": overrides.get("description", "Reported by resident via mobile app."),
        "residentId": overrides.get("residentId", str(uuid.uuid4())[:8]),
        "residentName": overrides.get("residentName", random.choice(RESIDENT_NAMES)),
        "assignedStaffId": overrides.get("assignedStaffId"),
        "assignedStaffName": overrides.get("assignedStaffName"),
        "dateRaised": overrides.get("dateRaised", _now(offset_minutes=-120)),
        "dateResolved": overrides.get("dateResolved"),
        "attachments": overrides.get("attachments", [make_attachment()]),
        "rating": overrides.get("rating"),
        "feedbackComment": overrides.get("feedbackComment"),
    }

    if status in ("Assigned", "In Progress", "Resolved", "Closed"):
        complaint["assignedStaffId"] = complaint["assignedStaffId"] or str(uuid.uuid4())[:8]
        complaint["assignedStaffName"] = complaint["assignedStaffName"] or random.choice(STAFF_NAMES)

    if status in ("Resolved", "Closed"):
        complaint["dateResolved"] = complaint["dateResolved"] or _now()

    return complaint


def make_dashboard_summary() -> dict:
    total = random.randint(20, 60)
    resolved = random.randint(0, total)
    closed = random.randint(0, total - resolved)
    remaining = total - resolved - closed
    open_ = random.randint(0, remaining)
    assigned = random.randint(0, remaining - open_)
    in_progress = max(0, remaining - open_ - assigned)
    return {
        "total": total,
        "open": open_,
        "assigned": assigned,
        "inProgress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "pending": open_ + assigned + in_progress,
    }


def make_notification() -> dict:
    types = ["ComplaintRegistered", "ComplaintAssigned", "WorkStarted",
             "ComplaintResolved", "FeedbackRequest"]
    channels = ["Email", "SMS", "InApp"]
    ntype = random.choice(types)
    titles = {
        "ComplaintRegistered": "Complaint Registered",
        "ComplaintAssigned": "Complaint Assigned",
        "WorkStarted": "Work Started",
        "ComplaintResolved": "Complaint Resolved",
        "FeedbackRequest": "Please Rate Your Experience",
    }
    return {
        "id": new_id("N"),
        "complaintId": new_id("C"),
        "type": ntype,
        "title": titles[ntype],
        "message": f"{titles[ntype]} - please check your dashboard for details.",
        "channel": random.choice(channels),
        "read": random.choice([True, False]),
        "createdAt": _now(offset_minutes=-random.randint(1, 500)),
    }


def make_notification_settings() -> dict:
    return {
        "emailAlerts": True,
        "smsAlerts": True,
        "inAppAlerts": True,
        "complaintStatusUpdates": "All",
        "newAssignmentAlerts": "All",
        "marketingOptIn": False,
    }


def make_staff_notification_preferences() -> dict:
    return {
        "receiveViaEmail": True,
        "receiveViaSms": True,
        "receiveViaInApp": True,
        "quietHoursFrom": "11:00 PM",
        "quietHoursTo": "07:00 AM",
    }
