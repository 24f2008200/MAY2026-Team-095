from flask_restx import Namespace, Resource

from app.controllers.category_controller import list_categories_handler
from app.middleware.auth import authenticated_required

category_ns = Namespace(
    name="categories",
    description="Complaint category APIs",
)


@category_ns.route("")
class CategoryListResource(Resource):

    @authenticated_required
    @category_ns.doc(
        security="Bearer",
        summary="List active categories",
    )
    @category_ns.response(200, "Success")
    @category_ns.response(401, "Unauthorized")
    def get(self):
        return list_categories_handler()
