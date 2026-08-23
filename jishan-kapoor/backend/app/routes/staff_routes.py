from flask_restx import Namespace, Resource, fields

from app.controllers.staff_controller import (
    add_timeline_handler,
    dashboard_summary_handler,
    get_assigned_complaint_handler,
    history_handler,
    list_assigned_complaints_handler,
    update_status_handler,
)
from app.middleware.auth import staff_required

staff_ns = Namespace(
    name="staff",
    description="Staff complaint management APIs",
)

status_update_model = staff_ns.model(
    "StatusUpdateRequest",
    {
        "status": fields.String(required=True, example="IN_PROGRESS"),
        "comment": fields.String(
            required=False,
            example="Started working on the issue.",
        ),
    },
)

timeline_comment_model = staff_ns.model(
    "TimelineCommentRequest",
    {
        "comment": fields.String(
            required=True,
            example="Inspected the area and ordered replacement parts.",
        ),
    },
)


@staff_ns.route("/complaints")
class StaffComplaintListResource(Resource):

    @staff_required
    @staff_ns.doc(
        security="Bearer",
        summary="List assigned complaints",
        params={
            "page": "Page number",
            "per_page": "Items per page",
            "status": "Filter by status",
            "priority": "Filter by priority",
            "search": "Search term",
        },
    )
    @staff_ns.response(200, "Success")
    def get(self):
        return list_assigned_complaints_handler()


@staff_ns.route("/dashboard/summary")
class StaffDashboardSummaryResource(Resource):

    @staff_required
    @staff_ns.doc(
        security="Bearer",
        summary="Staff dashboard summary",
        description="Counts of the staff member's assigned complaints by status.",
    )
    @staff_ns.response(200, "Success")
    def get(self):
        return dashboard_summary_handler()


@staff_ns.route("/complaints/history")
class StaffComplaintHistoryResource(Resource):

    @staff_required
    @staff_ns.doc(
        security="Bearer",
        summary="Staff complaint history",
        description="Resolved/closed complaints previously assigned to the staff member.",
        params={
            "page": "Page number",
            "per_page": "Items per page",
            "status": "Filter by status (RESOLVED or CLOSED)",
        },
    )
    @staff_ns.response(200, "Success")
    @staff_ns.response(400, "Validation error")
    def get(self):
        return history_handler()


@staff_ns.route("/complaints/<int:complaint_id>")
class StaffComplaintDetailResource(Resource):

    @staff_required
    @staff_ns.doc(
        security="Bearer",
        summary="Get assigned complaint details",
    )
    @staff_ns.response(200, "Success")
    @staff_ns.response(403, "Forbidden")
    @staff_ns.response(404, "Not found")
    def get(self, complaint_id):
        return get_assigned_complaint_handler(complaint_id)


@staff_ns.route("/complaints/<int:complaint_id>/status")
class StaffStatusUpdateResource(Resource):

    @staff_required
    @staff_ns.doc(
        security="Bearer",
        summary="Update complaint status",
        description="Staff can set status to IN_PROGRESS or RESOLVED.",
    )
    @staff_ns.expect(status_update_model, validate=True)
    @staff_ns.response(200, "Status updated")
    @staff_ns.response(400, "Validation error")
    @staff_ns.response(403, "Forbidden")
    @staff_ns.response(404, "Not found")
    def put(self, complaint_id):
        return update_status_handler(complaint_id)


@staff_ns.route("/complaints/<int:complaint_id>/timeline")
class StaffTimelineResource(Resource):

    @staff_required
    @staff_ns.doc(
        security="Bearer",
        summary="Add timeline comment",
    )
    @staff_ns.expect(timeline_comment_model, validate=True)
    @staff_ns.response(201, "Timeline update added")
    @staff_ns.response(400, "Validation error")
    @staff_ns.response(403, "Forbidden")
    @staff_ns.response(404, "Not found")
    def post(self, complaint_id):
        return add_timeline_handler(complaint_id)
