from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource, fields

from app.controllers.auth_controller import (
    register_user,
    login_user,
    get_profile,
    forgot_password_handler,
    reset_password_handler,
    verify_password_reset_otp_handler,
)

auth_ns = Namespace(
    name="auth",
    description="Authentication APIs",
)


register_model = auth_ns.model(
    "RegisterRequest",
    {
        "name": fields.String(required=True, example="Thomas Reed"),
        "email": fields.String(required=True, example="thomas.reed@example.com"),
        "mobile_number": fields.String(required=True, example="9876543210"),
        "password": fields.String(required=True, example="Password@123"),
        "flat_number": fields.String(required=True, example="A101"),
        "building": fields.String(required=True, example="Block A"),
    },
)

forgot_password_model = auth_ns.model(
    "ForgotPasswordRequest",
    {
        "email": fields.String(required=True, example="thomas.reed@example.com"),
    },
)

verify_reset_otp_model = auth_ns.model(
    "VerifyResetOtpRequest",
    {
        "email": fields.String(required=True, example="thomas.reed@example.com"),
        "otp": fields.String(required=True, example="483921"),
    },
)

reset_password_model = auth_ns.model(
    "ResetPasswordRequest",
    {
        "email": fields.String(required=True, example="thomas.reed@example.com"),
        "reset_token": fields.String(required=True, example="verified-reset-token"),
        "password": fields.String(required=True, example="NewPassword@123"),
    },
)

login_model = auth_ns.model(
    "LoginRequest",
    {
        "email": fields.String(required=True, example="thomas.reed@example.com"),
        "password": fields.String(required=True, example="Password@123"),
    },
)


@auth_ns.route("/register")
class RegisterResource(Resource):

    @auth_ns.doc(
        summary="Register a new resident",
        description="Creates a new resident account.",
    )
    @auth_ns.expect(register_model, validate=True)
    @auth_ns.response(201, "User registered successfully")
    @auth_ns.response(400, "Validation error")
    @auth_ns.response(409, "Email or mobile already exists")
    @auth_ns.response(500, "Internal server error")
    def post(self):
        return register_user()


@auth_ns.route("/login")
class LoginResource(Resource):

    @auth_ns.doc(
        summary="Login",
        description="Authenticate user and return JWT access token.",
    )
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.response(200, "Login successful")
    @auth_ns.response(401, "Invalid credentials")
    @auth_ns.response(403, "Inactive account")
    def post(self):
        return login_user()


@auth_ns.route("/forgot-password")
class ForgotPasswordResource(Resource):

    @auth_ns.doc(
        summary="Forgot password",
        description=(
            "Emails a six-digit, ten-minute verification code when the account "
            "exists. No password changes during this request. "
            "Unknown accounts receive the same generic response."
        ),
    )
    @auth_ns.expect(forgot_password_model, validate=True)
    @auth_ns.response(200, "Request accepted")
    @auth_ns.response(400, "Validation error")
    def post(self):
        return forgot_password_handler()


@auth_ns.route("/verify-reset-otp")
class VerifyResetOtpResource(Resource):

    @auth_ns.doc(
        summary="Verify password-reset OTP",
        description=(
            "Validates a six-digit recovery code before any new password is "
            "accepted. Codes expire after ten minutes, allow at most five "
            "failed attempts, and issue a short-lived one-time reset token."
        ),
    )
    @auth_ns.expect(verify_reset_otp_model, validate=True)
    @auth_ns.response(200, "Code verified")
    @auth_ns.response(400, "Invalid, expired, or malformed code")
    def post(self):
        return verify_password_reset_otp_handler()


@auth_ns.route("/reset-password")
class ResetPasswordResource(Resource):

    @auth_ns.doc(
        summary="Set a new password",
        description=(
            "Sets a strong new password using the one-time token issued only "
            "after successful OTP verification."
        ),
    )
    @auth_ns.expect(reset_password_model, validate=True)
    @auth_ns.response(200, "Password reset successful")
    @auth_ns.response(400, "Invalid, expired, or malformed reset session")
    def post(self):
        return reset_password_handler()


@auth_ns.route("/profile")
class ProfileResource(Resource):

    @jwt_required()
    @auth_ns.doc(
        security="Bearer",
        summary="Current user profile",
        description="Returns the currently authenticated user's profile.",
    )
    @auth_ns.response(200, "Success")
    @auth_ns.response(401, "Unauthorized")
    @auth_ns.response(404, "User not found")
    def get(self):
        return get_profile()
