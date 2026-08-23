import os
from pathlib import Path

from flask import Flask, current_app, jsonify, send_from_directory
from flask_cors import CORS
from flask_restx import Api
from werkzeug.security import check_password_hash, generate_password_hash

from app.config.config import BASE_DIR, Config
from app.extensions import db, migrate, jwt

# Register all models
from app.models import (
    User,
    UserRole,
    Category,
    Complaint,
    ComplaintUpdate,
    Attachment,
    Notification,
    Feedback,
    PasswordResetOtp,
)

# Routes
from app.routes.auth_routes import auth_ns
from app.routes.complaint_routes import complaint_ns
from app.routes.category_routes import category_ns
from app.routes.admin_routes import admin_ns
from app.routes.staff_routes import staff_ns
from app.routes.notification_routes import notification_ns


def _sync_admin_credentials():
    """Create or rotate the environment-managed administrator account."""
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if not admin_email or not admin_password:
        return

    existing_admin = User.query.filter_by(role=UserRole.ADMIN).first()
    email_owner = User.query.filter_by(email=admin_email).first()

    if email_owner and email_owner.role != UserRole.ADMIN:
        current_app.logger.error(
            "Cannot sync administrator: configured ADMIN_EMAIL belongs to "
            "a non-admin account."
        )
        return

    admin = email_owner or existing_admin
    if not admin:
        admin = User(
            name=os.getenv("ADMIN_NAME", "Administrator").strip(),
            email=admin_email,
            mobile_number=os.getenv("ADMIN_MOBILE", "+10000000000").strip(),
            password_hash=generate_password_hash(admin_password),
            role=UserRole.ADMIN,
            flat_number="ADMIN",
            building="Management",
            is_active=True,
        )
        db.session.add(admin)
    else:
        admin.email = admin_email
        admin.name = os.getenv("ADMIN_NAME", "Administrator").strip()
        admin.is_active = True
        if not check_password_hash(admin.password_hash, admin_password):
            admin.password_hash = generate_password_hash(admin_password)

    db.session.commit()


def create_app():
    # The repository's frontend uses /static/*.html for its page URLs. Disable
    # Flask's built-in package static route so the frontend catch-all below can
    # serve those files instead of returning a backend/static 404.
    app = Flask(__name__, static_folder=None)

    # Configuration
    app.config.from_object(Config)

    # Extensions
    CORS(
        app,
        resources={
            r"/*": {
                "origins": "*",
            }
        },
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
        doc="/api-docs/",
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
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

    # A fresh free-tier deployment starts without a database. Create the
    # schema and optionally seed its first administrator from Render secrets.
    with app.app_context():
        db.create_all()

        _sync_admin_credentials()

        if os.getenv("SEED_DEMO_DATA", "false").lower() == "true":
            from app.seed import seed_demo_data

            seed_demo_data()

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename,
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    frontend_dir = Path(BASE_DIR).parent / "frontend"

    # flask-restx registers its own '/' endpoint even when Swagger is moved.
    # Point that endpoint at the real frontend instead of its default 404.
    app.view_functions["root"] = lambda: send_from_directory(
        frontend_dir,
        "index.html",
    )

    @app.route("/", defaults={"path": "index.html"})
    @app.route("/<path:path>")
    def frontend(path):
        requested = frontend_dir / path
        if requested.is_file():
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, "index.html")

    return app
