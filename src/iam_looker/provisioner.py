"""Looker provisioning and automation orchestration.

This module provides comprehensive automation for Looker project lifecycle management,
including project creation, user/group provisioning, connection management, content
deployment, and decommissioning.
"""

import logging
from typing import Any
import uuid

from .exceptions import ProvisioningError, ValidationError

logger = logging.getLogger("iam_looker.provisioner")


class LookerProvisioner:
    """Orchestrates Looker API operations for complete project lifecycle management.

    Provides idempotent operations for:
    - Group and user provisioning
    - Project and folder management
    - Dashboard and content cloning
    - Database connection management
    - LookML project operations
    - Decommissioning and cleanup
    """

    def __init__(self, sdk: Any) -> None:
        """Initialize provisioner with Looker SDK client.

        Args:
            sdk: Initialized Looker SDK client (looker_sdk.init40())
        """
        self.sdk = sdk

    # ============================================================================
    # GROUP & USER MANAGEMENT
    # ============================================================================

    def ensure_group(self, group_email: str) -> int:
        """Find or create Looker group by email/name.

        Args:
            group_email: Group email or name

        Returns:
            Group ID (int)

        Raises:
            ProvisioningError: If group search or creation fails
        """
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
            if gid is None:
                raise ProvisioningError(f"Group {group_email} found but has no ID")
            return int(gid)

        body = {"name": group_email}
        try:
            created = self.sdk.create_group(body=body)
        except Exception as e:
            raise ProvisioningError(f"create_group failed: {e}")

        gid = getattr(created, "id", None)
        if gid is None:
            raise ProvisioningError(f"Created group {group_email} but no ID returned")
        logger.info(
            "Created group",
            extra={"event": "group.create", "groupEmail": group_email, "groupId": gid},
        )
        return int(gid)

    def add_user_to_group(self, group_id: int, user_id: int) -> bool:
        """Add user to Looker group.

        Args:
            group_id: Group ID
            user_id: User ID

        Returns:
            True if user was added, False if already in group

        Raises:
            ProvisioningError: If operation fails
        """
        try:
            # Check if user already in group
            group_users = self.sdk.all_group_users(group_id=group_id) or []
            existing_user_ids = [getattr(u, "id", None) for u in group_users]

            if user_id in existing_user_ids:
                logger.info(
                    "User already in group",
                    extra={"event": "group.user.exists", "groupId": group_id, "userId": user_id},
                )
                return False

            # Add user to group
            self.sdk.add_group_user(group_id=group_id, body={"user_id": user_id})
            logger.info(
                "Added user to group",
                extra={"event": "group.user.add", "groupId": group_id, "userId": user_id},
            )
            return True
        except Exception as e:
            raise ProvisioningError(f"add_group_user failed: {e}")

    def remove_user_from_group(self, group_id: int, user_id: int) -> bool:
        """Remove user from Looker group.

        Args:
            group_id: Group ID
            user_id: User ID

        Returns:
            True if user was removed

        Raises:
            ProvisioningError: If operation fails
        """
        try:
            self.sdk.delete_group_user(group_id=group_id, user_id=user_id)
            logger.info(
                "Removed user from group",
                extra={"event": "group.user.remove", "groupId": group_id, "userId": user_id},
            )
            return True
        except Exception as e:
            raise ProvisioningError(f"delete_group_user failed: {e}")

    def create_user(
        self, email: str, first_name: str, last_name: str, role_ids: list[int] | None = None
    ) -> int:
        """Create new Looker user.

        Args:
            email: User email address
            first_name: User first name
            last_name: User last name
            role_ids: Optional list of role IDs to assign

        Returns:
            User ID

        Raises:
            ProvisioningError: If user creation fails
        """
        body = {"email": email, "first_name": first_name, "last_name": last_name}

        try:
            user = self.sdk.create_user(body=body)
            user_id = getattr(user, "id", None)
            if user_id is None:
                raise ProvisioningError(f"Created user {email} but no ID returned")

            # Assign roles if provided
            if role_ids:
                self.sdk.set_user_roles(user_id=user_id, body=role_ids)

            logger.info(
                "Created user", extra={"event": "user.create", "userId": user_id, "email": email}
            )
            return int(user_id)
        except Exception as e:
            raise ProvisioningError(f"create_user failed: {e}")

    def bulk_provision_users(
        self, users: list[dict[str, Any]], group_id: int | None = None
    ) -> list[int]:
        """Provision multiple users and optionally add to group.

        Args:
            users: List of user dicts with email, first_name, last_name
            group_id: Optional group ID to add all users to

        Returns:
            List of created user IDs

        Raises:
            ProvisioningError: If any user creation fails
        """
        user_ids = []
        for user_data in users:
            user_id = self.create_user(
                email=user_data["email"],
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                role_ids=user_data.get("role_ids"),
            )
            user_ids.append(user_id)

            if group_id:
                self.add_user_to_group(group_id, user_id)

        logger.info(
            "Bulk provisioned users",
            extra={"event": "users.bulk_provision", "count": len(user_ids)},
        )
        return user_ids

    # ============================================================================
    # FOLDER & CONTENT MANAGEMENT
    # ============================================================================

    def ensure_project_folder(self, project_id: str, parent_id: str | None = None) -> int:
        """Find or create project folder with naming convention.

        Args:
            project_id: GCP project ID
            parent_id: Optional parent folder ID

        Returns:
            Folder ID

        Raises:
            ProvisioningError: If folder operations fail
        """
        folder_name = f"Project: {project_id}"
        try:
            existing = self.sdk.search_folders(name=folder_name) or []
        except Exception as e:
            raise ProvisioningError(f"search_folders failed: {e}")

        if existing:
            fid = getattr(existing[0], "id", None)
            if fid is None:
                raise ProvisioningError(f"Folder {folder_name} found but has no ID")
            logger.info("Reusing folder", extra={"event": "folder.reuse", "folderId": fid})
            return int(fid)

        body = {"name": folder_name}
        if parent_id:
            body["parent_id"] = parent_id

        try:
            created = self.sdk.create_folder(body=body)
        except Exception as e:
            raise ProvisioningError(f"create_folder failed: {e}")

        fid = getattr(created, "id", None)
        if fid is None:
            raise ProvisioningError(f"Created folder {folder_name} but no ID returned")
        logger.info("Created folder", extra={"event": "folder.create", "folderId": fid})
        return int(fid)

    def move_content_to_folder(self, dashboard_id: int, target_folder_id: int) -> bool:
        """Move dashboard to different folder.

        Args:
            dashboard_id: Dashboard ID to move
            target_folder_id: Target folder ID

        Returns:
            True if moved successfully

        Raises:
            ProvisioningError: If move fails
        """
        try:
            self.sdk.update_dashboard(
                dashboard_id=dashboard_id, body={"folder_id": target_folder_id}
            )
            logger.info(
                "Moved dashboard",
                extra={
                    "event": "dashboard.move",
                    "dashboardId": dashboard_id,
                    "targetFolderId": target_folder_id,
                },
            )
            return True
        except Exception as e:
            raise ProvisioningError(f"move dashboard failed: {e}")

    def clone_dashboard_if_missing(
        self, template_dashboard_id: int, target_folder_id: int, project_id: str
    ) -> int | None:
        """Clone dashboard template to project folder if not exists.

        Args:
            template_dashboard_id: Template dashboard ID
            target_folder_id: Target folder ID
            project_id: GCP project ID for naming

        Returns:
            Dashboard ID (existing or newly cloned)

        Raises:
            ProvisioningError: If dashboard operations fail
        """
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
            if did is None:
                raise ProvisioningError(f"Dashboard {desired_title} found but has no ID")
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
        if did is None:
            raise ProvisioningError(f"Cloned dashboard {desired_title} but no ID returned")
        logger.info("Cloned dashboard", extra={"event": "dashboard.clone", "dashboardId": did})
        return int(did)

    def create_scheduled_plan(
        self,
        dashboard_id: int,
        name: str,
        cron_schedule: str,
        destination_emails: list[str],
        pdf_paper_size: str = "letter",
    ) -> int:
        """Create scheduled dashboard delivery.

        Args:
            dashboard_id: Dashboard to schedule
            name: Schedule name
            cron_schedule: Cron expression (e.g., "0 9 * * *")
            destination_emails: List of recipient emails
            pdf_paper_size: Paper size for PDF (letter, A4, etc.)

        Returns:
            Scheduled plan ID

        Raises:
            ProvisioningError: If schedule creation fails
        """
        body = {
            "name": name,
            "dashboard_id": dashboard_id,
            "cron tab": cron_schedule,
            "enabled": True,
            "scheduled_plan_destination": [
                {
                    "format": "pdf",
                    "type": "email",
                    "address": email,
                    "parameters": {"pdf_paper_size": pdf_paper_size},
                }
                for email in destination_emails
            ],
        }

        try:
            plan = self.sdk.create_scheduled_plan(body=body)
            plan_id = getattr(plan, "id", None)
            if plan_id is None:
                raise ProvisioningError(f"Created scheduled plan but no ID returned")
            logger.info(
                "Created scheduled plan",
                extra={
                    "event": "scheduled_plan.create",
                    "planId": plan_id,
                    "dashboardId": dashboard_id,
                },
            )
            return int(plan_id)
        except Exception as e:
            raise ProvisioningError(f"create_scheduled_plan failed: {e}")

    # ============================================================================
    # CONNECTION MANAGEMENT
    # ============================================================================

    def create_connection(
        self,
        name: str,
        host: str,
        database: str,
        dialect_name: str = "bigquery_standard_sql",
        username: str | None = None,
        password: str | None = None,
        service_account_json: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Create database connection.

        Args:
            name: Connection name
            host: Database host
            database: Database name
            dialect_name: SQL dialect (bigquery_standard_sql, postgres, mysql, etc.)
            username: Database username (if applicable)
            password: Database password (if applicable)
            service_account_json: GCP service account JSON (for BigQuery)
            **kwargs: Additional connection parameters

        Returns:
            Connection name

        Raises:
            ProvisioningError: If connection creation fails
        """
        body = {
            "name": name,
            "host": host,
            "database": database,
            "dialect_name": dialect_name,
            **kwargs,
        }

        if username:
            body["username"] = username
        if password:
            body["password"] = password
        if service_account_json:
            body["service_account_json"] = service_account_json

        try:
            connection = self.sdk.create_connection(body=body)
            conn_name = getattr(connection, "name", None)
            logger.info(
                "Created connection",
                extra={"event": "connection.create", "connectionName": conn_name},
            )
            return str(conn_name)
        except Exception as e:
            raise ProvisioningError(f"create_connection failed: {e}")

    def test_connection(self, connection_name: str) -> dict[str, Any]:
        """Test database connection.

        Args:
            connection_name: Connection name to test

        Returns:
            Test result dict with status and message

        Raises:
            ProvisioningError: If test fails
        """
        try:
            result = self.sdk.test_connection(connection_name=connection_name)
            status = getattr(result, "status", None)
            message = getattr(result, "message", None)

            logger.info(
                "Tested connection",
                extra={
                    "event": "connection.test",
                    "connectionName": connection_name,
                    "status": status,
                },
            )

            return {"status": status, "message": message, "success": status == "success"}
        except Exception as e:
            raise ProvisioningError(f"test_connection failed: {e}")

    def update_connection(self, connection_name: str, **updates: Any) -> str:
        """Update connection configuration.

        Args:
            connection_name: Connection name to update
            **updates: Fields to update

        Returns:
            Connection name

        Raises:
            ProvisioningError: If update fails
        """
        try:
            self.sdk.update_connection(connection_name=connection_name, body=updates)
            logger.info(
                "Updated connection",
                extra={"event": "connection.update", "connectionName": connection_name},
            )
            return connection_name
        except Exception as e:
            raise ProvisioningError(f"update_connection failed: {e}")

    def delete_connection(self, connection_name: str) -> bool:
        """Delete database connection.

        Args:
            connection_name: Connection name to delete

        Returns:
            True if deleted

        Raises:
            ProvisioningError: If deletion fails
        """
        try:
            self.sdk.delete_connection(connection_name=connection_name)
            logger.info(
                "Deleted connection",
                extra={"event": "connection.delete", "connectionName": connection_name},
            )
            return True
        except Exception as e:
            raise ProvisioningError(f"delete_connection failed: {e}")

    def list_connections(self) -> list[dict[str, str]]:
        """List all database connections.

        Returns:
            List of connection dicts with name, dialect, host

        Raises:
            ProvisioningError: If listing fails
        """
        try:
            connections = self.sdk.all_connections() or []
            return [
                {
                    "name": getattr(conn, "name", ""),
                    "dialect": getattr(conn, "dialect_name", ""),
                    "host": getattr(conn, "host", ""),
                }
                for conn in connections
            ]
        except Exception as e:
            raise ProvisioningError(f"all_connections failed: {e}")

    # ============================================================================
    # LOOKML PROJECT MANAGEMENT
    # ============================================================================

    def create_project(
        self, name: str, git_remote_url: str, git_service_name: str | None = "github"
    ) -> str:
        """Create LookML project from git repository.

        Args:
            name: Project name
            git_remote_url: Git repository URL
            git_service_name: Git service (github, gitlab, bitbucket, etc.)

        Returns:
            Project ID

        Raises:
            ProvisioningError: If project creation fails
        """
        body = {
            "name": name,
            "git_remote_url": git_remote_url,
            "git_service_name": git_service_name,
        }

        try:
            project = self.sdk.create_project(body=body)
            project_id = getattr(project, "id", None)
            logger.info(
                "Created LookML project", extra={"event": "project.create", "projectId": project_id}
            )
            return str(project_id)
        except Exception as e:
            raise ProvisioningError(f"create_project failed: {e}")

    def deploy_project_to_production(self, project_id: str) -> bool:
        """Deploy LookML project to production.

        Args:
            project_id: Project ID to deploy

        Returns:
            True if deployment successful

        Raises:
            ProvisioningError: If deployment fails
        """
        try:
            self.sdk.deploy_to_production(project_id=project_id)
            logger.info(
                "Deployed project to production",
                extra={"event": "project.deploy", "projectId": project_id},
            )
            return True
        except Exception as e:
            raise ProvisioningError(f"deploy_to_production failed: {e}")

    def validate_project(self, project_id: str) -> dict[str, Any]:
        """Validate LookML project.

        Args:
            project_id: Project ID to validate

        Returns:
            Validation result dict with errors/warnings

        Raises:
            ProvisioningError: If validation check fails
        """
        try:
            result = self.sdk.validate_project(project_id=project_id)
            errors = getattr(result, "errors", []) or []
            warnings = getattr(result, "warnings", []) or []

            logger.info(
                "Validated project",
                extra={
                    "event": "project.validate",
                    "projectId": project_id,
                    "errorCount": len(errors),
                    "warningCount": len(warnings),
                },
            )

            return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
        except Exception as e:
            raise ProvisioningError(f"validate_project failed: {e}")

    def create_git_branch(self, project_id: str, branch_name: str) -> str:
        """Create git branch in LookML project.

        Args:
            project_id: Project ID
            branch_name: Branch name to create

        Returns:
            Branch name

        Raises:
            ProvisioningError: If branch creation fails
        """
        try:
            self.sdk.create_git_branch(project_id=project_id, body={"name": branch_name})
            logger.info(
                "Created git branch",
                extra={
                    "event": "project.branch.create",
                    "projectId": project_id,
                    "branch": branch_name,
                },
            )
            return branch_name
        except Exception as e:
            raise ProvisioningError(f"create_git_branch failed: {e}")

    # ============================================================================
    # SAML CONFIGURATION
    # ============================================================================

    def ensure_saml_group_mapping(self, group_id: int, group_email: str) -> None:
        """Add group to SAML configuration if not already mapped.

        Args:
            group_id: Looker group ID
            group_email: Group email/name

        Raises:
            ProvisioningError: If SAML config update fails
        """
        try:
            saml_cfg = self.sdk.saml_config()
        except Exception as e:
            raise ProvisioningError(f"saml_config failed: {e}")

        groups_field = getattr(saml_cfg, "groups", []) or []

        # Check if already mapped
        for g in groups_field:
            if getattr(g, "name", None) == group_email:
                logger.info(
                    "Reusing SAML mapping",
                    extra={"event": "saml.group.reuse", "groupEmail": group_email},
                )
                return

        # Add new group mapping
        new_group_entry = {"name": group_email, "id": group_id}
        update_body = {"groups": [*list(groups_field), new_group_entry]}

        try:
            self.sdk.update_saml_config(body=update_body)
        except Exception as e:
            raise ProvisioningError(f"update_saml_config failed: {e}")

        logger.info(
            "Added SAML group", extra={"event": "saml.group.add", "groupEmail": group_email}
        )

    # ============================================================================
    # DECOMMISSIONING & CLEANUP
    # ============================================================================

    def decommission_project(
        self,
        project_id: str,
        archive_folder: bool = True,
        delete_dashboards: bool = False,
        delete_schedules: bool = False,
    ) -> dict[str, Any]:
        """Decommission Looker project resources.

        Args:
            project_id: GCP project ID
            archive_folder: If True, rename folder to "Archived: {name}"
            delete_dashboards: If True, delete all dashboards in folder
            delete_schedules: If True, delete all scheduled plans

        Returns:
            Dict with decommissioning results

        Raises:
            ProvisioningError: If decommissioning fails
        """
        folder_name = f"Project: {project_id}"
        results: dict[str, Any] = {
            "projectId": project_id,
            "archived_folder": False,
            "deleted_dashboards": 0,
            "deleted_schedules": 0,
        }

        try:
            # Find project folder
            folders = self.sdk.search_folders(name=folder_name) or []
            if not folders:
                logger.warning(
                    "Folder not found for decommissioning",
                    extra={"event": "decommission.folder_not_found", "projectId": project_id},
                )
                return results

            folder_id = getattr(folders[0], "id", None)

            # Get all dashboards in folder
            dashboards = self.sdk.search_dashboards(folder_id=folder_id) or []

            # Delete or archive dashboards
            if delete_dashboards:
                for dash in dashboards:
                    dash_id = getattr(dash, "id", None)
                    if dash_id:
                        self.sdk.delete_dashboard(dash_id)
                        results["deleted_dashboards"] += 1

            # Delete scheduled plans if requested
            if delete_schedules:
                for dash in dashboards:
                    dash_id = getattr(dash, "id", None)
                    if dash_id:
                        schedules = self.sdk.scheduled_plans_for_dashboard(dash_id) or []
                        for schedule in schedules:
                            schedule_id = getattr(schedule, "id", None)
                            if schedule_id:
                                self.sdk.delete_scheduled_plan(schedule_id)
                                results["deleted_schedules"] += 1

            # Archive folder by renaming
            if archive_folder:
                archived_name = f"Archived: {folder_name}"
                self.sdk.update_folder(folder_id=folder_id, body={"name": archived_name})
                results["archived_folder"] = True

            logger.info(
                "Decommissioned project", extra={"event": "project.decommission", **results}
            )

            return results

        except Exception as e:
            raise ProvisioningError(f"decommission_project failed: {e}")

    def delete_group(self, group_id: int) -> bool:
        """Delete Looker group.

        Args:
            group_id: Group ID to delete

        Returns:
            True if deleted

        Raises:
            ProvisioningError: If deletion fails
        """
        try:
            self.sdk.delete_group(group_id=group_id)
            logger.info("Deleted group", extra={"event": "group.delete", "groupId": group_id})
            return True
        except Exception as e:
            raise ProvisioningError(f"delete_group failed: {e}")

    def disable_user(self, user_id: int) -> bool:
        """Disable user account (soft delete).

        Args:
            user_id: User ID to disable

        Returns:
            True if disabled

        Raises:
            ProvisioningError: If disable fails
        """
        try:
            self.sdk.update_user(user_id=user_id, body={"is_disabled": True})
            logger.info("Disabled user", extra={"event": "user.disable", "userId": user_id})
            return True
        except Exception as e:
            raise ProvisioningError(f"disable_user failed: {e}")

    def delete_user(self, user_id: int) -> bool:
        """Delete user account (hard delete).

        Args:
            user_id: User ID to delete

        Returns:
            True if deleted

        Raises:
            ProvisioningError: If deletion fails
        """
        try:
            self.sdk.delete_user(user_id=user_id)
            logger.info("Deleted user", extra={"event": "user.delete", "userId": user_id})
            return True
        except Exception as e:
            raise ProvisioningError(f"delete_user failed: {e}")

    # ============================================================================
    # ORCHESTRATION (MAIN PROVISION WORKFLOW)
    # ============================================================================

    def provision(
        self, project_id: str, group_email: str, template_dashboard_ids: list[int]
    ) -> dict:
        """Complete project provisioning workflow.

        Orchestrates:
        1. Group creation/lookup
        2. SAML group mapping
        3. Project folder creation
        4. Dashboard template cloning

        Args:
            project_id: GCP project ID
            group_email: Google Workspace group email
            template_dashboard_ids: List of template dashboard IDs to clone

        Returns:
            Provisioning result dict with IDs and correlation ID

        Raises:
            ValidationError: If required parameters missing
            ProvisioningError: If any provisioning step fails
        """
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

        # Step 1: Ensure group exists
        group_id = self.ensure_group(group_email)

        # Step 2: Add group to SAML config
        self.ensure_saml_group_mapping(group_id, group_email)

        # Step 3: Create project folder
        folder_id = self.ensure_project_folder(project_id)

        # Step 4: Clone dashboard templates
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
