import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-jwt-secret")

    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24  # 24 hours

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

    PROPAGATE_EXCEPTIONS = True

    RESTX_MASK_SWAGGER = False

    SWAGGER_UI_DOC_EXPANSION = "list"

    ERROR_404_HELP = False