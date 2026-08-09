from marshmallow import ValidationError
from flask import current_app, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
)
from sqlalchemy.exc import IntegrityError
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from app.extensions import db
from app.models.user import User, UserRole
from app.services.notification_service import create_notification
from app.schemas.auth_schema import (
    ForgotPasswordSchema,
    RegisterSchema,
    LoginSchema,
)


register_schema = RegisterSchema()
login_schema = LoginSchema()
forgot_password_schema = ForgotPasswordSchema()


def _user_response(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "mobile_number": user.mobile_number,
        "role": user.role.value,
        "flat_number": user.flat_number,
        "building": user.building,
        "is_active": user.is_active,
        "created_at": (
            user.created_at.isoformat()
            if user.created_at
            else None
        ),
    }


def register():

    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required."
        }, 400

    try:
        data = register_schema.load(json_data)

    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages
        }, 400

    existing_email = User.query.filter_by(
        email=data["email"]
    ).first()

    if existing_email:
        return {
            "success": False,
            "message": "Email already registered."
        }, 409

    existing_mobile = User.query.filter_by(
        mobile_number=data["mobile_number"]
    ).first()

    if existing_mobile:
        return {
            "success": False,
            "message": "Mobile number already registered."
        }, 409

    password_hash = generate_password_hash(
        data["password"]
    )

    user = User(
        name=data["name"].strip(),
        email=data["email"].lower().strip(),
        mobile_number=data["mobile_number"].strip(),
        password_hash=password_hash,
        role=UserRole.RESIDENT,
        flat_number=data["flat_number"].strip(),
        building=data["building"].strip(),
        # New resident sign-ups are held for admin approval before they
        # can log in. Staff/admin accounts are created pre-approved
        # elsewhere (admin_service.create_staff, initial admin seed).
        is_active=False,
    )

    try:

        db.session.add(user)
        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return {
            "success": False,
            "message": "Unable to register user."
        }, 500

    # No access_token here: the account is pending admin approval
    # (is_active=False) and must not be usable until approved.
    # Notify every admin so they see it in the Approvals section.
    admins = User.query.filter_by(role=UserRole.ADMIN, is_active=True).all()
    for admin in admins:
        create_notification(
            user_id=admin.id,
            complaint_id=None,
            title="New Resident Registration",
            message=(
                f"{user.name} (Flat {user.flat_number}) has registered "
                f"and is awaiting approval."
            ),
            notification_type="RESIDENT_APPROVAL",
        )
    db.session.commit()

    return {
        "success": True,
        "message": (
            "Registration successful. Your account is pending admin "
            "approval - you'll be able to log in once it's approved."
        ),
        "user": _user_response(user),
    }, 201


def login():

    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required."
        }, 400

    try:
        data = login_schema.load(json_data)

    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages
        }, 400

    user = User.query.filter_by(
        email=data["email"].lower().strip()
    ).first()

    if not user:
        return {
            "success": False,
            "message": "Invalid email or password."
        }, 401

    if not check_password_hash(
        user.password_hash,
        data["password"],
    ):
        return {
            "success": False,
            "message": "Invalid email or password."
        }, 401

    if not user.is_active:
        message = (
            "Your account is pending admin approval. You'll be able to "
            "log in once an administrator approves it."
            if user.role == UserRole.RESIDENT
            else "Account has been disabled."
        )
        return {
            "success": False,
            "message": message,
        }, 403

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role.value,
            "email": user.email,
        },
    )

    return {
        "success": True,
        "message": "Login successful.",
        "access_token": access_token,
        "user": _user_response(user),
    }, 200


def profile():

    user_id = get_jwt_identity()

    user = User.query.get(user_id)

    if not user:
        return {
            "success": False,
            "message": "User not found."
        }, 404

    return {
        "success": True,
        "user": _user_response(user),
    }, 200


def forgot_password():
    """
    Accepts an email and (stub) triggers a password reset.

    Real email delivery is out of scope for this project, so this logs
    the request server-side. The response is intentionally generic and
    identical whether or not the email is registered, so the endpoint
    can't be used to check which emails exist in the system.
    """
    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    try:
        data = forgot_password_schema.load(json_data)
    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages,
        }, 400

    email = data["email"]
    user = User.query.filter_by(email=email).first()

    if user:
        current_app.logger.info(
            "Password reset requested for user_id=%s email=%s",
            user.id,
            email,
        )
    else:
        current_app.logger.info(
            "Password reset requested for unregistered email=%s",
            email,
        )

    return {
        "success": True,
        "message": (
            "If an account with that email exists, password reset "
            "instructions have been sent."
        ),
    }, 200