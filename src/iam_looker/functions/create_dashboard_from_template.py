from iam_looker.handler import provisioner
from iam_looker.models import ProvisionResult
from iam_looker.exceptions import ProvisioningError

def create_dashboard_from_template(event, context=None):
    if provisioner is None:
        return {"status": "sdk_unavailable"}
    template_id = int(event.get("templateDashboardId", 0))
    folder_id = int(event.get("folderId", 0))
    project_id = event.get("projectId", "")
    group_email = event.get("groupEmail", "")
    try:
        did = provisioner.clone_dashboard_if_missing(template_id, folder_id, project_id)
        return ProvisionResult(status="ok", projectId=project_id, groupEmail=group_email, dashboardIds=[did]).model_dump()
    except ProvisioningError as e:
        return ProvisionResult(status="error", projectId=project_id, groupEmail=group_email, error=str(e)).model_dump()

