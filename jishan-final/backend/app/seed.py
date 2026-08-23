"""Idempotent starter data for a fresh Smart Society deployment."""

import os
import secrets
from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    Category,
    Complaint,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintUpdate,
    Feedback,
    Notification,
    User,
    UserRole,
)


def _utc_naive(days_ago: int, hours_ago: int = 0) -> datetime:
    """Return a SQLite-friendly UTC datetime."""
    return (
        datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)
    ).replace(tzinfo=None, microsecond=0)


def _demo_user(**values) -> User:
    # Demo people appear in reports and assignments but cannot be signed into
    # with a shared hard-coded credential.
    values["password_hash"] = generate_password_hash(secrets.token_urlsafe(32))
    return User(**values)


def _recovery_test_email() -> str:
    value = os.getenv("RECOVERY_TEST_EMAIL", "").strip().lower()
    return value if "@" in value else "emily.carter@example.com"


def _migrate_demo_identities() -> None:
    """Rename older demo identities without duplicating their linked records."""
    migrations = (
        ("+15550101001", "Emma Collins", "emma.collins@example.com"),
        ("+15550101002", "Oliver Turner", "oliver.turner@example.com"),
        ("+15550101003", "Amelia Parker", "amelia.parker@example.com"),
        ("+15550202001", "Emily Carter", _recovery_test_email()),
        ("+15550202002", "James Wilson", "james.wilson@example.com"),
        ("+15550202003", "Sophie Bennett", "sophie.bennett@example.com"),
        ("+15550202004", "Jack Thompson", "jack.thompson@example.com"),
    )
    changed = False
    for mobile_number, new_name, new_email in migrations:
        user = User.query.filter_by(mobile_number=mobile_number).first()
        if not user:
            continue

        if user.name != new_name:
            user.name = new_name
            changed = True
        email_owner = User.query.filter_by(email=new_email).first()
        if user.email != new_email and (not email_owner or email_owner.id == user.id):
            user.email = new_email
            changed = True

    if changed:
        db.session.commit()


