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
        nullable=False,
        index=True,
    )

    # Foreign Keys
    resident_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )

    # Complaint Details
    title = db.Column(
        db.String(150),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    location = db.Column(
        db.String(150),
        nullable=False,
    )

    priority = db.Column(
        db.Enum(ComplaintPriority),
        nullable=False,
        default=ComplaintPriority.MEDIUM,
        index=True,
    )

    status = db.Column(
        db.Enum(ComplaintStatus),
        nullable=False,
        default=ComplaintStatus.OPEN,
        index=True,
    )

    # Dates
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        nullable=False,
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    # -------------------------
    # Relationships
    # -------------------------

    resident = db.relationship(
        "User",
        foreign_keys=[resident_id],
        back_populates="complaints",
        lazy="joined",
    )

    assigned_staff = db.relationship(
        "User",
        foreign_keys=[assigned_staff_id],
        back_populates="assigned_complaints",
        lazy="joined",
    )

    category = db.relationship(
        "Category",
        back_populates="complaints",
        lazy="joined",
    )

    updates = db.relationship(
        "ComplaintUpdate",
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy=True,
    )

    attachments = db.relationship(
        "Attachment",
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy=True,
    )

    feedback = db.relationship(
        "Feedback",
        back_populates="complaint",
        uselist=False,
        cascade="all, delete-orphan",
        lazy=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_code": self.complaint_code,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "priority": self.priority.value,
            "status": self.status.value,
            "resident_id": self.resident_id,
            "assigned_staff_id": self.assigned_staff_id,
            "category_id": self.category_id,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
            "resolved_at": (
                self.resolved_at.isoformat()
                if self.resolved_at
                else None
            ),
        }

    def __repr__(self):
        return (
            f"<Complaint("
            f"id={self.id}, "
            f"code='{self.complaint_code}', "
            f"status='{self.status.value}'"
            f")>"
        )