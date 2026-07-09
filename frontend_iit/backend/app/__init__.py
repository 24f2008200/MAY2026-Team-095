from flask import Flask
from flask_cors import CORS

from app.config.config import Config
from app.extensions import db, migrate


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/")
    def home():
        return {
            "message": "Smart Society Apartment Maintenance API",
            "status": "Running"
        }

    return app