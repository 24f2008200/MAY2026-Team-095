from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
)


class FeedbackSchema(Schema):
    rating = fields.Integer(
        required=True,
        strict=True,
        validate=validate.Range(
            min=1,
            max=5,
        ),
    )

    comment = fields.String(
        required=False,
        validate=validate.Length(
            max=1000,
        ),
    )

    @validates_schema
    def normalize(self, data, **kwargs):
        if "comment" in data and data["comment"]:
            data["comment"] = data["comment"].strip()
