from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    validates,
    validates_schema,
)

from app.models.complaint import (
    ComplaintPriority,
)


class CreateComplaintSchema(Schema):
    category_id = fields.Integer(
        required=True,
        strict=True,
    )

    title = fields.String(
        required=True,
        validate=validate.Length(
            min=5,
            max=150,
            error="Title must be between 5 and 150 characters.",
        ),
    )

    description = fields.String(
        required=True,
        validate=validate.Length(
            min=10,
            max=5000,
            error="Description must be between 10 and 5000 characters.",
        ),
    )

    location = fields.String(
        required=True,
        validate=validate.Length(
            min=2,
            max=150,
        ),
    )

    priority = fields.String(
        required=False,
        load_default="MEDIUM",
    )

    @validates("priority")
    def validate_priority(self, value, **kwargs):
        allowed = [p.value for p in ComplaintPriority]

        if value not in allowed:
            raise ValidationError(
                f"Priority must be one of: {', '.join(allowed)}"
            )

    @validates_schema
    def normalize(self, data, **kwargs):
        data["title"] = data["title"].strip()
        data["description"] = data["description"].strip()
        data["location"] = data["location"].strip()


class UpdateComplaintSchema(Schema):
    title = fields.String(
        required=False,
        validate=validate.Length(
            min=5,
            max=150,
        ),
    )

    description = fields.String(
        required=False,
        validate=validate.Length(
            min=10,
            max=5000,
        ),
    )

    location = fields.String(
        required=False,
        validate=validate.Length(
            min=2,
            max=150,
        ),
    )

    priority = fields.String(
        required=False,
    )

    @validates("priority")
    def validate_priority(self, value, **kwargs):
        allowed = [p.value for p in ComplaintPriority]

        if value not in allowed:
            raise ValidationError(
                f"Priority must be one of: {', '.join(allowed)}"
            )

    @validates_schema
    def normalize(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()


class ComplaintTimelineSchema(Schema):
    status = fields.String(required=True)

    comment = fields.String(required=False)