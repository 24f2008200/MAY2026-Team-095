"""
schema_loader.py

OpenAPI Specification Loader

Responsibilities
----------------
1. Download OpenAPI YAML
2. Cache locally
3. Parse YAML
4. Resolve $ref references
5. Expose helper methods used by the rest of the engine

Part 1
"""

from pathlib import Path
import copy
import logging

import requests
import yaml

from config import (
    OPENAPI_URL,
    LOCAL_SPEC,
    AUTO_DOWNLOAD_SPEC,
    ALLOW_CACHE_FALLBACK,
)

logger = logging.getLogger(__name__)


# =====================================================================
# OpenAPI Specification Wrapper
# =====================================================================

class OpenAPISpec:

    def __init__(self, spec: dict):

        self.spec = spec or {}

        self.info = self.spec.get("info", {})

        self.paths = self.spec.get("paths", {})

        self.components = self.spec.get("components", {})

        self.schemas = self.components.get(
            "schemas",
            {}
        )

    # ------------------------------------------------------------

    @property
    def title(self):

        return self.info.get(
            "title",
            "Unknown"
        )

    # ------------------------------------------------------------

    @property
    def version(self):

        return self.info.get(
            "version",
            "Unknown"
        )

    # ------------------------------------------------------------

    def operations(self):
        """
        Iterate through every endpoint.

        Returns

            path
            method
            operation
        """

        valid = {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options"
        }

        for path, methods in self.paths.items():

            for method, operation in methods.items():

                if method.lower() not in valid:
                    continue

                yield (
                    path,
                    method.lower(),
                    operation
                )

    # ============================================================
    # Schema Lookup
    # ============================================================

    def get_schema(self, name):

        return self.schemas.get(name)

    # ------------------------------------------------------------

    def schema_names(self):

        return sorted(
            self.schemas.keys()
        )

    # ============================================================
    # $ref Resolution
    # ============================================================

    def resolve_ref(self, ref):
        """
        Resolve

            #/components/schemas/User

        into the actual schema dictionary.
        """

        if not ref.startswith("#/"):
            raise ValueError(
                f"External references not supported : {ref}"
            )

        node = self.spec

        parts = ref.lstrip("#/").split("/")

        for part in parts:

            if part not in node:
                raise KeyError(
                    f"Cannot resolve {ref}"
                )

            node = node[part]

        return node

    # ------------------------------------------------------------

    def resolve_schema(self, schema):
        """
        Recursively resolves every $ref
        found inside a schema.

        Returns a fully expanded schema.
        """

        if schema is None:
            return None

        schema = copy.deepcopy(schema)

        return self._resolve(schema)

    # ------------------------------------------------------------

    def _resolve(self, node):

        if isinstance(node, list):

            return [
                self._resolve(item)
                for item in node
            ]

        if not isinstance(node, dict):
            return node

        # ------------------------------------------
        # Entire object is a $ref
        # ------------------------------------------

        if "$ref" in node:

            resolved = self.resolve_ref(
                node["$ref"]
            )

            resolved = copy.deepcopy(
                resolved
            )

            # Merge any extra keys
            # besides $ref

            extras = {
                k: v
                for k, v in node.items()
                if k != "$ref"
            }

            resolved.update(extras)

            return self._resolve(resolved)

        # ------------------------------------------
        # Walk recursively
        # ------------------------------------------

        for key, value in node.items():

            node[key] = self._resolve(value)

        return node

    # ============================================================
    # Helpers
    # ============================================================

    def response_codes(self, operation):

        responses = operation.get(
            "responses",
            {}
        )

        return sorted(
            responses.keys()
        )

    # ------------------------------------------------------------

    def request_body(self, operation):

        return operation.get(
            "requestBody"
        )

    # ------------------------------------------------------------

    def parameters(self, operation):

        return operation.get(
            "parameters",
            []
        )

    # ------------------------------------------------------------

    def has_request_body(self, operation):

        return (
            "requestBody"
            in operation
        )

    # ------------------------------------------------------------

    def has_parameters(self, operation):

        return (
            len(
                operation.get(
                    "parameters",
                    []
                )
            )
            > 0
        )

