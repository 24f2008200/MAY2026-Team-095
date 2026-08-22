from flask import request
from flask_restx import Namespace, Resource, fields

from app.controllers.admin_controller import (
    assign_staff_handler,
    create_category_handler,
    list_all_categories_handler,
    update_category_status_handler,
    create_staff_handler,
    dashboard_handler,
    list_staff_handler,
    reports_handler,
    reviews_handler,
    remove_staff_handler,
    list_complaints_handler,
    list_pending_residents_handler,
    approve_resident_handler,
    reject_resident_handler,
)

from app.middleware.auth import admin_required
from app.services.complaint_service import get_all_complaints


admin_ns = Namespace(
    name="admin",
    description="Admin management APIs",
)


# -------------------------------------------------------------------------
# Request models
# -------------------------------------------------------------------------

assign_staff_model = admin_ns.model(
    "AssignStaffRequest",
    {
        "staff_id": fields.Integer(
            required=True,
            example=2,
        ),

        # IMPORTANT:
        # Do not use Flask-RESTX validation for this request.
        # The actual Marshmallow schema in admin_service.py supports
        # optional/null remarks and normalizes them safely.
        "remarks": fields.String(
            required=False,
            example="Please inspect the main valve before replacing parts.",
        ),
    },
)


create_category_model = admin_ns.model(
    "CreateCategoryRequest",
    {
        "name": fields.String(
            required=True,
            example="Plumbing",
        ),
        "description": fields.String(
            required=False,
            example="Water and pipe related issues",
        ),
    },
)


create_staff_model = admin_ns.model(
    "CreateStaffRequest",
    {
        "name": fields.String(
            required=True,
            example="Sarah Connor",
        ),
        "email": fields.String(
            required=True,
            example="staff@smartsociety.com",
        ),
        "mobile_number": fields.String(
            required=False,
            example="9876543210",
        ),
        "flat_number": fields.String(
            required=False,
            example="A-101",
        ),
        "building": fields.String(
            required=False,
            example="Block A",
        ),
        "password": fields.String(
            required=True,
            example="Staff@123",
        ),
        "trade": fields.String(
            required=True,
            example="Plumber",
        ),
    },
)


category_status_model = admin_ns.model(
    "CategoryStatusRequest",
    {
        "is_active": fields.Boolean(
            required=True,
            example=False,
        ),
    },
)


# -------------------------------------------------------------------------
# Dashboard
# -------------------------------------------------------------------------

@admin_ns.route("/dashboard")
class AdminDashboardResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Admin dashboard summary",
    )
    @admin_ns.response(
        200,
        "Success",
    )
    @admin_ns.response(
        403,
        "Forbidden",
    )
    def get(self):
        return dashboard_handler()


# -------------------------------------------------------------------------
# Complaint assignment / reassignment
# -------------------------------------------------------------------------

@admin_ns.route(
    "/complaints/<int:complaint_id>/assign"
)
class AdminAssignStaffResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Assign or reassign staff to complaint",
    )

    # IMPORTANT:
    #
    # validate=False is deliberate.
    #
    # Previously Flask-RESTX validated the JSON before the request reached
    # admin_service.py. When remarks was JSON null, RESTX generated:
    #
    # Remarks: None is not of type 'string'
    #
    # The service has its own Marshmallow validation and allows remarks=None,
    # therefore RESTX should document this payload but must not reject it.
    @admin_ns.expect(
        assign_staff_model,
        validate=False,
    )

    @admin_ns.response(
        200,
        "Staff assigned",
    )
    @admin_ns.response(
        400,
        "Validation error",
    )
    @admin_ns.response(
        404,
        "Not found",
    )
    def put(
        self,
        complaint_id,
    ):
        return assign_staff_handler(
            complaint_id
        )


# -------------------------------------------------------------------------
# Reports
# -------------------------------------------------------------------------

@admin_ns.route("/reports")
class AdminReportsResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Admin reports and analytics",
    )
    @admin_ns.response(
        200,
        "Success",
    )
    def get(self):
        return reports_handler()


# -------------------------------------------------------------------------
# Reviews
# -------------------------------------------------------------------------

@admin_ns.route("/reviews")
class AdminReviewsResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="List aggregate resident reviews",
        params={
            "page":
                "Page number",

            "per_page":
                "Items per page (max 100)",

            "rating":
                "Filter by star rating (1-5)",

            "date_from":
                "Review date from (YYYY-MM-DD)",

            "date_to":
                "Review date to (YYYY-MM-DD)",
        },
    )
    @admin_ns.response(
        200,
        "Success",
    )
    @admin_ns.response(
        400,
        "Validation error",
    )
    def get(self):
        return reviews_handler()


