
"""
mock_engine.py

Core request dispatcher for the OpenAPI Mock Engine.

Responsibilities
----------------
1. Receive every request
2. Collect request data
3. Validate request
4. Choose response
5. Generate response
6. Return Flask response
"""

from __future__ import annotations

import logging
import time

from flask import jsonify

from checksum import checksum_engine

logger = logging.getLogger(__name__)


# =====================================================================
# Mock Engine
# =====================================================================

class MockEngine:

    def __init__(
        self,
        spec,
        validator=None,
        response_generator=None,
    ):
        """
        Parameters
        ----------
        spec
            OpenAPISpec

        validator
            validator.py

        response_generator
            response_generator.py
        """

        self.spec = spec

        self.validator = validator

        self.generator = response_generator

    # ==========================================================
    # Main entry point
    # ==========================================================

    def handle_request(
        self,
        path,
        path_item,
        method,
        operation,
        request,
        path_params=None,
    ):
        """
        Every dynamically created Flask route
        calls this function.
        """

        started = time.time()

        try:

            req = self.build_request_context(
                path=path,
                path_item=path_item,
                method=method,
                operation=operation,
                request=request,
                path_params=path_params,
            )

            self.log_request(req)

            #
            # Actual work is delegated.
            #

            return self.process_request(req)

        except Exception:

            logger.exception(
                "Unhandled exception"
            )

            return jsonify(
                {
                    "success": False,
                    "message": "Internal Mock Server Error"
                }
            ), 500

        finally:

            elapsed = (
                time.time() - started
            ) * 1000

            logger.info(
                "%.1f ms",
                elapsed,
            )

    # ==========================================================
    # Build Request Context
    # ==========================================================

    def build_request_context(
        self,
        path,
        path_item,
        method,
        operation,
        request,
        path_params,
    ):
        """
        Converts Flask request into a
        dictionary understood by the
        mock engine.
        """

        ctx = {}

        ctx["path"] = path

        ctx["path_item"] = path_item

        ctx["method"] = method

        ctx["operation"] = operation

        ctx["headers"] = dict(request.headers)

        ctx["query"] = request.args.to_dict()

        ctx["path_params"] = (
            path_params or {}
        )

        #
        # JSON body
        #

        if request.is_json:

            ctx["json"] = (
                request.get_json(
                    silent=True
                ) or {}
            )

        else:

            ctx["json"] = {}

        #
        # Form data
        #

        ctx["form"] = (
            request.form.to_dict()
        )

        #
        # Uploaded files
        #

        ctx["files"] = dict(
            request.files
        )

        #
        # Raw body
        #

        ctx["raw"] = request.get_data()

        #
        # Parameters from OpenAPI
        #

        ctx["parameters"] = (
            self.spec.split_parameters(
                path_item,
                operation,
            )
        )

        #
        # Request schema
        #

        ctx["request_schema"] = (
            self.spec.get_request_schema(
                operation
            )
        )

        #
        # Available response codes
        #

        ctx["response_codes"] = (
            self.spec.response_codes(
                operation
            )
        )

        return ctx

    # ==========================================================
    # Logging
    # ==========================================================

    def log_request(
        self,
        ctx,
    ):

        logger.info(
            "%s %s",
            ctx["method"].upper(),
            ctx["path"],
        )

        if ctx["query"]:

            logger.info(
                "Query : %s",
                ctx["query"],
            )

        if ctx["path_params"]:

            logger.info(
                "Path : %s",
                ctx["path_params"],
            )

        if ctx["json"]:

            logger.info(
                "JSON : %s",
                ctx["json"],
            )

    # ==========================================================
    # Pipeline
    # ==========================================================

    def process_request(
        self,
        ctx,
    ):
        """
        Main processing pipeline.

        Actual implementation comes
        in Part 2.
        """

        #
        # Validation
        #

        if self.validator:

            result = self.validator.validate(
                ctx,
            )

            if result is not None:
                return result

        #
        # Choose response
        #

        response_index = (
            checksum_engine.choose_response(
                ctx["json"],
                ctx["headers"],
                len(
                    ctx["response_codes"]
                ),
            )
        )

        #
        # Build response
        #

        if self.generator is None:

            #
            # Temporary placeholder.
            #

            status = int(
                ctx["response_codes"][
                    response_index
                ]
            )

            return jsonify(
                {
                    "status": status,
                    "message": "Generator not installed",
                    "responseIndex": response_index,
                }
            ), status

        #
        # Real implementation in Part 2
        #

        return self.generator.generate(
            ctx,
            response_index,
        )






