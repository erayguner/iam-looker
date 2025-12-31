from __future__ import annotations

from typing import Any

from ..exceptions import ProvisioningError
from ..handler import provisioner
from ..models import ProvisionResult


def create_project_folder(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    project_id = event.get("projectId", "")
    group_email = event.get("groupEmail", "")
    if provisioner is None:
        return ProvisionResult(
            status="sdk_unavailable", projectId=project_id, groupEmail=group_email
        ).model_dump()
    try:
        fid = provisioner.ensure_project_folder(project_id)
        return ProvisionResult(
            status="ok", projectId=project_id, groupEmail=group_email, folderId=fid
        ).model_dump()
    except ProvisioningError as e:
        return ProvisionResult(
            status="error", projectId=project_id, groupEmail=group_email, error=str(e)
        ).model_dump()
