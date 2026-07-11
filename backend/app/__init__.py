from flask import Flask
from flask_cors import CORS
from flask_restx import Api

from app.config.config import Config
from app.extensions import db, migrate, jwt

# Register all models
from app.models import (
    User,
    Category,
    Complaint,
    ComplaintUpdate,
    Attachment,
    Notification,
    Feedback,
)

# Routes
from app.routes.auth_routes import auth_ns


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config.from_object(Config)

    # Extensions
    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Swagger
    api = Api(
        app,
        version="1.0",
        title="Smart Society API",
        description="Apartment Maintenance & Complaint Resolution System",
        doc="/"
    )

    # Routes
    api.add_namespace(auth_ns, path="/auth")

    return app