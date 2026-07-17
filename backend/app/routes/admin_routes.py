from flask_restx import Namespace, Resource, fields

from app.controllers.admin_controller import (
    assign_staff_handler,
    create_category_handler,
    dashboard_handler,
    list_staff_handler,
    reports_handler,
)
from app.middleware.auth import admin_required

admin_ns = Namespace(
    name="admin",
    description="Admin management APIs",
)

assign_staff_model = admin_ns.model(
    "AssignStaffRequest",
    {
        "staff_id": fields.Integer(required=True, example=2),
    },
)

create_category_model = admin_ns.model(
    "CreateCategoryRequest",
    {
        "name": fields.String(required=True, example="Plumbing"),
        "description": fields.String(
            required=False,
            example="Water and pipe related issues",
        ),
    },
)


@admin_ns.route("/dashboard")
class AdminDashboardResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Admin dashboard summary",
    )
    @admin_ns.response(200, "Success")
    @admin_ns.response(403, "Forbidden")
    def get(self):
        return dashboard_handler()


@admin_ns.route("/complaints/<int:complaint_id>/assign")
class AdminAssignStaffResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Assign staff to complaint",
    )
    @admin_ns.expect(assign_staff_model, validate=True)
    @admin_ns.response(200, "Staff assigned")
    @admin_ns.response(400, "Validation error")
    @admin_ns.response(404, "Not found")
    def put(self, complaint_id):
        return assign_staff_handler(complaint_id)


@admin_ns.route("/reports")
class AdminReportsResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Admin reports and analytics",
    )
    @admin_ns.response(200, "Success")
    def get(self):
        return reports_handler()


@admin_ns.route("/staff")
class AdminStaffListResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="List active staff members",
    )
    @admin_ns.response(200, "Success")
    def get(self):
        return list_staff_handler()


@admin_ns.route("/categories")
class AdminCategoryResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Create a complaint category",
    )
    @admin_ns.expect(create_category_model, validate=True)
    @admin_ns.response(201, "Category created")
    @admin_ns.response(409, "Already exists")
    def post(self):
        return create_category_handler()