# =====================================================================
# Continue in Part 2
# =====================================================================

    # ============================================================
    # Media Type Helpers
    # ============================================================

    def select_media_type(self, content):
        """
        Returns the preferred media type.

        Preference order:

            application/json
            application/*+json
            first available
        """

        if not content:
            return None

        if "application/json" in content:
            return "application/json"

        for media in content:
            if media.endswith("+json"):
                return media

        return next(iter(content.keys()))

    # ------------------------------------------------------------

    def get_request_content(self, operation):
        """
        Returns

            media_type,
            content_object
        """

        body = operation.get("requestBody")

        if not body:
            return None, None

        body = self.resolve_schema(body)

        content = body.get("content", {})

        media = self.select_media_type(content)

        if media is None:
            return None, None

        return media, content[media]

    # ------------------------------------------------------------

    def get_response_content(self, operation, status):
        """
        Returns

            media_type,
            content_object
        """

        responses = operation.get("responses", {})

        response = responses.get(str(status))

        if response is None:
            return None, None

        response = self.resolve_schema(response)

        content = response.get("content", {})

        media = self.select_media_type(content)

        if media is None:
            return None, None

        return media, content[media]

    # ============================================================
    # Schema Extraction
    # ============================================================

    def get_request_schema(self, operation):
        """
        Returns the resolved request schema.
        """

        _, content = self.get_request_content(operation)

        if content is None:
            return None

        schema = content.get("schema")

        if schema is None:
            return None

        return self.resolve_schema(schema)

    # ------------------------------------------------------------

    def get_response_schema(self, operation, status):
        """
        Returns the resolved response schema.
        """

        _, content = self.get_response_content(
            operation,
            status,
        )

        if content is None:
            return None

        schema = content.get("schema")

        if schema is None:
            return None

        return self.resolve_schema(schema)

    # ============================================================
    # Examples
    # ============================================================

    def get_request_example(self, operation):
        """
        Returns a request example if present.
        """

        _, content = self.get_request_content(operation)

        if content is None:
            return None

        if "example" in content:
            return content["example"]

        examples = content.get("examples")

        if examples:

            first = next(iter(examples.values()))

            if "value" in first:
                return first["value"]

        return None

    # ------------------------------------------------------------

    def get_response_example(self, operation, status):
        """
        Returns a response example if present.
        """

        _, content = self.get_response_content(
            operation,
            status,
        )

        if content is None:
            return None

        if "example" in content:
            return content["example"]

        examples = content.get("examples")

        if examples:

            first = next(iter(examples.values()))

            if "value" in first:
                return first["value"]

        return None


    # ============================================================
    # Parameter Handling
    # ============================================================

    def get_parameters(
        self,
        path_item: dict = None,
        operation: dict = None
    ):
        """
        Returns merged parameters.

        OpenAPI allows parameters at

            paths:
                /users/{id}
                    parameters:

        and

            get:
                parameters:

        Operation parameters override
        path parameters having the same
        (name,in).
        """

        merged = {}

        if path_item:

            for p in path_item.get("parameters", []):

                p = self.resolve_schema(p)

                key = (
                    p["name"],
                    p["in"]
                )

                merged[key] = p

        if operation:

            for p in operation.get("parameters", []):

                p = self.resolve_schema(p)

                key = (
                    p["name"],
                    p["in"]
                )

                merged[key] = p

        return list(merged.values())

    # ------------------------------------------------------------

    def split_parameters(
        self,
        path_item=None,
        operation=None
    ):
        """
        Returns

            {
                "path":[...],
                "query":[...],
                "header":[...],
                "cookie":[...]
            }
        """

        result = {
            "path": [],
            "query": [],
            "header": [],
            "cookie": []
        }

        params = self.get_parameters(
            path_item,
            operation
        )

        for p in params:

            location = p.get("in")

            if location in result:
                result[location].append(p)

        return result

    # ------------------------------------------------------------

    def required_parameters(
        self,
        path_item=None,
        operation=None
    ):

        params = self.get_parameters(
            path_item,
            operation
        )

        return [
            p
            for p in params
            if p.get("required")
        ]

    def operations(self):
        """
        Iterate through every operation.

        Returns

            path,
            path_item,
            method,
            operation
        """

        valid = {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
        }

        for path, path_item in self.paths.items():

            for method, operation in path_item.items():

                if method.lower() not in valid:
                    continue

                yield (
                    path,
                    path_item,
                    method.lower(),
                    operation,
                )

class SchemaLoader:

    def __init__(self):

        self.spec = None

    # --------------------------------------------------------

    def load(self):

        raw = None

        if AUTO_DOWNLOAD_SPEC:
            raw = self.download()

        if raw is None:
            raw = self.load_cache()

        if raw is None:
            raise RuntimeError(
                "Unable to load OpenAPI specification."
            )

        data = yaml.safe_load(raw)

        self.spec = OpenAPISpec(data)

        logger.info(
            "Loaded '%s' v%s",
            self.spec.title,
            self.spec.version,
        )

        logger.info(
            "%d paths",
            len(self.spec.paths)
        )

        logger.info(
            "%d schemas",
            len(self.spec.schemas)
        )

        return self.spec

    # --------------------------------------------------------

    def download(self):

        try:

            logger.info(
                "Downloading specification..."
            )

            r = requests.get(
                OPENAPI_URL,
                timeout=20
            )

            r.raise_for_status()

            LOCAL_SPEC.write_text(
                r.text,
                encoding="utf8"
            )

            logger.info(
                "Cached specification."
            )

            return r.text

        except Exception as ex:

            logger.warning(ex)

            return None

    # --------------------------------------------------------

    def load_cache(self):

        if not ALLOW_CACHE_FALLBACK:
            return None

        if not Path(LOCAL_SPEC).exists():
            return None

        logger.info(
            "Loading cached specification..."
        )

        return LOCAL_SPEC.read_text(
            encoding="utf8"
        )

loader = SchemaLoader()

# ------------------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    spec = loader.load()

    print()

    print(spec.title)
    print(spec.version)

    print()

    for (
        path,
        path_item,
        method,
        operation,
    ) in spec.operations():

        print(
            f"{method.upper():6s}",
            path
        )

        params = spec.split_parameters(
            path_item,
            operation
        )

        if params["path"]:
            print(
                "   Path Params:",
                [p["name"] for p in params["path"]]
            )

        if params["query"]:
            print(
                "   Query Params:",
                [p["name"] for p in params["query"]]
            )

