from __future__ import annotations

from typing import Any

from iam_looker.exceptions import ProvisioningError
from iam_looker.handler import provisioner
from iam_looker.models import ProvisionResult

from .common import decode_pubsub

# Single responsibility: create or reuse a project folder.

def create_project_folder(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    payload = decode_pubsub(event)
    project_id = payload.get("projectId", "")
    group_email = payload.get("groupEmail", "")
    if provisioner is None:
        return ProvisionResult(status="sdk_unavailable", projectId=project_id, groupEmail=group_email).model_dump()
    try:
        fid = provisioner.ensure_project_folder(project_id)
        return ProvisionResult(status="ok", projectId=project_id, groupEmail=group_email, folderId=fid).model_dump()
    except ProvisioningError as e:
        return ProvisionResult(status="error", projectId=project_id, groupEmail=group_email, error=str(e)).model_dump()

