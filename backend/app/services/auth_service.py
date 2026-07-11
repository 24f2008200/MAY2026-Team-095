from flask import request
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

# Later
# from app.models import User
# from app.extensions import db
# from flask_jwt_extended import create_access_token


def register():

    data = request.get_json()

    return {
        "message": "Register API Ready",
        "request": data
    }, 201


def login():

    data = request.get_json()

    return {
        "message": "Login API Ready",
        "request": data
    }, 200


def profile():

    return {
        "message": "Profile API Ready"
    }, 200