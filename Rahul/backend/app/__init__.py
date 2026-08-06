import os

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
from app.routes.complaint_routes import complaint_ns
from app.routes.category_routes import category_ns
from app.routes.admin_routes import admin_ns
from app.routes.staff_routes import staff_ns
from app.routes.notification_routes import notification_ns
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configuration
    
    app.config.from_object(Config)

    # Extensions
    # Extensions
    CORS(
    app,
    resources={
        r"/*": {
            "origins": "*"
        }
    }
)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Swagger
    api = Api(
    app,
    version="1.0.0",
    title="Smart Society API",
    description="Apartment Maintenance & Complaint Resolution System",
    doc="/",
    authorizations={
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "JWT Authorization Header. Example: Bearer <token>",
        }
    },
    security="Bearer",
)

    # Routes
    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(complaint_ns, path="/complaints")
    api.add_namespace(category_ns, path="/categories")
    api.add_namespace(admin_ns, path="/admin")
    api.add_namespace(staff_ns, path="/staff")
    api.add_namespace(notification_ns, path="/notifications")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app