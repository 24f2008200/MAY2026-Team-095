from marshmallow import Schema, fields


class RegisterSchema(Schema):

    name = fields.String(required=True)

    email = fields.Email(required=True)

    mobile_number = fields.String(required=True)

    password = fields.String(required=True)

    flat_number = fields.String(required=True)

    building = fields.String(required=True)


class LoginSchema(Schema):

    email = fields.Email(required=True)

    password = fields.String(required=True)