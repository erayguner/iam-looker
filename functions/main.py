"""Cloud Function entry points for Looker automation.

This module provides all Cloud Function handlers for Looker operations including:
- Project provisioning and decommissioning
- User and group management
- Connection management
- LookML project operations
- Content management (dashboards, schedules)
"""

import json
from typing import Any, Dict

from iam_looker.provisioner import LookerProvisioner
from iam_looker.exceptions import ProvisioningError, ValidationError
from iam_looker.models import ProvisionResult, ProvisionPayload
from iam_looker.settings import settings
from iam_looker.handler import provisioner as shared_provisioner

try:
    import looker_sdk
    _sdk = looker_sdk.init40()
except Exception:
    _sdk = None

provisioner = shared_provisioner or (LookerProvisioner(_sdk) if _sdk else None)


# ============================================================================
# CORE PROVISIONING FUNCTIONS
# ============================================================================

def provision_looker_project(event: Dict[str, Any], context: Any = None):
    """Complete project provisioning workflow.

    Args:
        event: {projectId, groupEmail, templateDashboardIds (optional)}
        context: Cloud Function context

    Returns:
        Provision result with status, IDs, and correlation ID
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        payload = ProvisionPayload(**event)
    except Exception as e:
        return ProvisionResult(
            status="validation_error",
            projectId=event.get("projectId", ""),
            groupEmail=event.get("groupEmail", ""),
            error=str(e)
        ).model_dump()

    template_ids = payload.templateDashboardIds or settings.template_dashboard_ids

    try:
        result = provisioner.provision(
            project_id=payload.projectId,
            group_email=payload.groupEmail,
            template_dashboard_ids=template_ids
        )
        return ProvisionResult(status="ok", **result).model_dump()
    except (ProvisioningError, ValidationError) as e:
        return ProvisionResult(
            status="error",
            projectId=payload.projectId,
            groupEmail=payload.groupEmail,
            error=str(e)
        ).model_dump()


def decommission_looker_project(event: Dict[str, Any], context: Any = None):
    """Decommission Looker project resources.

    Args:
        event: {
            projectId,
            archiveFolder (bool, default True),
            deleteDashboards (bool, default False),
            deleteSchedules (bool, default False)
        }
        context: Cloud Function context

    Returns:
        Decommission result with counts of archived/deleted resources
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    project_id = event.get("projectId", "")
    archive_folder = event.get("archiveFolder", True)
    delete_dashboards = event.get("deleteDashboards", False)
    delete_schedules = event.get("deleteSchedules", False)

    try:
        result = provisioner.decommission_project(
            project_id=project_id,
            archive_folder=archive_folder,
            delete_dashboards=delete_dashboards,
            delete_schedules=delete_schedules
        )
        return {"status": "ok", **result}
    except ProvisioningError as e:
        return {"status": "error", "projectId": project_id, "error": str(e)}


# ============================================================================
# GROUP & USER MANAGEMENT FUNCTIONS
# ============================================================================

def add_group_to_saml(event: Dict[str, Any], context: Any = None):
    """Add group to SAML configuration.

    Args:
        event: {groupEmail}
        context: Cloud Function context

    Returns:
        Result with group ID
    """
    group_email = event.get("groupEmail") or ""
    if not provisioner:
        return {"status": "sdk_unavailable", "groupEmail": group_email}

    try:
        gid = provisioner.ensure_group(group_email)
        provisioner.ensure_saml_group_mapping(gid, group_email)
        return ProvisionResult(
            status="ok",
            projectId="",
            groupEmail=group_email,
            groupId=gid
        ).model_dump()
    except (ProvisioningError, ValidationError) as e:
        return ProvisionResult(
            status="error",
            projectId="",
            groupEmail=group_email,
            error=str(e)
        ).model_dump()


def add_user_to_group(event: Dict[str, Any], context: Any = None):
    """Add user to Looker group.

    Args:
        event: {groupId, userId}
        context: Cloud Function context

    Returns:
        Result with success status
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    group_id = event.get("groupId")
    user_id = event.get("userId")

    try:
        added = provisioner.add_user_to_group(int(group_id), int(user_id))
        return {
            "status": "ok",
            "groupId": group_id,
            "userId": user_id,
            "added": added
        }
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


def create_user(event: Dict[str, Any], context: Any = None):
    """Create Looker user.

    Args:
        event: {email, firstName, lastName, roleIds (optional)}
        context: Cloud Function context

    Returns:
        Result with user ID
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        user_id = provisioner.create_user(
            email=event.get("email", ""),
            first_name=event.get("firstName", ""),
            last_name=event.get("lastName", ""),
            role_ids=event.get("roleIds")
        )
        return {"status": "ok", "userId": user_id, "email": event.get("email")}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


