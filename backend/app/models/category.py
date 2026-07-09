from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Category Details
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Audit Fields
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

    # Relationships
    complaints = db.relationship(
        "Complaint",
        back_populates="category",
        lazy=True
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"