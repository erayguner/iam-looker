from __future__ import annotations

from typing import Any

from iam_looker.exceptions import ProvisioningError
from iam_looker.handler import provisioner
from iam_looker.models import ProvisionResult

from .common import decode_pubsub

# Single responsibility: ensure group exists and mapped in SAML; returns result payload.

def add_group_to_saml(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    payload = decode_pubsub(event)
    group_email = payload.get("groupEmail", "")
    project_id = payload.get("projectId", "")
    if provisioner is None:
        return ProvisionResult(status="sdk_unavailable", projectId=project_id, groupEmail=group_email).model_dump()
    try:
        gid = provisioner.ensure_group(group_email)
        provisioner.ensure_saml_group_mapping(gid, group_email)
        return ProvisionResult(status="ok", projectId=project_id, groupEmail=group_email, groupId=gid).model_dump()
    except ProvisioningError as e:
        return ProvisionResult(status="error", projectId=project_id, groupEmail=group_email, error=str(e)).model_dump()

