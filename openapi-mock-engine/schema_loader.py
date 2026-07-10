"""
schema_loader.py

Loads an OpenAPI 3.x specification from

    • GitHub RAW URL
    • Local file
    • Cached copy

and exposes helper methods for the mock engine.
"""

from pathlib import Path
import requests
import yaml
import logging

from config import (
    OPENAPI_URL,
    LOCAL_SPEC,
    AUTO_DOWNLOAD_SPEC,
    ALLOW_CACHE_FALLBACK,
)

logger = logging.getLogger(__name__)


class OpenAPISpec:

    def __init__(self, spec: dict):
        self.spec = spec or {}

        self.info = self.spec.get("info", {})
        self.paths = self.spec.get("paths", {})
        self.components = self.spec.get("components", {})
        self.schemas = self.components.get("schemas", {})

    # --------------------------------------------------------

    def title(self):
        return self.info.get("title", "Unknown")

    # --------------------------------------------------------

    def version(self):
        return self.info.get("version", "Unknown")

    # --------------------------------------------------------

    def operations(self):
        """
        Iterate through every operation.

        Returns tuples:

            path,
            method,
            operation
        """

        for path, methods in self.paths.items():

            for method, operation in methods.items():

                if method.lower() not in (
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "options",
                    "head",
                ):
                    continue

                yield (
                    path,
                    method.lower(),
                    operation,
                )

    # --------------------------------------------------------

    def get_schema(self, name):

        return self.schemas.get(name)

    # --------------------------------------------------------

    def schema_names(self):

        return list(self.schemas.keys())

    # --------------------------------------------------------

    def response_codes(self, operation):

        responses = operation.get("responses", {})

        return sorted(responses.keys())

    # --------------------------------------------------------

    def get_response(self, operation, status):

        return operation.get("responses", {}).get(status)

    # --------------------------------------------------------

    def request_body(self, operation):

        return operation.get("requestBody")

    # --------------------------------------------------------

    def parameters(self, operation):

        return operation.get("parameters", [])


# =====================================================================


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
            "Loaded '%s' version %s",
            self.spec.title(),
            self.spec.version(),
        )

        return self.spec

    # --------------------------------------------------------

    def download(self):

        try:

            logger.info("Downloading OpenAPI specification...")

            r = requests.get(
                OPENAPI_URL,
                timeout=15,
            )

            r.raise_for_status()

            LOCAL_SPEC.write_text(
                r.text,
                encoding="utf8",
            )

            logger.info("Specification cached.")

            return r.text

        except Exception as ex:

            logger.warning(
                "Download failed : %s",
                ex,
            )

            return None

    # --------------------------------------------------------

    def load_cache(self):

        if not ALLOW_CACHE_FALLBACK:
            return None

        if not Path(LOCAL_SPEC).exists():

            logger.warning(
                "Cached specification not found."
            )

            return None

        logger.info(
            "Loading cached specification..."
        )

        return LOCAL_SPEC.read_text(
            encoding="utf8"
        )


# =====================================================================

loader = SchemaLoader()

# =====================================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    spec = loader.load()

    print()

    print("Title    :", spec.title())
    print("Version  :", spec.version())
    print()

    print("Schemas")

    for name in spec.schema_names():
        print("   ", name)

    print()

    print("Operations")

    for path, method, operation in spec.operations():

        print(
            f"{method.upper():6s} {path}"
        )
