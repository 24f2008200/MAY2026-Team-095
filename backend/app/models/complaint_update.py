from app.extensions import db


class ComplaintUpdate(db.Model):
    __tablename__ = "complaint_updates"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=False
    )

    updated_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Update Details
    status = db.Column(
        db.String(30),
        nullable=False
    )

    comment = db.Column(
        db.Text,
        nullable=True
    )

    # Audit Fields
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    # -------------------------
    # Relationships
    # -------------------------

    complaint = db.relationship(
        "Complaint",
        back_populates="updates"
    )

    updated_by_user = db.relationship(
        "User",
        back_populates="complaint_updates"
    )

    def __repr__(self):
        return (
            f"<ComplaintUpdate("
            f"complaint_id={self.complaint_id}, "
            f"status='{self.status}')>"
        )