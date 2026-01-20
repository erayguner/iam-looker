import logging
import uuid

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .exceptions import ProvisioningError, ValidationError

logger = logging.getLogger("iam_looker.provisioner")


class LookerProvisioner:
    def __init__(self, sdk):
        self.sdk = sdk

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ProvisioningError),
    )
    def ensure_group(self, group_email: str) -> int:
        try:
            existing = self.sdk.search_groups(name=group_email) or []
        except Exception as e:
            raise ProvisioningError(f"search_groups failed: {e}")
        if existing:
            gid = getattr(existing[0], "id", None)
            logger.info(
                "Reusing group",
                extra={"event": "group.reuse", "groupEmail": group_email, "groupId": gid},
            )
            return int(gid)
        body = {"name": group_email}
        try:
            created = self.sdk.create_group(body=body)
        except Exception as e:
            raise ProvisioningError(f"create_group failed: {e}")
        gid = getattr(created, "id", None)
        logger.info(
            "Created group",
            extra={"event": "group.create", "groupEmail": group_email, "groupId": gid},
        )
        return int(gid)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ProvisioningError),
    )
    def ensure_project_folder(self, project_id: str) -> int:
        folder_name = f"Project: {project_id}"
        try:
            existing = self.sdk.search_folders(name=folder_name) or []
        except Exception as e:
            raise ProvisioningError(f"search_folders failed: {e}")
        if existing:
            fid = getattr(existing[0], "id", None)
            logger.info("Reusing folder", extra={"event": "folder.reuse", "folderId": fid})
            return int(fid)
        body = {"name": folder_name}
        try:
            created = self.sdk.create_folder(body=body)
        except Exception as e:
            raise ProvisioningError(f"create_folder failed: {e}")
        fid = getattr(created, "id", None)
        logger.info("Created folder", extra={"event": "folder.create", "folderId": fid})
        return int(fid)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ProvisioningError),
    )
    def clone_dashboard_if_missing(
        self, template_dashboard_id: int, target_folder_id: int, project_id: str
    ) -> int | None:
        try:
            template = self.sdk.dashboard(template_dashboard_id)
        except Exception as e:
            raise ProvisioningError(f"dashboard fetch failed: {e}")
        base_title = getattr(template, "title", f"dashboard-{template_dashboard_id}")
        desired_title = f"{base_title} (project: {project_id})"
        try:
            existing = self.sdk.search_dashboards(title=desired_title) or []
        except Exception:
            existing = []
        if existing:
            did = getattr(existing[0], "id", None)
            logger.info("Reusing dashboard", extra={"event": "dashboard.reuse", "dashboardId": did})
            return int(did)
        body = {
            "dashboard_id": template_dashboard_id,
            "name": desired_title,
            "folder_id": target_folder_id,
        }
        try:
            cloned = self.sdk.dashboard_copy(template_dashboard_id, body=body)
        except Exception as e:
            raise ProvisioningError(f"dashboard_copy failed: {e}")
        did = getattr(cloned, "id", None)
        logger.info("Cloned dashboard", extra={"event": "dashboard.clone", "dashboardId": did})
        return int(did)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ProvisioningError),
    )
    def ensure_saml_group_mapping(self, group_id: int, group_email: str) -> None:
        try:
            saml_cfg = self.sdk.saml_config()
        except Exception as e:
            raise ProvisioningError(f"saml_config failed: {e}")
        groups_field = getattr(saml_cfg, "groups", []) or []
        for g in groups_field:
            if getattr(g, "name", None) == group_email:
                logger.info(
                    "Reusing SAML mapping",
                    extra={"event": "saml.group.reuse", "groupEmail": group_email},
                )
                return
        new_group_entry = {"name": group_email, "id": group_id}
        update_body = {"groups": list(groups_field) + [new_group_entry]}
        try:
            self.sdk.update_saml_config(body=update_body)
        except Exception as e:
            raise ProvisioningError(f"update_saml_config failed: {e}")
        logger.info(
            "Added SAML group", extra={"event": "saml.group.add", "groupEmail": group_email}
        )

    def provision(
        self, project_id: str, group_email: str, template_dashboard_ids: list[int]
    ) -> dict:
        if not project_id or not group_email:
            raise ValidationError("Missing project_id or group_email")
        correlation_id = str(uuid.uuid4())
        logger.info(
            "Provision start",
            extra={
                "event": "provision.start",
                "projectId": project_id,
                "correlationId": correlation_id,
            },
        )
        group_id = self.ensure_group(group_email)
        self.ensure_saml_group_mapping(group_id, group_email)
        folder_id = self.ensure_project_folder(project_id)
        cloned_ids: list[int] = []
        for dash_id in template_dashboard_ids:
            cloned = self.clone_dashboard_if_missing(dash_id, folder_id, project_id)
            if cloned:
                cloned_ids.append(cloned)
        result = {
            "projectId": project_id,
            "groupEmail": group_email,
            "groupId": group_id,
            "folderId": folder_id,
            "dashboardIds": cloned_ids,
            "correlationId": correlation_id,
        }
        logger.info("Provision complete", extra={"event": "provision.complete", **result})
        return result
