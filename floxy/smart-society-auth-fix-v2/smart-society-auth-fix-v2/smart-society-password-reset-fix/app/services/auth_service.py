from marshmallow import ValidationError
from flask import current_app, request
import hashlib
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
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


PASSWORD_RESET_SALT = "smart-society-password-reset-v1"


def _password_fingerprint(password_hash: str) -> str:
    """Short non-reversible fingerprint used to invalidate old reset tokens."""
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:24]


def _reset_serializer() -> URLSafeTimedSerializer:
    secret = current_app.config.get("SECRET_KEY")
    if not secret or secret == "change-this-secret-key":
        raise RuntimeError("SECRET_KEY must be configured before password recovery can be used.")
    return URLSafeTimedSerializer(secret_key=secret, salt=PASSWORD_RESET_SALT)


def _generate_reset_token(user: User) -> str:
    return _reset_serializer().dumps({
        "uid": user.id,
        "email": user.email,
        "ph": _password_fingerprint(user.password_hash),
    })


def _send_password_reset_email(user: User, token: str) -> None:
    mail_server = (current_app.config.get("MAIL_SERVER") or "").strip()
    mail_username = (current_app.config.get("MAIL_USERNAME") or "").strip()
    mail_password = current_app.config.get("MAIL_PASSWORD") or ""
    sender = (current_app.config.get("MAIL_DEFAULT_SENDER") or mail_username).strip()
    frontend_url = (current_app.config.get("FRONTEND_URL") or "http://localhost:3000").rstrip("/")

    if not mail_server or not sender:
        raise RuntimeError("Password recovery email is not configured. Set MAIL_SERVER and MAIL_DEFAULT_SENDER.")

    query = urlencode({"token": token})
    reset_url = f"{frontend_url}/static/reset-password.html?{query}"

    msg = EmailMessage()
    msg["Subject"] = "Reset your Smart Society password"
    msg["From"] = sender
    msg["To"] = user.email
    msg.set_content(
        f"Hello {user.name},\n\n"
        "A password reset was requested for your Smart Society account.\n\n"
        f"Open this secure link to choose a new password:\n{reset_url}\n\n"
        f"This link expires in {current_app.config.get('PASSWORD_RESET_TOKEN_MINUTES', 30)} minutes. "
        "If you did not request this reset, you can ignore this email.\n"
    )

    port = int(current_app.config.get("MAIL_PORT", 587))
    use_tls = bool(current_app.config.get("MAIL_USE_TLS", True))
    use_ssl = bool(current_app.config.get("MAIL_USE_SSL", False))
    timeout = int(current_app.config.get("MAIL_TIMEOUT", 15))

    if use_ssl:
        with smtplib.SMTP_SSL(mail_server, port, timeout=timeout, context=ssl.create_default_context()) as smtp:
            if mail_username:
                smtp.login(mail_username, mail_password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(mail_server, port, timeout=timeout) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if mail_username:
                smtp.login(mail_username, mail_password)
            smtp.send_message(msg)


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
    """Send a privacy-safe, expiring password-reset link when the account exists."""
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

    email = data["email"].lower().strip()
    user = User.query.filter_by(email=email).first()

    # Keep the public response identical whether or not the account exists.
    # This prevents the endpoint from becoming an account-enumeration tool.
    if user:
        try:
            token = _generate_reset_token(user)
            _send_password_reset_email(user, token)
            current_app.logger.info("Password reset email sent for user_id=%s", user.id)
        except Exception:
            # Do not leak mail-provider details or account existence to the client.
            current_app.logger.exception("Password reset email delivery failed for user_id=%s", user.id)
            return {
                "success": False,
                "message": "Password recovery is temporarily unavailable. Please try again later.",
            }, 503
    else:
        current_app.logger.info("Password reset requested for unregistered email")

    return {
        "success": True,
        "message": (
            "If an account with that email exists, password reset "
            "instructions have been sent."
        ),
    }, 200


def reset_password():
    """Validate a reset token and replace the user's stored password hash."""
    json_data = request.get_json(silent=True)
    if not json_data:
        return {"success": False, "message": "Request body is required."}, 400

    token = str(json_data.get("token") or "").strip()
    password = str(json_data.get("password") or "")

    if not token:
        return {"success": False, "message": "The password reset link is invalid."}, 400
    if len(password) < 8:
        return {"success": False, "message": "Password must be at least 8 characters long."}, 400
    if len(password) > 128:
        return {"success": False, "message": "Password must be 128 characters or fewer."}, 400

    max_age = int(current_app.config.get("PASSWORD_RESET_TOKEN_MINUTES", 30)) * 60

    try:
        payload = _reset_serializer().loads(token, max_age=max_age)
    except SignatureExpired:
        return {
            "success": False,
            "message": "This password reset link has expired. Please request a new one.",
        }, 400
    except BadSignature:
        return {
            "success": False,
            "message": "This password reset link is invalid. Please request a new one.",
        }, 400

    user = User.query.filter_by(id=payload.get("uid"), email=payload.get("email")).first()
    if not user:
        return {
            "success": False,
            "message": "This password reset link is invalid. Please request a new one.",
        }, 400

    # Once the password changes, the fingerprint changes too. This makes an old
    # token unusable even if its time limit has not yet expired.
    if payload.get("ph") != _password_fingerprint(user.password_hash):
        return {
            "success": False,
            "message": "This password reset link has already been used or is no longer valid.",
        }, 400

    user.password_hash = generate_password_hash(password)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unable to update password for user_id=%s", user.id)
        return {
            "success": False,
            "message": "We could not update your password. Please try again.",
        }, 500

    current_app.logger.info("Password reset completed for user_id=%s", user.id)
    return {
        "success": True,
        "message": "Your password has been reset successfully. You can now sign in.",
    }, 200
