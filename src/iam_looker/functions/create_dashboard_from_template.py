from __future__ import annotations

from typing import Any

from ..exceptions import ProvisioningError
from ..handler import provisioner
from ..models import ProvisionResult


def create_dashboard_from_template(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    template_id = int(event.get("templateDashboardId", 0))
    folder_id = int(event.get("folderId", 0))
    project_id = event.get("projectId", "")
    group_email = event.get("groupEmail", "")
    if provisioner is None:
        return ProvisionResult(status="sdk_unavailable", projectId=project_id, groupEmail=group_email).model_dump()
    try:
        did = provisioner.clone_dashboard_if_missing(template_id, folder_id, project_id)
        return ProvisionResult(status="ok", projectId=project_id, groupEmail=group_email, dashboardIds=[did]).model_dump()
    except ProvisioningError as e:
        return ProvisionResult(status="error", projectId=project_id, groupEmail=group_email, error=str(e)).model_dump()
