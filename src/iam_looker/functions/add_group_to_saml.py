from __future__ import annotations

from typing import Any

from ..exceptions import ProvisioningError
from ..handler import provisioner
from ..models import ProvisionResult


def add_group_to_saml(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    group_email = event.get("groupEmail", "")
    project_id = event.get("projectId", "")
    if provisioner is None:
        return ProvisionResult(
            status="sdk_unavailable", projectId=project_id, groupEmail=group_email
        ).model_dump()
    try:
        gid = provisioner.ensure_group(group_email)
        provisioner.ensure_saml_group_mapping(gid, group_email)
        return ProvisionResult(
            status="ok", projectId=project_id, groupEmail=group_email, groupId=gid
        ).model_dump()
    except ProvisioningError as e:
        return ProvisionResult(
            status="error", projectId=project_id, groupEmail=group_email, error=str(e)
        ).model_dump()
