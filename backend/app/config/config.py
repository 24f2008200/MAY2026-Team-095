import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-jwt-secret")

    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24  # 24 hours

    PROPAGATE_EXCEPTIONS = True

    RESTX_MASK_SWAGGER = False

    SWAGGER_UI_DOC_EXPANSION = "list"

    ERROR_404_HELP = False