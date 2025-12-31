import logging
import uuid

# NOTE: Legacy implementation retained; new code resides in iam_looker.provisioner.LookerProvisioner

logger = logging.getLogger("looker_provisioner")
logging.basicConfig(level=logging.INFO)


class ProvisioningError(Exception):
    pass


class ValidationError(Exception):
    pass


class LookerProvisioner:
    def __init__(self, sdk):
        self.sdk = sdk

    # GROUP HANDLING
    def ensure_group(self, group_email: str) -> int:
        """Find or create group by email. Returns group ID."""
        search = []
        try:
            search = self.sdk.search_groups(name=group_email) or []
        except Exception as e:
            raise ProvisioningError(f"search_groups failed: {e}")
        if search:
            gid = getattr(search[0], "id", None)
            logger.info({"event": "group.reuse", "groupEmail": group_email, "groupId": gid})
            return int(gid)
        body = {"name": group_email}
        try:
            created = self.sdk.create_group(body=body)
        except Exception as e:
            raise ProvisioningError(f"create_group failed: {e}")
        gid = getattr(created, "id", None)
        logger.info({"event": "group.create", "groupEmail": group_email, "groupId": gid})
        return int(gid)

    # FOLDER HANDLING
    def ensure_project_folder(self, project_id: str) -> int:
        folder_name = f"Project: {project_id}"
        try:
            existing = self.sdk.search_folders(name=folder_name) or []
        except Exception as e:
            raise ProvisioningError(f"search_folders failed: {e}")
        if existing:
            fid = getattr(existing[0], "id", None)
            logger.info({"event": "folder.reuse", "folderId": fid})
            return int(fid)
        body = {"name": folder_name}
        try:
            created = self.sdk.create_folder(body=body)
        except Exception as e:
            raise ProvisioningError(f"create_folder failed: {e}")
        fid = getattr(created, "id", None)
        logger.info({"event": "folder.create", "folderId": fid})
        return int(fid)

    # DASHBOARD CLONE
    def clone_dashboard_if_missing(
        self, template_dashboard_id: int, target_folder_id: int, project_id: str
    ) -> int | None:
        try:
            template = self.sdk.dashboard(template_dashboard_id)
        except Exception as e:
            raise ProvisioningError(f"dashboard fetch failed: {e}")
        base_title = getattr(template, "title", f"dashboard-{template_dashboard_id}")
        desired_title = f"{base_title} (project: {project_id})"
        # Search attempt (Looker search API might differ; placeholder logic)
        try:
            existing = self.sdk.search_dashboards(title=desired_title) or []
        except Exception:
            existing = []
        if existing:
            did = getattr(existing[0], "id", None)
            logger.info({"event": "dashboard.reuse", "dashboardId": did})
            return int(did)
        copy_body = {
            "dashboard_id": template_dashboard_id,
            "name": desired_title,
            "folder_id": target_folder_id,
        }
        try:
            cloned = self.sdk.dashboard_copy(template_dashboard_id, body=copy_body)
        except Exception as e:
            raise ProvisioningError(f"dashboard_copy failed: {e}")
        did = getattr(cloned, "id", None)
        logger.info({"event": "dashboard.clone", "dashboardId": did})
        return int(did)

    # SAML CONFIG (placeholder, field names may differ)
    def ensure_saml_group_mapping(self, group_id: int, group_email: str) -> None:
        try:
            saml_cfg = self.sdk.saml_config()
        except Exception as e:
            raise ProvisioningError(f"saml_config fetch failed: {e}")
        groups_field = getattr(saml_cfg, "groups", []) or []
        # naive check
        for g in groups_field:
            if getattr(g, "name", None) == group_email:
                logger.info({"event": "saml.group.reuse", "groupEmail": group_email})
                return
        # Append logic - Actual model needs verification; placeholder uses dict
        new_group_entry = {"name": group_email, "id": group_id}
        updated_groups = list(groups_field) + [new_group_entry]
        update_body = {"groups": updated_groups}
        try:
            self.sdk.update_saml_config(body=update_body)
        except Exception as e:
            raise ProvisioningError(f"update_saml_config failed: {e}")
        logger.info({"event": "saml.group.add", "groupEmail": group_email})

    def provision(
        self,
        project_id: str,
        group_email: str,
        template_dashboard_ids: list[int],
        template_folder_id: int | None,
    ) -> dict:
        if not project_id or not group_email or "@" not in group_email:
            raise ValidationError("Invalid project_id or group_email")
        correlation_id = str(uuid.uuid4())
        logger.info(
            {"event": "provision.start", "projectId": project_id, "correlationId": correlation_id}
        )
        group_id = self.ensure_group(group_email)
        self.ensure_saml_group_mapping(group_id, group_email)
        folder_id = self.ensure_project_folder(project_id)
        cloned_dashboards = []
        for dash_id in template_dashboard_ids:
            try:
                cloned_id = self.clone_dashboard_if_missing(dash_id, folder_id, project_id)
                if cloned_id:
                    cloned_dashboards.append(cloned_id)
            except ProvisioningError as e:
                logger.error(
                    {
                        "event": "dashboard.clone.error",
                        "dashboardTemplateId": dash_id,
                        "error": str(e),
                    }
                )
                raise
        result = {
            "projectId": project_id,
            "groupEmail": group_email,
            "groupId": group_id,
            "folderId": folder_id,
            "dashboardIds": cloned_dashboards,
            "correlationId": correlation_id,
        }
        logger.info({"event": "provision.complete", **result})
        return result
