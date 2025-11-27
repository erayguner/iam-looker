import base64
import json
import logging
from typing import Any

from .exceptions import ProvisioningError, ValidationError
from .models import ProvisionPayload, ProvisionResult
from .provisioner import LookerProvisioner
from .settings import settings

logger = logging.getLogger("iam_looker.handler")

try:
    import looker_sdk
    _sdk = looker_sdk.init40()
except Exception:
    _sdk = None

provisioner = LookerProvisioner(_sdk) if _sdk else None
PUBSUB_DATA_KEY = "data"

def _decode_pubsub(event: dict[str, Any]) -> dict[str, Any]:
    if PUBSUB_DATA_KEY in event:
        raw = event[PUBSUB_DATA_KEY]
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
            return json.loads(decoded)
        except Exception as e:
            raise ValidationError(f"Failed to decode pubsub data: {e}")
    return event


def handle_event(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    payload_dict = _decode_pubsub(event)
    try:
        payload = ProvisionPayload(**payload_dict)
    except Exception as e:
        return ProvisionResult(status="validation_error", projectId=payload_dict.get("projectId", ""), groupEmail=payload_dict.get("groupEmail", ""), error=str(e)).model_dump()
    template_ids = payload.templateDashboardIds or settings.template_dashboard_ids
    if provisioner is None:
        return ProvisionResult(status="sdk_unavailable", projectId=payload.projectId, groupEmail=payload.groupEmail).model_dump()
    try:
        result = provisioner.provision(project_id=payload.projectId, group_email=payload.groupEmail, template_dashboard_ids=template_ids)
        return ProvisionResult(status="ok", **result).model_dump()
    except ValidationError as ve:
        return ProvisionResult(status="validation_error", projectId=payload.projectId, groupEmail=payload.groupEmail, error=str(ve)).model_dump()
    except ProvisioningError as pe:
        return ProvisionResult(status="provisioning_error", projectId=payload.projectId, groupEmail=payload.groupEmail, error=str(pe)).model_dump()
    except Exception as e:
        logger.exception("Unhandled error")
        return ProvisionResult(status="unknown_error", projectId=payload.projectId, groupEmail=payload.groupEmail, error=str(e)).model_dump()