def seed_demo_data() -> None:
    """Add realistic, non-sensitive example records exactly once."""
    _migrate_demo_identities()
    if Complaint.query.filter(Complaint.complaint_code.like("SSC-2026-%")).first():
        return

    admin = User.query.filter_by(role=UserRole.ADMIN, is_active=True).first()
    if not admin:
        return

    category_values = [
        ("Plumbing", "Leaks, drainage, water pressure and fixture repairs."),
        ("Electrical", "Lighting, outlets, breakers and common-area power."),
        ("Elevator", "Lift availability, controls, doors and safety checks."),
        ("Security & Access", "Entry gates, intercoms, keys and access cards."),
        ("Housekeeping", "Cleaning and upkeep of shared spaces."),
        ("HVAC", "Heating, ventilation and air-conditioning issues."),
        ("Waste Management", "Garbage, recycling and collection concerns."),
    ]
    categories = {}
    for name, description in category_values:
        category = Category.query.filter_by(name=name).first()
        if not category:
            category = Category(name=name, description=description, is_active=True)
            db.session.add(category)
        categories[name] = category

    staff_values = [
        dict(name="Emma Collins", email="emma.collins@example.com", mobile_number="+15550101001", trade="Plumbing", flat_number="STAFF-01", building="Maintenance", role=UserRole.STAFF),
        dict(name="Oliver Turner", email="oliver.turner@example.com", mobile_number="+15550101002", trade="Electrical", flat_number="STAFF-02", building="Maintenance", role=UserRole.STAFF),
        dict(name="Amelia Parker", email="amelia.parker@example.com", mobile_number="+15550101003", trade="Elevator & HVAC", flat_number="STAFF-03", building="Maintenance", role=UserRole.STAFF),
    ]
    resident_values = [
        dict(name="Emily Carter", email=_recovery_test_email(), mobile_number="+15550202001", flat_number="12B", building="Maple Tower", role=UserRole.RESIDENT),
        dict(name="James Wilson", email="james.wilson@example.com", mobile_number="+15550202002", flat_number="7A", building="Cedar House", role=UserRole.RESIDENT),
        dict(name="Sophie Bennett", email="sophie.bennett@example.com", mobile_number="+15550202003", flat_number="18C", building="Maple Tower", role=UserRole.RESIDENT),
        dict(name="Jack Thompson", email="jack.thompson@example.com", mobile_number="+15550202004", flat_number="4D", building="Oak Residence", role=UserRole.RESIDENT),
    ]

    users = {}
    for values in staff_values + resident_values:
        user = User.query.filter_by(email=values["email"]).first()
        if not user:
            user = _demo_user(**values, is_active=True)
            db.session.add(user)
        users[values["email"]] = user

    db.session.flush()

    complaints = [
        dict(
            complaint_code="SSC-2026-001",
            resident=users[_recovery_test_email()],
            assigned_staff=users["emma.collins@example.com"],
            category=categories["Plumbing"],
            title="Kitchen sink leak worsening",
            description="A steady leak below the kitchen sink is soaking the cabinet base. The shut-off valve is accessible.",
            location="Maple Tower · Unit 12B",
            priority=ComplaintPriority.URGENT,
            status=ComplaintStatus.IN_PROGRESS,
            created_at=_utc_naive(1, 5),
        ),
        dict(
            complaint_code="SSC-2026-002",
            resident=users["james.wilson@example.com"],
            assigned_staff=users["oliver.turner@example.com"],
            category=categories["Electrical"],
            title="Hallway light flickering",
            description="The light outside units 7A–7C flickers continuously after sunset and occasionally turns off.",
            location="Cedar House · Level 7 corridor",
            priority=ComplaintPriority.MEDIUM,
            status=ComplaintStatus.ASSIGNED,
            created_at=_utc_naive(2, 3),
        ),
        dict(
            complaint_code="SSC-2026-003",
            resident=users["sophie.bennett@example.com"],
            assigned_staff=users["amelia.parker@example.com"],
            category=categories["Elevator"],
            title="Elevator doors closing slowly",
            description="The east elevator pauses for several seconds before its doors close on the lobby level.",
            location="Maple Tower · East elevator",
            priority=ComplaintPriority.HIGH,
            status=ComplaintStatus.RESOLVED,
            created_at=_utc_naive(6),
            resolved_at=_utc_naive(2),
        ),
        dict(
            complaint_code="SSC-2026-004",
            resident=users["jack.thompson@example.com"],
            category=categories["Security & Access"],
            title="Parking gate not reading access card",
            description="The resident access card works at the lobby but is not detected by the north parking gate reader.",
            location="Oak Residence · North garage entrance",
            priority=ComplaintPriority.HIGH,
            status=ComplaintStatus.OPEN,
            created_at=_utc_naive(0, 8),
        ),
        dict(
            complaint_code="SSC-2026-005",
            resident=users["james.wilson@example.com"],
            assigned_staff=users["amelia.parker@example.com"],
            category=categories["HVAC"],
            title="Lounge air conditioner rattling",
            description="The common lounge unit rattles when the fan is on high. Cooling remained available during the visit.",
            location="Cedar House · Resident lounge",
            priority=ComplaintPriority.LOW,
            status=ComplaintStatus.CLOSED,
            created_at=_utc_naive(12),
            resolved_at=_utc_naive(9),
            closed_at=_utc_naive(8),
        ),
        dict(
            complaint_code="SSC-2026-006",
            resident=users[_recovery_test_email()],
            assigned_staff=users["emma.collins@example.com"],
            category=categories["Waste Management"],
            title="Recycling pickup missed",
            description="Blue recycling bins on level P1 were not emptied on the scheduled collection day.",
            location="Maple Tower · Parking level P1",
            priority=ComplaintPriority.MEDIUM,
            status=ComplaintStatus.REOPENED,
            created_at=_utc_naive(7),
            resolved_at=_utc_naive(3),
        ),
    ]

    created = {}
    for values in complaints:
        complaint = Complaint.query.filter_by(
            complaint_code=values["complaint_code"]
        ).first()
        if not complaint:
            complaint = Complaint(**values)
            db.session.add(complaint)
        created[values["complaint_code"]] = complaint

    db.session.flush()

    update_values = [
        ("SSC-2026-001", users[_recovery_test_email()], "OPEN", "Leak reported with cabinet cleared for access.", 1, 5),
        ("SSC-2026-001", admin, "ASSIGNED", "Assigned to the plumbing team for same-day inspection.", 1, 3),
        ("SSC-2026-001", users["emma.collins@example.com"], "IN_PROGRESS", "Supply line isolated; replacement fitting is being installed.", 0, 2),
        ("SSC-2026-002", admin, "ASSIGNED", "Electrical technician scheduled for tomorrow morning.", 1, 1),
        ("SSC-2026-003", users["amelia.parker@example.com"], "RESOLVED", "Door sensor alignment corrected and tested across ten cycles.", 2, 0),
        ("SSC-2026-005", users["amelia.parker@example.com"], "RESOLVED", "Fan housing tightened and vibration pads replaced.", 9, 0),
        ("SSC-2026-005", users["james.wilson@example.com"], "CLOSED", "Confirmed the lounge is quiet again. Thank you.", 8, 0),
        ("SSC-2026-006", users[_recovery_test_email()], "REOPENED", "Bins remain full after the follow-up collection window.", 1, 0),
    ]
    for code, author, status, comment, days, hours in update_values:
        db.session.add(
            ComplaintUpdate(
                complaint=created[code],
                updated_by_user=author,
                status=status,
                comment=comment,
                created_at=_utc_naive(days, hours),
            )
        )

    db.session.add_all(
        [
            Feedback(
                complaint=created["SSC-2026-003"],
                resident=users["sophie.bennett@example.com"],
                rating=5,
                comment="Quick response and the elevator is operating smoothly now.",
                created_at=_utc_naive(1),
            ),
            Feedback(
                complaint=created["SSC-2026-005"],
                resident=users["james.wilson@example.com"],
                rating=4,
                comment="Resolved cleanly with minimal disruption to the lounge.",
                created_at=_utc_naive(8),
            ),
            Notification(
                user=admin,
                complaint=created["SSC-2026-004"],
                title="New high-priority access issue",
                message="Parking gate access failure reported at Oak Residence.",
                type="NEW_COMPLAINT",
                is_read=False,
                created_at=_utc_naive(0, 8),
            ),
            Notification(
                user=admin,
                complaint=created["SSC-2026-006"],
                title="Complaint reopened",
                message="The missed recycling pickup requires another follow-up.",
                type="COMPLAINT_REOPENED",
                is_read=False,
                created_at=_utc_naive(1),
            ),
        ]
    )

    db.session.commit()
