from __future__ import annotations

import base64
import json
import logging
from typing import Any

logger = logging.getLogger("cloud_functions.common")

PUBSUB_DATA_KEY = "data"


def decode_pubsub(event: dict[str, Any]) -> dict[str, Any]:
    if PUBSUB_DATA_KEY in event:
        raw = event[PUBSUB_DATA_KEY]
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
            return json.loads(decoded)
        except Exception as e:
            logger.warning("pubsub.decode_failed", extra={"error": str(e)})
            return {}
    return event
