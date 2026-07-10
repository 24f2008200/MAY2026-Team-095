"""
config.py

Configuration for the OpenAPI Mock Engine.
"""

from pathlib import Path
import os

# ---------------------------------------------------------------------
# Project Directories
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

CACHE_DIR = BASE_DIR / "cache"
LOG_DIR = BASE_DIR / "logs"
SPEC_DIR = BASE_DIR / "specs"

CACHE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
SPEC_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------
# OpenAPI Specification
# ---------------------------------------------------------------------

# GitHub RAW URL
OPENAPI_URL = os.getenv(
    "OPENAPI_URL",
    "https://raw.githubusercontent.com/24f2008200/MAY2026-Team-095/main/api-docs/openapi.yaml"
)

# Cached copy
LOCAL_SPEC = CACHE_DIR / "openapi.yaml"

# ---------------------------------------------------------------------
# Flask Server
# ---------------------------------------------------------------------

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# ---------------------------------------------------------------------
# Mock Behaviour
# ---------------------------------------------------------------------

# Artificial response delay (milliseconds)
DEFAULT_DELAY_MS = int(os.getenv("DEFAULT_DELAY_MS", 0))

# If True, validate request JSON against schema
ENABLE_VALIDATION = True

# If True, generate fake data from schemas
ENABLE_FAKE_DATA = True

# Allow overriding the response using:
#
#     X-Mock-Response: 2
#
ALLOW_HEADER_OVERRIDE = True

# Allow:
#
#     "name": "john#3"
#
ALLOW_FIELD_OVERRIDE = True

# ---------------------------------------------------------------------
# Checksum Configuration
# ---------------------------------------------------------------------

# Parameter priority while selecting checksum field.
#
# The first field found in the incoming request wins.
#
CONTROL_FIELD_PRIORITY = [

    "name",
    "username",
    "email",
    "mobile",
    "phone",
    "id",
    "userId",
    "eventId",
    "postId",
    "title"

]

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

LOG_LEVEL = "INFO"

REQUEST_LOG = LOG_DIR / "requests.log"

# ---------------------------------------------------------------------
# Response Profiles
# ---------------------------------------------------------------------

#
# Future feature.
#
# "normal"
# "mostly-success"
# "mostly-errors"
# "auth-errors"
#

PROFILE = "normal"

# ---------------------------------------------------------------------
# Miscellaneous
# ---------------------------------------------------------------------

# Maximum size of request body accepted.
MAX_REQUEST_SIZE = 5 * 1024 * 1024

# Pretty-print JSON responses.
PRETTY_JSON = True

# Automatically download latest YAML at startup.
AUTO_DOWNLOAD_SPEC = True

# If GitHub is unavailable, use cached copy.
ALLOW_CACHE_FALLBACK = True

# ---------------------------------------------------------------------
# Developer Routes
# ---------------------------------------------------------------------

ENABLE_ROUTE_LIST = True
ENABLE_RELOAD = True
ENABLE_HEALTHCHECK = True

# ---------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------

CORS_ORIGINS = [
    "*"
]
