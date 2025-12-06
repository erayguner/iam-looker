from __future__ import annotations

from typing import Any

from iam_looker.exceptions import ProvisioningError
from iam_looker.handler import provisioner
from iam_looker.models import ProvisionResult

from .common import decode_pubsub

# Single responsibility: clone a dashboard template into a project-specific folder.


def create_dashboard_from_template(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    payload = decode_pubsub(event)
    template_id = int(payload.get("templateDashboardId", 0))
    folder_id = int(payload.get("folderId", 0))
    project_id = payload.get("projectId", "")
    group_email = payload.get("groupEmail", "")
    if provisioner is None:
        return ProvisionResult(
            status="sdk_unavailable", projectId=project_id, groupEmail=group_email
        ).model_dump()
    try:
        did = provisioner.clone_dashboard_if_missing(template_id, folder_id, project_id)
        return ProvisionResult(
            status="ok", projectId=project_id, groupEmail=group_email, dashboardIds=[did]
        ).model_dump()
    except ProvisioningError as e:
        return ProvisionResult(
            status="error", projectId=project_id, groupEmail=group_email, error=str(e)
        ).model_dump()
