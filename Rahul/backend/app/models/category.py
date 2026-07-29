# from app.extensions import db
#
#
# class Category(db.Model):
#     __tablename__ = "categories"
#
#     # Primary Key
#     id = db.Column(db.Integer, primary_key=True)
#
#     # Category Details
#     name = db.Column(
#         db.String(100),
#         unique=True,
#         nullable=False,
#         index=True,
#     )
#
#     description = db.Column(
#         db.String(255),
#         nullable=True,
#     )
#
#     # Status
#     is_active = db.Column(
#         db.Boolean,
#         nullable=False,
#         default=True,
#     )
#
#     # Audit Fields
#     created_at = db.Column(
#         db.DateTime,
#         nullable=False,
#         server_default=db.func.now(),
#     )
#
#     updated_at = db.Column(
#         db.DateTime,
#         nullable=False,
#         server_default=db.func.now(),
#         onupdate=db.func.now(),
#     )
#
#     # Relationships
#     complaints = db.relationship(
#         "Complaint",
#         back_populates="category",
#         lazy=True,
#         cascade="all",
#     )
#
#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "description": self.description,
#             "is_active": self.is_active,
#             "created_at": (
#                 self.created_at.isoformat()
#                 if self.created_at
#                 else None
#             ),
#             "updated_at": (
#                 self.updated_at.isoformat()
#                 if self.updated_at
#                 else None
#             ),
#         }
#
#     def __repr__(self):
#         return (
#             f"<Category("
#             f"id={self.id}, "
#             f"name='{self.name}', "
#             f"active={self.is_active}"
#             f")>"
#         )
from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Category Details
    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.String(255),
        nullable=True,
    )

    # Status
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    # Audit Fields
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # Relationships
    complaints = db.relationship(
        "Complaint",
        back_populates="category",
        lazy=True,
        cascade="all",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
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
        }

    def __repr__(self):
        return (
            f"<Category("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"active={self.is_active}"
            f")>"
        )