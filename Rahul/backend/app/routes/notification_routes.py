from flask_restx import Namespace, Resource

from app.controllers.notification_controller import (
    list_notifications_handler,
    mark_all_read_handler,
    mark_read_handler,
)
from app.middleware.auth import authenticated_required

notification_ns = Namespace(
    name="notifications",
    description="User notification APIs",
)


@notification_ns.route("")
class NotificationListResource(Resource):

    @authenticated_required
    @notification_ns.doc(
        security="Bearer",
        summary="List user notifications",
        params={
            "page": "Page number (default: 1)",
            "per_page": "Items per page (default: 20, max: 100)",
            "unread_only": "Set to true to show only unread",
        },
    )
    @notification_ns.response(200, "Success")
    @notification_ns.response(401, "Unauthorized")
    def get(self):
        return list_notifications_handler()


@notification_ns.route("/<int:notification_id>/read")
class NotificationReadResource(Resource):

    @authenticated_required
    @notification_ns.doc(
        security="Bearer",
        summary="Mark notification as read",
    )
    @notification_ns.response(200, "Marked as read")
    @notification_ns.response(404, "Not found")
    def put(self, notification_id):
        return mark_read_handler(notification_id)


@notification_ns.route("/read-all")
class NotificationReadAllResource(Resource):

    @authenticated_required
    @notification_ns.doc(
        security="Bearer",
        summary="Mark all notifications as read",
    )
    @notification_ns.response(200, "All marked as read")
    def put(self):
        return mark_all_read_handler()