# -------------------------------------------------------------------------
# Staff
# -------------------------------------------------------------------------

@admin_ns.route("/staff")
class AdminStaffListResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="List active staff members",
        description=(
            "Optionally filter by trade using the ?trade= query parameter."
        ),
        params={
            "trade":
                "Filter staff by trade "
                "(e.g. Plumbing, Electrical, Carpentry, Janitorial, Security)"
        },
    )
    @admin_ns.response(
        200,
        "Success",
    )
    def get(self):
        return list_staff_handler()


@admin_ns.route("/staff")
class AdminStaffCreateResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Create a new staff account",
    )
    @admin_ns.expect(
        create_staff_model,
        validate=True,
    )
    @admin_ns.response(
        201,
        "Staff created successfully",
    )
    @admin_ns.response(
        400,
        "Validation error",
    )
    @admin_ns.response(
        409,
        "Email or mobile already exists",
    )
    def post(self):
        return create_staff_handler()


@admin_ns.route(
    "/staff/<int:staff_id>"
)
class AdminStaffResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Deactivate a staff account",
    )
    @admin_ns.response(
        200,
        "Staff deactivated successfully",
    )
    @admin_ns.response(
        404,
        "Staff not found",
    )
    @admin_ns.response(
        403,
        "Forbidden - cannot deactivate self",
    )
    def delete(
        self,
        staff_id,
    ):
        return remove_staff_handler(
            staff_id
        )


# -------------------------------------------------------------------------
# Categories
# -------------------------------------------------------------------------

@admin_ns.route("/categories")
class AdminCategoryResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="List all categories (active and inactive)",
    )
    @admin_ns.response(
        200,
        "Success",
    )
    def get(self):
        return list_all_categories_handler()

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Create a complaint category",
    )
    @admin_ns.expect(
        create_category_model,
        validate=True,
    )
    @admin_ns.response(
        201,
        "Category created",
    )
    @admin_ns.response(
        409,
        "Already exists",
    )
    def post(self):
        return create_category_handler()


@admin_ns.route(
    "/categories/<int:category_id>/status"
)
class AdminCategoryStatusResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Activate or deactivate a category",
    )
    @admin_ns.expect(
        category_status_model,
        validate=True,
    )
    @admin_ns.response(
        200,
        "Updated",
    )
    @admin_ns.response(
        404,
        "Not found",
    )
    def put(
        self,
        category_id,
    ):
        return update_category_status_handler(
            category_id
        )


# -------------------------------------------------------------------------
# Complaints
# -------------------------------------------------------------------------

@admin_ns.route("/complaints")
class AdminComplaintListResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="List all complaints for admin dashboard",
        params={
            "status":
                "Filter by status",

            "priority":
                "Filter by priority "
                "(LOW, MEDIUM, HIGH, URGENT)",

            "search":
                "Search ticket, resident, flat, category, "
                "staff, location, or trade",

            "date_from":
                "Created date from (YYYY-MM-DD)",

            "date_to":
                "Created date to (YYYY-MM-DD)",

            "sort":
                "newest or oldest",

            "page":
                "Page number",

            "per_page":
                "Items per page "
                "(default: 10, max: 100)",
        },
    )
    @admin_ns.response(
        200,
        "Success",
    )
    @admin_ns.response(
        400,
        "Validation error",
    )
    def get(self):
        return get_all_complaints()


# -------------------------------------------------------------------------
# Resident approvals
# -------------------------------------------------------------------------

@admin_ns.route(
    "/residents/pending"
)
class AdminPendingResidentsResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="List residents pending approval",
        description=(
            "Residents who registered but have not yet "
            "been approved by an admin."
        ),
    )
    @admin_ns.response(
        200,
        "Success",
    )
    def get(self):
        return list_pending_residents_handler()


@admin_ns.route(
    "/residents/<int:resident_id>/approve"
)
class AdminApproveResidentResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Approve a pending resident registration",
    )
    @admin_ns.response(
        200,
        "Resident approved",
    )
    @admin_ns.response(
        404,
        "Not found",
    )
    @admin_ns.response(
        409,
        "Already approved",
    )
    def put(
        self,
        resident_id,
    ):
        return approve_resident_handler(
            resident_id
        )


@admin_ns.route(
    "/residents/<int:resident_id>/reject"
)
class AdminRejectResidentResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Reject and remove a pending resident registration",
    )
    @admin_ns.response(
        200,
        "Registration rejected",
    )
    @admin_ns.response(
        404,
        "Not found",
    )
    @admin_ns.response(
        409,
        "Already approved",
    )
    def delete(
        self,
        resident_id,
    ):
        return reject_resident_handler(
            resident_id
        )