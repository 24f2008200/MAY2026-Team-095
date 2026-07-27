# from app.extensions import db
#
#
# class Attachment(db.Model):
#     __tablename__ = "attachments"
#
#     # Primary Key
#     id = db.Column(db.Integer, primary_key=True)
#
#     # Foreign Keys
#     complaint_id = db.Column(
#         db.Integer,
#         db.ForeignKey("complaints.id"),
#         nullable=False
#     )
#
#     uploaded_by = db.Column(
#         db.Integer,
#         db.ForeignKey("users.id"),
#         nullable=False
#     )
#
#     # File Information
#     file_name = db.Column(
#         db.String(255),
#         nullable=False
#     )
#
#     file_path = db.Column(
#         db.String(500),
#         nullable=False
#     )
#
#     file_type = db.Column(
#         db.String(50),
#         nullable=False
#     )
#
#     file_size = db.Column(
#         db.Integer,
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
#         back_populates="attachments"
#     )
#
#     uploaded_by_user = db.relationship(
#         "User",
#         back_populates="attachments"
#     )
#
#     def __repr__(self):
#         return (
#             f"<Attachment(id={self.id}, "
#             f"file='{self.file_name}')>"
#         )

from app.extensions import db


class Attachment(db.Model):
    __tablename__ = "attachments"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=False
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # File Information
    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    file_type = db.Column(
        db.String(50),
        nullable=False
    )

    file_size = db.Column(
        db.Integer,
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
        back_populates="attachments"
    )

    uploaded_by_user = db.relationship(
        "User",
        back_populates="attachments"
    )

    def __repr__(self):
        return (
            f"<Attachment(id={self.id}, "
            f"file='{self.file_name}')>"
        )