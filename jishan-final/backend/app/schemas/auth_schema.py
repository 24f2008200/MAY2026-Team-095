from marshmallow import (
    Schema,
    fields,
    validates,
    validates_schema,
    ValidationError,
    validate,
)


def _validate_password_strength(value):
    if not any(c.isupper() for c in value):
        raise ValidationError(
            "Password must contain at least one uppercase letter."
        )
    if not any(c.islower() for c in value):
        raise ValidationError(
            "Password must contain at least one lowercase letter."
        )
    if not any(c.isdigit() for c in value):
        raise ValidationError(
            "Password must contain at least one number."
        )
    special = "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~"
    if not any(c in special for c in value):
        raise ValidationError(
            "Password must contain at least one special character."
        )


class RegisterSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(
            min=2,
            max=100,
            error="Name must be between 2 and 100 characters."
        ),
    )

    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
    )

    mobile_number = fields.String(
        required=True,
    )

    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(
            min=8,
            max=128,
            error="Password must be between 8 and 128 characters."
        ),
    )

    flat_number = fields.String(
        required=True,
        validate=validate.Length(
            min=1,
            max=20,
        ),
    )

    building = fields.String(
        required=True,
        validate=validate.Length(
            min=2,
            max=100,
        ),
    )

    @validates("name")
    def validate_name(self, value, **kwargs):
        value = value.strip()

        if not value:
            raise ValidationError("Name is required.")

        if not all(
            c.isalpha() or c.isspace() or c in ".-'"
            for c in value
        ):
            raise ValidationError(
                "Name contains invalid characters."
            )

    @validates("mobile_number")
    def validate_mobile(self, value, **kwargs):
        value = value.strip()

        if not value.isdigit():
            raise ValidationError(
                "Mobile number must contain digits only."
            )

        if len(value) != 10:
            raise ValidationError(
                "Mobile number must be exactly 10 digits."
            )

        if value[0] not in ["6", "7", "8", "9"]:
            raise ValidationError(
                "Invalid Indian mobile number."
            )

    @validates("password")
    def validate_password(self, value, **kwargs):
        _validate_password_strength(value)

    @validates_schema
    def normalize(self, data, **kwargs):
        data["name"] = data["name"].strip()
        data["email"] = data["email"].strip().lower()
        data["mobile_number"] = data["mobile_number"].strip()
        data["flat_number"] = data["flat_number"].strip()
        data["building"] = data["building"].strip()


class ForgotPasswordSchema(Schema):
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
    )

    @validates_schema
    def normalize(self, data, **kwargs):
        data["email"] = data["email"].strip().lower()


class LoginSchema(Schema):
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
    )

    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(
            min=8,
            max=128,
        ),
    )

    @validates_schema
    def normalize(self, data, **kwargs):
        data["email"] = data["email"].strip().lower()


class VerifyResetOtpSchema(Schema):
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
    )
    otp = fields.String(
        required=True,
        validate=validate.Regexp(
            r"^\d{6}$",
            error="Verification code must contain exactly six digits.",
        ),
    )
    @validates_schema
    def normalize(self, data, **kwargs):
        data["email"] = data["email"].strip().lower()
        data["otp"] = data["otp"].strip()


class ResetPasswordSchema(Schema):
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
    )
    reset_token = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(min=32, max=256),
    )
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(
            min=8,
            max=128,
            error="Password must be between 8 and 128 characters.",
        ),
    )

    @validates("password")
    def validate_password(self, value, **kwargs):
        _validate_password_strength(value)

    @validates_schema
    def normalize(self, data, **kwargs):
        data["email"] = data["email"].strip().lower()
