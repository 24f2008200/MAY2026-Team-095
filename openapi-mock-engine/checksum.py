"""
checksum.py

Determines which response to return for a request.

Priority:

1. X-Mock-Response header
2. Field override using '#'
3. Checksum of selected control field
4. Checksum of entire JSON body
"""

import hashlib
from typing import Any, Dict, Optional

from config import (
    ALLOW_FIELD_OVERRIDE,
    ALLOW_HEADER_OVERRIDE,
    CONTROL_FIELD_PRIORITY,
)


class ChecksumEngine:

    # -------------------------------------------------------------
    # Public
    # -------------------------------------------------------------

    def choose_response(
        self,
        request_json: Optional[Dict[str, Any]],
        headers,
        number_of_responses: int,
    ) -> int:
        """
        Returns response index

        Example:

            number_of_responses = 4

            returns

                0
                1
                2
                3
        """

        if number_of_responses <= 1:
            return 0

        # ---------------------------------------------------------
        # Header override
        # ---------------------------------------------------------

        if ALLOW_HEADER_OVERRIDE:

            override = headers.get("X-Mock-Response")

            if override is not None:
                try:
                    return int(override) % number_of_responses
                except ValueError:
                    pass

        # ---------------------------------------------------------
        # JSON body missing
        # ---------------------------------------------------------

        if not request_json:
            return 0

        # ---------------------------------------------------------
        # Pick best control field
        # ---------------------------------------------------------

        field = self.pick_control_field(request_json)

        if field is None:
            checksum = self.json_checksum(request_json)
            return checksum % number_of_responses

        value = str(request_json[field])

        # ---------------------------------------------------------
        # Inline override
        #
        # john#2
        # pbn#1
        # ---------------------------------------------------------

        if ALLOW_FIELD_OVERRIDE:

            forced = self.extract_override(value)

            if forced is not None:
                return forced % number_of_responses

        checksum = self.string_checksum(value)

        return checksum % number_of_responses

    # -------------------------------------------------------------
    # Control field selection
    # -------------------------------------------------------------

    def pick_control_field(self, data):

        for field in CONTROL_FIELD_PRIORITY:
            if field in data:
                return field

        # First string field

        for key, value in data.items():
            if isinstance(value, str):
                return key

        # First field

        if len(data):
            return next(iter(data.keys()))

        return None

    # -------------------------------------------------------------
    # Inline override
    # -------------------------------------------------------------

    def extract_override(self, value: str):

        if "#" not in value:
            return None

        try:
            return int(value.split("#")[-1])
        except Exception:
            return None

    # -------------------------------------------------------------
    # String checksum
    # -------------------------------------------------------------

    def string_checksum(self, text: str) -> int:
        """
        Stable checksum.

        Uses SHA256 instead of ord() so that

        abc
        acb

        do NOT collide.
        """

        digest = hashlib.sha256(text.encode("utf8")).digest()

        return int.from_bytes(digest[:8], "big")

    # -------------------------------------------------------------
    # Whole JSON checksum
    # -------------------------------------------------------------

    def json_checksum(self, data):

        text = str(sorted(data.items()))

        return self.string_checksum(text)


# -----------------------------------------------------------------
# Convenience singleton
# -----------------------------------------------------------------

checksum_engine = ChecksumEngine()


# -----------------------------------------------------------------
# Self test
# -----------------------------------------------------------------

if __name__ == "__main__":

    class DummyHeaders(dict):
        pass

    headers = DummyHeaders()

    request = {
        "name": "baskar"
    }

    idx = checksum_engine.choose_response(
        request,
        headers,
        5,
    )

    print("Response Index =", idx)

    request["name"] = "baskar#3"

    idx = checksum_engine.choose_response(
        request,
        headers,
        5,
    )

    print("Forced Response =", idx)

    headers["X-Mock-Response"] = "4"

    idx = checksum_engine.choose_response(
        request,
        headers,
        5,
    )

    print("Header Override =", idx)
