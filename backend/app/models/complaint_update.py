# from app.extensions import db
#
#
# class ComplaintUpdate(db.Model):
#     __tablename__ = "complaint_updates"
#
#     # Primary Key
#     id = db.Column(db.Integer, primary_key=True)
#
#     # Foreign Keys
#     complaint_id = db.Column(
#         db.Integer,
#         db.ForeignKey("complaints.id"),
#         nullable=False,
#         index=True,
#     )
#
#     updated_by = db.Column(
#         db.Integer,
#         db.ForeignKey("users.id"),
#         nullable=False,
#         index=True,
#     )
#
#     # Update Details
#     status = db.Column(
#         db.String(30),
#         nullable=False,
#         index=True,
#     )
#
#     comment = db.Column(
#         db.Text,
#         nullable=True,
#     )
#
#     # Audit Fields
#     created_at = db.Column(
#         db.DateTime,
#         nullable=False,
#         server_default=db.func.now(),
#     )
#
#     # Relationships
#     complaint = db.relationship(
#         "Complaint",
#         back_populates="updates",
#         lazy="joined",
#     )
#
#     updated_by_user = db.relationship(
#         "User",
#         back_populates="complaint_updates",
#         lazy="joined",
#     )
#
#     def to_dict(self):
#         return {
#             "id": self.id,
#             "complaint_id": self.complaint_id,
#             "updated_by": self.updated_by,
#             "status": self.status,
#             "comment": self.comment,
#             "created_at": (
#                 self.created_at.isoformat()
#                 if self.created_at
#                 else None
#             ),
#         }
#
#     def __repr__(self):
#         return (
#             f"<ComplaintUpdate("
#             f"id={self.id}, "
#             f"complaint_id={self.complaint_id}, "
#             f"status='{self.status}'"
#             f")>"
#         )

from app.extensions import db


class ComplaintUpdate(db.Model):
    __tablename__ = "complaint_updates"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=False,
        index=True,
    )

    updated_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Update Details
    status = db.Column(
        db.String(30),
        nullable=False,
        index=True,
    )

    comment = db.Column(
        db.Text,
        nullable=True,
    )

    # Audit Fields
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    # Relationships
    complaint = db.relationship(
        "Complaint",
        back_populates="updates",
        lazy="joined",
    )

    updated_by_user = db.relationship(
        "User",
        back_populates="complaint_updates",
        lazy="joined",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "updated_by": self.updated_by,
            "status": self.status,
            "comment": self.comment,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }

    def __repr__(self):
        return (
            f"<ComplaintUpdate("
            f"id={self.id}, "
            f"complaint_id={self.complaint_id}, "
            f"status='{self.status}'"
            f")>"
        )