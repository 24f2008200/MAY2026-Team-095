from enum import Enum

from app.extensions import db


class UserRole(Enum):
    RESIDENT = "RESIDENT"
    ADMIN = "ADMIN"
    STAFF = "STAFF"


class User(db.Model):
    __tablename__ = "users"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Personal Information
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)

    # Authentication
    password_hash = db.Column(db.String(255), nullable=False)

    # Role
    role = db.Column(
        db.Enum(UserRole),
        nullable=False,
        default=UserRole.RESIDENT
    )

    # Apartment / profile information
    flat_number = db.Column(db.String(20), nullable=False)
    building = db.Column(db.String(100), nullable=False)

    # Maintenance expertise. Kept separate from building so staff assignment
    # does not overload a resident/location field.
    trade = db.Column(db.String(100), nullable=True)

    # Account Status
    is_active = db.Column(db.Boolean, default=True)

    # Audit Fields
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        nullable=False
    )

    # -----------------------------
    # Relationships
    # -----------------------------

    # Complaints raised by Resident
    complaints = db.relationship(
        "Complaint",
        foreign_keys="Complaint.resident_id",
        back_populates="resident",
        lazy=True
    )

    # Complaints assigned to Staff
    assigned_complaints = db.relationship(
        "Complaint",
        foreign_keys="Complaint.assigned_staff_id",
        back_populates="assigned_staff",
        lazy=True
    )

    # Complaint Timeline Updates
    complaint_updates = db.relationship(
        "ComplaintUpdate",
        back_populates="updated_by_user",
        lazy=True
    )

    # Uploaded Attachments
    attachments = db.relationship(
        "Attachment",
        back_populates="uploaded_by_user",
        lazy=True
    )

    # Notifications
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        lazy=True
    )

    # Feedback Submitted
    feedbacks = db.relationship(
        "Feedback",
        back_populates="resident",
        lazy=True
    )

    def __repr__(self):
        return (
            f"<User(id={self.id}, "
            f"name='{self.name}', "
            f"role='{self.role.value}')>"
        )