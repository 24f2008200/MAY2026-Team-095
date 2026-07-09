from flask_restx import Namespace, Resource

from app.controllers.auth_controller import (
    register_user,
    login_user,
    get_profile
)

auth_ns = Namespace(
    "auth",
    description="Authentication APIs"
)


@auth_ns.route("/register")
class RegisterResource(Resource):

    def post(self):
        return register_user()


@auth_ns.route("/login")
class LoginResource(Resource):

    def post(self):
        return login_user()


@auth_ns.route("/profile")
class ProfileResource(Resource):

    def get(self):
        return get_profile()