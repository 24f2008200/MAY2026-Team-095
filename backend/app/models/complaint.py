from enum import Enum

from app.extensions import db


class ComplaintPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ComplaintStatus(Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class Complaint(db.Model):
    __tablename__ = "complaints"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    complaint_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    # Foreign Keys
    resident_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    # Complaint Details
    title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    location = db.Column(
        db.String(150),
        nullable=False
    )

    priority = db.Column(
        db.Enum(ComplaintPriority),
        nullable=False,
        default=ComplaintPriority.MEDIUM
    )

    status = db.Column(
        db.Enum(ComplaintStatus),
        nullable=False,
        default=ComplaintStatus.OPEN
    )

    # Dates
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # -------------------------
    # Relationships
    # -------------------------

    resident = db.relationship(
        "User",
        foreign_keys=[resident_id],
        back_populates="complaints"
    )

    assigned_staff = db.relationship(
        "User",
        foreign_keys=[assigned_staff_id],
        back_populates="assigned_complaints"
    )

    category = db.relationship(
        "Category",
        back_populates="complaints"
    )

    updates = db.relationship(
        "ComplaintUpdate",
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy=True
    )

    attachments = db.relationship(
        "Attachment",
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy=True
    )

    feedback = db.relationship(
        "Feedback",
        back_populates="complaint",
        uselist=False
    )

    def __repr__(self):
        return (
            f"<Complaint(code={self.complaint_code}, "
            f"status={self.status.value})>"
        )