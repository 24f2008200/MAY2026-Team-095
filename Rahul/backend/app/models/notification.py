from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=True
    )

    # Notification Details
    title = db.Column(
        db.String(150),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    type = db.Column(
        db.String(50),
        nullable=False
    )

    channel = db.Column(
        db.String(30),
        nullable=False,
        default="IN_APP"
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    # Audit Fields
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        nullable=False
    )

    # -------------------------
    # Relationships
    # -------------------------

    user = db.relationship(
        "User",
        back_populates="notifications"
    )

    complaint = db.relationship(
        "Complaint"
    )

    def __repr__(self):
        return (
            f"<Notification(id={self.id}, "
            f"user_id={self.user_id}, "
            f"type='{self.type}')>"
        )