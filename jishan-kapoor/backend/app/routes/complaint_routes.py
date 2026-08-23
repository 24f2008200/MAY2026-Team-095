from flask_restx import Namespace, Resource, fields

from app.controllers.complaint_controller import (
    add_timeline_comment_handler,
    create_complaint_handler,
    get_complaint_handler,
    get_timeline_handler,
    list_complaints_handler,
    submit_feedback_handler,
    update_complaint_handler,
    upload_attachment_handler,
    close_complaint_handler,
    reopen_complaint_handler,
)
from app.middleware.auth import (
    authenticated_required,
    resident_required,
    roles_required,
)

complaint_ns = Namespace(
    name="complaints",
    description="Complaint management APIs",
)

create_complaint_model = complaint_ns.model(
    "CreateComplaintRequest",
    {
        "category_id": fields.Integer(required=True, example=1),
        "title": fields.String(required=True, example="Water leakage in kitchen"),
        "description": fields.String(
            required=True,
            example="There is continuous water leakage under the kitchen sink.",
        ),
        "location": fields.String(required=True, example="Flat A101, Kitchen"),
        "priority": fields.String(required=False, example="MEDIUM"),
    },
)

update_complaint_model = complaint_ns.model(
    "UpdateComplaintRequest",
    {
        "title": fields.String(required=False, example="Updated title"),
        "description": fields.String(required=False, example="Updated description"),
        "location": fields.String(required=False, example="Flat A101"),
        "priority": fields.String(required=False, example="HIGH"),
    },
)

timeline_comment_model = complaint_ns.model(
    "ComplaintTimelineCommentRequest",
    {
        "comment": fields.String(
            required=True,
            example="Just checking on the status of this.",
        ),
    },
)

feedback_model = complaint_ns.model(
    "FeedbackRequest",
    {
        "rating": fields.Integer(required=True, example=4),
        "comment": fields.String(required=False, example="Issue resolved quickly."),
    },
)


@complaint_ns.route("")
class ComplaintListResource(Resource):

    @authenticated_required
    @complaint_ns.doc(
        security="Bearer",
        summary="List complaints",
        description=(
            "Returns complaints based on user role. "
            "Residents see their own, staff see assigned, admin sees all."
        ),
        params={
            "page": "Page number (default: 1)",
            "per_page": "Items per page (default: 10, max: 100)",
            "status": "Filter by status (OPEN, ASSIGNED, etc.)",
            "priority": "Filter by priority (LOW, MEDIUM, HIGH, URGENT)",
            "category_id": "Filter by category ID",
            "search": "Search in title, code, or location",
        },
    )
    @complaint_ns.response(200, "Success")
    @complaint_ns.response(401, "Unauthorized")
    @complaint_ns.response(403, "Forbidden")
    def get(self):
        return list_complaints_handler()

    @resident_required
    @complaint_ns.doc(
        security="Bearer",
        summary="Create a complaint",
        description="Residents can submit a new maintenance complaint.",
    )
    @complaint_ns.expect(create_complaint_model, validate=True)
    @complaint_ns.response(201, "Complaint created")
    @complaint_ns.response(400, "Validation error")
    @complaint_ns.response(401, "Unauthorized")
    @complaint_ns.response(403, "Forbidden")
    def post(self):
        return create_complaint_handler()


@complaint_ns.route("/<int:complaint_id>")
class ComplaintDetailResource(Resource):

    @authenticated_required
    @complaint_ns.doc(
        security="Bearer",
        summary="Get complaint details",
    )
    @complaint_ns.response(200, "Success")
    @complaint_ns.response(403, "Forbidden")
    @complaint_ns.response(404, "Not found")
    def get(self, complaint_id):
        return get_complaint_handler(complaint_id)

    @resident_required
    @complaint_ns.doc(
        security="Bearer",
        summary="Update complaint details",
        description="Residents can update OPEN or REOPENED complaints.",
    )
    @complaint_ns.expect(update_complaint_model, validate=True)
    @complaint_ns.response(200, "Updated")
    @complaint_ns.response(400, "Validation error")
    @complaint_ns.response(403, "Forbidden")
    @complaint_ns.response(404, "Not found")
    def put(self, complaint_id):
        return update_complaint_handler(complaint_id)


