from datetime import datetime, timedelta, timezone
from html import escape
import secrets

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
from app.models.password_reset_otp import PasswordResetOtp
from app.models.user import User, UserRole
from app.services.notification_service import create_notification
from app.services.email_service import send_email
from app.schemas.auth_schema import (
    ForgotPasswordSchema,
    RegisterSchema,
    LoginSchema,
    VerifyResetOtpSchema,
)


register_schema = RegisterSchema()
login_schema = LoginSchema()
forgot_password_schema = ForgotPasswordSchema()
verify_reset_otp_schema = VerifyResetOtpSchema()

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def _user_response(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "mobile_number": user.mobile_number,
        "role": user.role.value,
        "flat_number": user.flat_number,
        "building": user.building,
        "trade": user.trade,
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


def _utcnow_naive() -> datetime:
    """Return UTC without tzinfo for consistent SQLAlchemy DateTime storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _generate_otp() -> str:
    """Generate a cryptographically secure six-digit recovery code."""
    return str(secrets.randbelow(900000) + 100000)


def forgot_password():
    """
    Email a short-lived verification code without changing the password.

    The response is intentionally generic and identical whether or not
    the email is registered, so the endpoint can't be used to check
    which emails exist in the system.
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

    generic_response = {
        "success": True,
        "message": (
            "If an account with that email exists, a verification code "
            "has been emailed to it."
        ),
    }, 200

    if not user:
        current_app.logger.info(
            "Password reset requested for unregistered email=%s", email
        )
        return generic_response

    otp = _generate_otp()
    safe_name = escape(user.name)

    subject = "Smart Society - Your Verification Code"
    html_body = f"""
        <!doctype html>
        <html>
        <body style="margin:0;padding:24px;background:#f4f5f7;font-family:Arial,sans-serif;color:#172033;">
          <div style="max-width:600px;margin:24px auto;background:#ffffff;padding:36px;border-radius:12px;">
            <h2 style="margin-top:0;">Smart Society password recovery</h2>
            <p>Hi {safe_name},</p>
            <p>We received a request to reset your Smart Society account password.</p>
            <p>Enter this verification code on the recovery page:</p>
            <div style="text-align:center;margin:28px 0;padding:18px;background:#f4f5f7;border-radius:8px;font-size:32px;font-weight:bold;letter-spacing:8px;">
              {otp}
            </div>
            <p>This code expires in {OTP_TTL_MINUTES} minutes and can be used only once. For your security, do not share it.</p>
            <p>If you did not request this change, you can safely ignore this email. Your password has not been changed.</p>
            <hr style="border:0;border-top:1px solid #e5e7eb;margin:28px 0;">
            <p style="font-size:13px;color:#64748b;">This is an automated message from Smart Society.</p>
          </div>
        </body>
        </html>
    """
    text_body = (
        f"Hi {user.name},\n\n"
        f"Your Smart Society verification code is: {otp}\n\n"
        f"This code expires in {OTP_TTL_MINUTES} minutes and can be used "
        "only once. If you did not request this change, ignore this email. "
        "Your password has not been changed."
    )

    if not send_email(user.email, subject, html_body, text_body):
        return {
            "success": False,
            "message": (
                "We couldn't send the verification email right now. "
                "Please try again later or contact an administrator."
            ),
        }, 502

    reset = PasswordResetOtp.query.filter_by(user_id=user.id).first()
    if reset is None:
        reset = PasswordResetOtp(user_id=user.id)
        db.session.add(reset)

    reset.code_hash = generate_password_hash(otp)
    reset.expires_at = _utcnow_naive() + timedelta(minutes=OTP_TTL_MINUTES)
    reset.attempts = 0

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "success": False,
            "message": "Unable to start password recovery. Please try again.",
        }, 500

    current_app.logger.info(
        "Password reset verification email sent to user_id=%s", user.id
    )
    return generic_response


def verify_password_reset_otp():
    """Validate a recovery code and replace the password exactly once."""
    json_data = request.get_json(silent=True)

    if not json_data:
        return {
            "success": False,
            "message": "Request body is required.",
        }, 400

    try:
        data = verify_reset_otp_schema.load(json_data)
    except ValidationError as err:
        return {
            "success": False,
            "errors": err.messages,
        }, 400

    failure = {
        "success": False,
        "message": (
            "The verification code is invalid or expired. Request a new "
            "code and try again."
        ),
    }, 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user:
        return failure

    reset = PasswordResetOtp.query.filter_by(user_id=user.id).first()
    if not reset:
        return failure

    if reset.expires_at <= _utcnow_naive():
        db.session.delete(reset)
        db.session.commit()
        return failure

    if reset.attempts >= OTP_MAX_ATTEMPTS:
        db.session.delete(reset)
        db.session.commit()
        return failure

    if not check_password_hash(reset.code_hash, data["otp"]):
        reset.attempts += 1
        if reset.attempts >= OTP_MAX_ATTEMPTS:
            db.session.delete(reset)
        db.session.commit()
        return failure

    user.password_hash = generate_password_hash(data["password"])
    db.session.delete(reset)
    db.session.commit()

    current_app.logger.info("Password reset completed for user_id=%s", user.id)
    return {
        "success": True,
        "message": "Password reset successful. You can now sign in.",
    }, 200