def bulk_provision_users(event: Dict[str, Any], context: Any = None):
    """Provision multiple users.

    Args:
        event: {users: [{email, firstName, lastName}], groupId (optional)}
        context: Cloud Function context

    Returns:
        Result with list of user IDs
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    users = event.get("users", [])
    group_id = event.get("groupId")

    try:
        user_ids = provisioner.bulk_provision_users(users, group_id=group_id)
        return {"status": "ok", "userIds": user_ids, "count": len(user_ids)}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


# ============================================================================
# FOLDER & CONTENT MANAGEMENT FUNCTIONS
# ============================================================================

def create_project_folder(event: Dict[str, Any], context: Any = None):
    """Create project folder.

    Args:
        event: {projectId, parentId (optional)}
        context: Cloud Function context

    Returns:
        Result with folder ID
    """
    project_id = event.get("projectId") or ""
    if not provisioner:
        return {"status": "sdk_unavailable", "projectId": project_id}

    try:
        fid = provisioner.ensure_project_folder(
            project_id,
            parent_id=event.get("parentId")
        )
        return {"status": "ok", "projectId": project_id, "folderId": fid}
    except ProvisioningError as e:
        return {"status": "error", "projectId": project_id, "error": str(e)}


def create_dashboard_from_template(event: Dict[str, Any], context: Any = None):
    """Clone dashboard template.

    Args:
        event: {templateDashboardId, folderId, projectId}
        context: Cloud Function context

    Returns:
        Result with dashboard ID
    """
    project_id = event.get("projectId") or ""
    if not provisioner:
        return {"status": "sdk_unavailable", "projectId": project_id}

    try:
        did = provisioner.clone_dashboard_if_missing(
            int(event.get("templateDashboardId")),
            int(event.get("folderId")),
            project_id
        )
        return {"status": "ok", "projectId": project_id, "dashboardId": did}
    except (ProvisioningError, Exception) as e:
        return {"status": "error", "projectId": project_id, "error": str(e)}


def move_dashboard_to_folder(event: Dict[str, Any], context: Any = None):
    """Move dashboard to different folder.

    Args:
        event: {dashboardId, targetFolderId}
        context: Cloud Function context

    Returns:
        Result with success status
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        provisioner.move_content_to_folder(
            int(event.get("dashboardId")),
            int(event.get("targetFolderId"))
        )
        return {
            "status": "ok",
            "dashboardId": event.get("dashboardId"),
            "targetFolderId": event.get("targetFolderId")
        }
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


def create_scheduled_delivery(event: Dict[str, Any], context: Any = None):
    """Create scheduled dashboard delivery.

    Args:
        event: {
            dashboardId,
            name,
            cronSchedule,
            destinationEmails (list),
            pdfPaperSize (optional, default 'letter')
        }
        context: Cloud Function context

    Returns:
        Result with schedule plan ID
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        plan_id = provisioner.create_scheduled_plan(
            dashboard_id=int(event.get("dashboardId")),
            name=event.get("name", ""),
            cron_schedule=event.get("cronSchedule", ""),
            destination_emails=event.get("destinationEmails", []),
            pdf_paper_size=event.get("pdfPaperSize", "letter")
        )
        return {"status": "ok", "scheduledPlanId": plan_id}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


# ============================================================================
# CONNECTION MANAGEMENT FUNCTIONS
# ============================================================================

def create_connection(event: Dict[str, Any], context: Any = None):
    """Create database connection.

    Args:
        event: {
            name,
            host,
            database,
            dialectName (default 'bigquery_standard_sql'),
            username (optional),
            password (optional),
            serviceAccountJson (optional)
        }
        context: Cloud Function context

    Returns:
        Result with connection name
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        conn_name = provisioner.create_connection(
            name=event.get("name", ""),
            host=event.get("host", ""),
            database=event.get("database", ""),
            dialect_name=event.get("dialectName", "bigquery_standard_sql"),
            username=event.get("username"),
            password=event.get("password"),
            service_account_json=event.get("serviceAccountJson")
        )
        return {"status": "ok", "connectionName": conn_name}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


def test_connection(event: Dict[str, Any], context: Any = None):
    """Test database connection.

    Args:
        event: {connectionName}
        context: Cloud Function context

    Returns:
        Test result with status and message
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        result = provisioner.test_connection(event.get("connectionName", ""))
        return {"status": "ok", **result}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


def delete_connection(event: Dict[str, Any], context: Any = None):
    """Delete database connection.

    Args:
        event: {connectionName}
        context: Cloud Function context

    Returns:
        Result with success status
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        provisioner.delete_connection(event.get("connectionName", ""))
        return {"status": "ok", "connectionName": event.get("connectionName")}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


def list_connections(event: Dict[str, Any], context: Any = None):
    """List all database connections.

    Args:
        event: {} (no parameters required)
        context: Cloud Function context

    Returns:
        List of connections with name, dialect, host
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        connections = provisioner.list_connections()
        return {"status": "ok", "connections": connections, "count": len(connections)}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


# ============================================================================
# LOOKML PROJECT MANAGEMENT FUNCTIONS
# ============================================================================

def create_lookml_project(event: Dict[str, Any], context: Any = None):
    """Create LookML project.

    Args:
        event: {name, gitRemoteUrl, gitServiceName (default 'github')}
        context: Cloud Function context

    Returns:
        Result with project ID
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        project_id = provisioner.create_project(
            name=event.get("name", ""),
            git_remote_url=event.get("gitRemoteUrl", ""),
            git_service_name=event.get("gitServiceName", "github")
        )
        return {"status": "ok", "projectId": project_id}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


def deploy_project_to_production(event: Dict[str, Any], context: Any = None):
    """Deploy LookML project to production.

    Args:
        event: {projectId}
        context: Cloud Function context

    Returns:
        Result with success status
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        provisioner.deploy_project_to_production(event.get("projectId", ""))
        return {"status": "ok", "projectId": event.get("projectId")}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


def validate_project(event: Dict[str, Any], context: Any = None):
    """Validate LookML project.

    Args:
        event: {projectId}
        context: Cloud Function context

    Returns:
        Validation result with errors and warnings
    """
    if not provisioner:
        return {"status": "sdk_unavailable"}

    try:
        result = provisioner.validate_project(event.get("projectId", ""))
        return {"status": "ok", **result}
    except ProvisioningError as e:
        return {"status": "error", "error": str(e)}


# ============================================================================
# LOCAL RUNNER
# ============================================================================

if __name__ == "__main__":
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else '{}'
    event = json.loads(raw)
    # Default to orchestration function
    print(json.dumps(provision_looker_project(event), indent=2))