@complaint_ns.route("/<int:complaint_id>/timeline")
class ComplaintTimelineResource(Resource):

    @authenticated_required
    @complaint_ns.doc(
        security="Bearer",
        summary="Get complaint timeline",
    )
    @complaint_ns.response(200, "Success")
    @complaint_ns.response(403, "Forbidden")
    @complaint_ns.response(404, "Not found")
    def get(self, complaint_id):
        return get_timeline_handler(complaint_id)

    @authenticated_required
    @complaint_ns.doc(
        security="Bearer",
        summary="Add a timeline comment",
        description=(
            "Post a comment on the complaint timeline. Available to the "
            "resident who owns the complaint, the assigned staff member, "
            "or an admin."
        ),
    )
    @complaint_ns.expect(timeline_comment_model, validate=True)
    @complaint_ns.response(201, "Comment added")
    @complaint_ns.response(400, "Validation error")
    @complaint_ns.response(403, "Forbidden")
    @complaint_ns.response(404, "Not found")
    def post(self, complaint_id):
        return add_timeline_comment_handler(complaint_id)


@complaint_ns.route("/<int:complaint_id>/attachments")
class ComplaintAttachmentResource(Resource):

    @authenticated_required
    @complaint_ns.doc(
        security="Bearer",
        summary="Upload attachment",
        description="Upload a file attachment for a complaint.",
    )
    @complaint_ns.response(201, "Uploaded")
    @complaint_ns.response(400, "Bad request")
    @complaint_ns.response(403, "Forbidden")
    @complaint_ns.response(404, "Not found")
    def post(self, complaint_id):
        return upload_attachment_handler(complaint_id)


@complaint_ns.route("/<int:complaint_id>/feedback")
class ComplaintFeedbackResource(Resource):

    @resident_required
    @complaint_ns.doc(
        security="Bearer",
        summary="Submit feedback",
        description="Submit feedback for a resolved or closed complaint.",
    )
    @complaint_ns.expect(feedback_model, validate=True)
    @complaint_ns.response(201, "Feedback submitted")
    @complaint_ns.response(400, "Validation error")
    @complaint_ns.response(403, "Forbidden")
    @complaint_ns.response(404, "Not found")
    @complaint_ns.response(409, "Already submitted")
    def post(self, complaint_id):
        return submit_feedback_handler(complaint_id)


@complaint_ns.route("/<int:complaint_id>/close")
class ComplaintCloseResource(Resource):

    @roles_required("ADMIN", "RESIDENT")
    @complaint_ns.doc(
        security="Bearer",
        summary="Close a complaint",
        description="An admin or the owning resident can close an active or resolved complaint.",
    )
    @complaint_ns.response(200, "Complaint closed")
    @complaint_ns.response(400, "Validation error")
    @complaint_ns.response(403, "Forbidden")
    @complaint_ns.response(404, "Not found")
    def put(self, complaint_id):
        return close_complaint_handler(complaint_id)


@complaint_ns.route("/<int:complaint_id>/reopen")
class ComplaintReopenResource(Resource):

    @resident_required
    @complaint_ns.doc(
        security="Bearer",
        summary="Reopen a resolved or closed complaint",
        description=(
            "The owning resident can reopen an unresolved issue within 7 days. "
            "Reopening clears the previous staff assignment and returns it to admin triage."
        ),
    )
    @complaint_ns.response(200, "Complaint reopened")
    @complaint_ns.response(400, "Validation error")
    @complaint_ns.response(403, "Forbidden")
    @complaint_ns.response(404, "Not found")
    def put(self, complaint_id):
        return reopen_complaint_handler(complaint_id)
