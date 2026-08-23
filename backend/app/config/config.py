import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

# Configuration class for the Flask application.
class Config:
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-jwt-secret")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 86400)
    )  # 24 hours

    # File uploads
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        os.path.join(BASE_DIR, "uploads")
    )

    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
    )  # 5 MB

    ALLOWED_EXTENSIONS = set(
        os.getenv(
            "ALLOWED_EXTENSIONS",
            "png,jpg,jpeg,gif,pdf"
        ).split(",")
    )

    # Application
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    TESTING = os.getenv("TESTING", "False").lower() == "true")

    # Error handling
    PROPAGATE_EXCEPTIONS = (
        os.getenv("PROPAGATE_EXCEPTIONS", "True").lower() == "true"
    )

    # Flask-RESTX / Swagger
    RESTX_MASK_SWAGGER = False
    SWAGGER_UI_DOC_EXPANSION = os.getenv(
        "SWAGGER_UI_DOC_EXPANSION", "list"
    )
    ERROR_404_HELP = False

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Pagination
    ITEMS_PER_PAGE = int(
        os.getenv("ITEMS_PER_PAGE", 20)
    )

    # Application URL
    BASE_URL = os.getenv(
        "BASE_URL",
        "http://localhost:5000"
    )

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Email
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"