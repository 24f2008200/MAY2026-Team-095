from flask import request
from flask_restx import Namespace, Resource, fields

from app.controllers.admin_controller import (
    assign_staff_handler,
    create_category_handler,
    create_staff_handler,
    dashboard_handler,
    list_staff_handler,
    reports_handler,
    remove_staff_handler,
    list_complaints_handler,
)
from app.middleware.auth import admin_required
from app.models.complaint import Complaint, ComplaintPriority, ComplaintStatus
from app.services.complaint_service import get_all_complaints, _complaint_response
from app.extensions import db

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

create_staff_model = admin_ns.model(
    "CreateStaffRequest",
    {
        "name": fields.String(required=True, example="Sarah Connor"),
        "email": fields.String(required=True, example="staff@smartsociety.com"),
        "mobile_number": fields.String(required=False, example="9876543210"),
        "flat_number": fields.String(required=False, example="A-101"),
        "building": fields.String(required=False, example="Block A"),
        "password": fields.String(required=True, example="Staff@123"),
        "trade": fields.String(required=True, example="Plumber"),
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


@admin_ns.route("/staff")
class AdminStaffCreateResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Create a new staff account",
    )
    @admin_ns.expect(create_staff_model, validate=True)
    @admin_ns.response(201, "Staff created successfully")
    @admin_ns.response(400, "Validation error")
    @admin_ns.response(409, "Email or mobile already exists")
    def post(self):
        return create_staff_handler()


@admin_ns.route("/staff/<int:staff_id>")
class AdminStaffResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="Deactivate a staff account",
    )
    @admin_ns.response(200, "Staff deactivated successfully")
    @admin_ns.response(404, "Staff not found")
    @admin_ns.response(403, "Forbidden - cannot deactivate self")
    def delete(self, staff_id):
        return remove_staff_handler(staff_id)


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


@admin_ns.route("/complaints")
class AdminComplaintListResource(Resource):

    @admin_required
    @admin_ns.doc(
        security="Bearer",
        summary="List all complaints for admin dashboard",
        params={
            "status": "Filter by status (OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, REOPENED)",
            "priority": "Filter by priority (LOW, MEDIUM, HIGH, URGENT)",
            "search": "Search in title or complaint_code",
            "page": "Page number",
            "per_page": "Items per page (default: 10, max: 100)",
        },
    )
    @admin_ns.response(200, "Success")
    def get(self):
        """List all complaints with optional filtering."""
        from app.services.complaint_service import get_all_complaints
        from flask import request
        
        args = request.args.to_dict()
        status = args.get("status")
        priority = args.get("priority")
        search = args.get("search")
        page = int(args.get("page", 1))
        per_page = min(int(args.get("per_page", 10)), 100)
        
        query = Complaint.query.order_by(Complaint.created_at.desc())
        
        if status:
            try:
                query = query.filter_by(status=ComplaintStatus[status])
            except KeyError:
                pass
        if priority:
            try:
                query = query.filter_by(priority=ComplaintPriority[priority])
            except KeyError:
                pass
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Complaint.title.ilike(search_term),
                    Complaint.complaint_code.ilike(search_term),
                )
            )
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        complaints = pagination.items
        
        return {
            "success": True,
            "complaints": [_complaint_response(c) for c in complaints],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            }
        }, 200
