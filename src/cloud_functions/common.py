from __future__ import annotations
import base64, json, logging
from typing import Any, Dict

logger = logging.getLogger("cloud_functions.common")

PUBSUB_DATA_KEY = "data"

def decode_pubsub(event: Dict[str, Any]) -> Dict[str, Any]:
    if PUBSUB_DATA_KEY in event:
        raw = event[PUBSUB_DATA_KEY]
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
            return json.loads(decoded)
        except Exception as e:
            logger.warning("pubsub.decode_failed", extra={"error": str(e)})
            return {}
    return event

