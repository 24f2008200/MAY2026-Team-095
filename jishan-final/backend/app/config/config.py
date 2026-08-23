import os
import secrets
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)

    # Render's free web service does not include a managed database. Use a
    # local SQLite database by default so the complete app runs at no cost.
    # Set DATABASE_URL later if a persistent external database is added.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'smart_society.db')}",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(48)

    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24  # 24 hours

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

    PROPAGATE_EXCEPTIONS = True

    RESTX_MASK_SWAGGER = False

    SWAGGER_UI_DOC_EXPANSION = "list"

    ERROR_404_HELP = False

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.zoho.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME

    # HTTPS email delivery works on Render Free, which blocks SMTP ports.
    BREVO_API_KEY = os.getenv("BREVO_API_KEY")
    BREVO_API_URL = os.getenv(
        "BREVO_API_URL",
        "https://api.brevo.com/v3/smtp/email",
    )
    BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
    BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Smart Society")
