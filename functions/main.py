import json
from typing import Any

from iam_looker.exceptions import ProvisioningError, ValidationError
from iam_looker.handler import provisioner as shared_provisioner
from iam_looker.models import ProvisionPayload, ProvisionResult
from iam_looker.provisioner import LookerProvisioner
from iam_looker.settings import settings

try:
    import looker_sdk
    _sdk = looker_sdk.init40()
except Exception:
    _sdk = None

provisioner = shared_provisioner or (LookerProvisioner(_sdk) if _sdk else None)

# Single-task functions

def add_group_to_saml(event: dict[str, Any], context: Any = None):
    group_email = event.get("groupEmail") or ""
    if not provisioner:
        return {"status": "sdk_unavailable", "groupEmail": group_email}
    try:
        gid = provisioner.ensure_group(group_email)
        provisioner.ensure_saml_group_mapping(gid, group_email)
        return ProvisionResult(status="ok", projectId="", groupEmail=group_email, groupId=gid).model_dump()
    except (ProvisioningError, ValidationError) as e:
        return ProvisionResult(status="error", projectId="", groupEmail=group_email, error=str(e)).model_dump()


def create_project_folder(event: dict[str, Any], context: Any = None):
    project_id = event.get("projectId") or ""
    group_email = event.get("groupEmail") or ""
    if not provisioner:
        return {"status": "sdk_unavailable", "projectId": project_id}
    try:
        fid = provisioner.ensure_project_folder(project_id)
        return ProvisionResult(status="ok", projectId=project_id, groupEmail=group_email, folderId=fid).model_dump()
    except ProvisioningError as e:
        return ProvisionResult(status="error", projectId=project_id, groupEmail=group_email, error=str(e)).model_dump()


def create_dashboard_from_template(event: dict[str, Any], context: Any = None):
    project_id = event.get("projectId") or ""
    group_email = event.get("groupEmail") or ""
    template_id = event.get("templateDashboardId")
    folder_id = event.get("folderId")
    if not provisioner:
        return {"status": "sdk_unavailable", "projectId": project_id}
    try:
        did = provisioner.clone_dashboard_if_missing(int(template_id), int(folder_id), project_id)
        return ProvisionResult(status="ok", projectId=project_id, groupEmail=group_email, dashboardIds=[did]).model_dump()
    except (ProvisioningError, Exception) as e:
        return ProvisionResult(status="error", projectId=project_id, groupEmail=group_email, error=str(e)).model_dump()


def provision_looker_project(event: dict[str, Any], context: Any = None):
    if not provisioner:
        return {"status": "sdk_unavailable"}
    try:
        payload = ProvisionPayload(**event)
    except Exception as e:
        return ProvisionResult(status="validation_error", projectId=event.get("projectId", ""), groupEmail=event.get("groupEmail", ""), error=str(e)).model_dump()
    template_ids = payload.templateDashboardIds or settings.template_dashboard_ids
    try:
        result = provisioner.provision(project_id=payload.projectId, group_email=payload.groupEmail, template_dashboard_ids=template_ids)
        return ProvisionResult(status="ok", **result).model_dump()
    except (ProvisioningError, ValidationError) as e:
        return ProvisionResult(status="error", projectId=payload.projectId, groupEmail=payload.groupEmail, error=str(e)).model_dump()

# Local runner
if __name__ == "__main__":
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else '{}'
    event = json.loads(raw)
    # Default to orchestration function
    print(json.dumps(provision_looker_project(event), indent=2))

