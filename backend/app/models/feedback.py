# from app.extensions import db
#
#
# class Feedback(db.Model):
#     __tablename__ = "feedbacks"
#
#     # Primary Key
#     id = db.Column(db.Integer, primary_key=True)
#
#     # Foreign Keys
#     complaint_id = db.Column(
#         db.Integer,
#         db.ForeignKey("complaints.id"),
#         nullable=False,
#         unique=True
#     )
#
#     resident_id = db.Column(
#         db.Integer,
#         db.ForeignKey("users.id"),
#         nullable=False
#     )
#
#     # Feedback Details
#     rating = db.Column(
#         db.Integer,
#         nullable=False
#     )
#
#     comment = db.Column(
#         db.Text,
#         nullable=True
#     )
#
#     # Audit Fields
#     created_at = db.Column(
#         db.DateTime,
#         server_default=db.func.now(),
#         nullable=False
#     )
#
#     # -------------------------
#     # Relationships
#     # -------------------------
#
#     complaint = db.relationship(
#         "Complaint",
#         back_populates="feedback"
#     )
#
#     resident = db.relationship(
#         "User",
#         back_populates="feedbacks"
#     )
#
#     def __repr__(self):
#         return (
#             f"<Feedback(id={self.id}, "
#             f"complaint_id={self.complaint_id}, "
#             f"rating={self.rating})>"
#         )

from app.extensions import db


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=False,
        unique=True
    )

    resident_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Feedback Details
    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comment = db.Column(
        db.Text,
        nullable=True
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

    complaint = db.relationship(
        "Complaint",
        back_populates="feedback"
    )

    resident = db.relationship(
        "User",
        back_populates="feedbacks"
    )

    def __repr__(self):
        return (
            f"<Feedback(id={self.id}, "
            f"complaint_id={self.complaint_id}, "
            f"rating={self.rating})>"
        )