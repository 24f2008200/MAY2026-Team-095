"""
route_builder.py

Creates Flask routes dynamically from an OpenAPI specification.

This module DOES NOT generate responses.
It simply registers routes and forwards requests to MockEngine.
"""

from functools import partial
from flask import request

HTTP_METHODS = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
    "options": "OPTIONS",
    "head": "HEAD",
}


class RouteBuilder:
    """
    Builds Flask routes dynamically.
    """

    def __init__(self, app, spec, engine):
        self.app = app
        self.spec = spec
        self.engine = engine

        self.routes = []

    # -------------------------------------------------------------

    def build(self):
        """
        Register every route in the OpenAPI document.
        """

        for path, method, operation in self.spec.operations():

            flask_path = self.convert_path(path)

            endpoint_name = self.make_endpoint_name(
                method,
                flask_path
            )

            handler = partial(
                self.dispatch,
                path=path,
                method=method,
                operation=operation,
            )

            self.app.add_url_rule(
                flask_path,
                endpoint=endpoint_name,
                view_func=handler,
                methods=[HTTP_METHODS[method]],
            )

            self.routes.append({
                "method": method.upper(),
                "path": flask_path,
                "operationId": operation.get(
                    "operationId",
                    ""
                )
            })

    # -------------------------------------------------------------

    def dispatch(
        self,
        path,
        method,
        operation,
        **kwargs
    ):
        """
        Every request comes here.
        """

        return self.engine.handle_request(
            path=path,
            method=method,
            operation=operation,
            request=request,
            path_params=kwargs,
        )

    # -------------------------------------------------------------

    def convert_path(self, path):
        """
        Convert OpenAPI syntax

            /users/{id}

        into Flask syntax

            /users/<id>
        """

        import re

        return re.sub(
            r"\{([^}]+)\}",
            r"<\1>",
            path,
        )

    # -------------------------------------------------------------

    def make_endpoint_name(
        self,
        method,
        path
    ):
        """
        Every endpoint name must be unique.
        """

        name = (
            method
            + "_"
            + path
        )

        name = (
            name.replace("/", "_")
                .replace("<", "")
                .replace(">", "")
                .replace("-", "_")
        )

        return name

    # -------------------------------------------------------------

    def list_routes(self):
        """
        Returns generated routes.
        """

        return sorted(
            self.routes,
            key=lambda r: (
                r["path"],
                r["method"]
            )
        )
