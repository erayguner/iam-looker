"""Comprehensive tests for advanced Looker provisioner functions.

Tests cover:
- User and group management
- Connection management
- LookML project operations
- Content management (dashboards, schedules)
- Decommissioning operations
"""

import types

import pytest

from iam_looker.exceptions import ProvisioningError
from iam_looker.provisioner import LookerProvisioner


class TestSDKError(Exception):
    """Custom exception for simulating SDK errors in tests."""


class MockSDK:
    """Mock Looker SDK for testing all provisioner operations."""

    def __init__(self):
        self.groups = []
        self.users = []
        self.folders = []
        self.dashboards = []
        self.connections = []
        self.projects = []
        self.scheduled_plans = []
        self.branches = []
        self.saml_cfg = types.SimpleNamespace(groups=[])
        # Track group memberships
        self.group_users = {}  # group_id -> [user_ids]

    # ========================================================================
    # GROUP OPERATIONS
    # ========================================================================

    def search_groups(self, name):
        return [g for g in self.groups if g.name == name]

    def create_group(self, body):
        g = types.SimpleNamespace(id=len(self.groups) + 1, name=body["name"])
        self.groups.append(g)
        self.group_users[g.id] = []
        return g

    def delete_group(self, group_id):
        self.groups = [g for g in self.groups if g.id != group_id]
        if group_id in self.group_users:
            del self.group_users[group_id]

    def all_group_users(self, group_id):
        user_ids = self.group_users.get(group_id, [])
        return [types.SimpleNamespace(id=uid) for uid in user_ids]

    def add_group_user(self, group_id, body):
        if group_id not in self.group_users:
            self.group_users[group_id] = []
        self.group_users[group_id].append(body["user_id"])
        return types.SimpleNamespace(success=True)

    def delete_group_user(self, group_id, user_id):
        if group_id in self.group_users:
            self.group_users[group_id] = [
                uid for uid in self.group_users[group_id] if uid != user_id
            ]

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def create_user(self, body):
        u = types.SimpleNamespace(
            id=len(self.users) + 1,
            email=body["email"],
            first_name=body.get("first_name", ""),
            last_name=body.get("last_name", ""),
            is_disabled=False,
        )
        self.users.append(u)
        return u

    def set_user_roles(self, user_id, body):
        # body is list of role IDs
        for u in self.users:
            if u.id == user_id:
                u.role_ids = body
                break

    def update_user(self, user_id, body):
        for u in self.users:
            if u.id == user_id:
                for key, value in body.items():
                    setattr(u, key, value)
                return u
        return None

    def delete_user(self, user_id):
        self.users = [u for u in self.users if u.id != user_id]

    # ========================================================================
    # FOLDER OPERATIONS
    # ========================================================================

    def search_folders(self, name):
        return [f for f in self.folders if f.name == name]

    def create_folder(self, body):
        f = types.SimpleNamespace(
            id=len(self.folders) + 1, name=body["name"], parent_id=body.get("parent_id")
        )
        self.folders.append(f)
        return f

    def update_folder(self, folder_id, body):
        for f in self.folders:
            if f.id == folder_id:
                for key, value in body.items():
                    setattr(f, key, value)
                return f
        return None

    # ========================================================================
    # DASHBOARD OPERATIONS
    # ========================================================================

    def dashboard(self, dashboard_id):
        for d in self.dashboards:
            if d.id == dashboard_id:
                return d
        return types.SimpleNamespace(id=dashboard_id, title=f"Template {dashboard_id}")

    def search_dashboards(self, title=None, folder_id=None):
        results = self.dashboards
        if title:
            results = [d for d in results if d.title == title]
        if folder_id:
            results = [d for d in results if d.folder_id == folder_id]
        return results

    def dashboard_copy(self, dashboard_id, body):
        d = types.SimpleNamespace(
            id=len(self.dashboards) + 100, title=body["name"], folder_id=body["folder_id"]
        )
        self.dashboards.append(d)
        return d

    def update_dashboard(self, dashboard_id, body):
        for d in self.dashboards:
            if d.id == dashboard_id:
                for key, value in body.items():
                    setattr(d, key, value)
                return d
        return None

    def delete_dashboard(self, dashboard_id):
        self.dashboards = [d for d in self.dashboards if d.id != dashboard_id]

    # ========================================================================
    # SCHEDULED PLANS
    # ========================================================================

    def create_scheduled_plan(self, body):
        plan = types.SimpleNamespace(
            id=len(self.scheduled_plans) + 1,
            name=body["name"],
            dashboard_id=body["dashboard_id"],
            cron_tab=body.get("cron tab", ""),
            enabled=body.get("enabled", True),
        )
        self.scheduled_plans.append(plan)
        return plan

    def scheduled_plans_for_dashboard(self, dashboard_id):
        return [p for p in self.scheduled_plans if p.dashboard_id == dashboard_id]

    def delete_scheduled_plan(self, schedule_id):
        self.scheduled_plans = [p for p in self.scheduled_plans if p.id != schedule_id]

    # ========================================================================
    # CONNECTION OPERATIONS
    # ========================================================================

    def create_connection(self, body):
        conn = types.SimpleNamespace(
            name=body["name"],
            host=body["host"],
            database=body["database"],
            dialect_name=body.get("dialect_name", ""),
            username=body.get("username"),
            password=body.get("password"),
        )
        self.connections.append(conn)
        return conn

    def test_connection(self, connection_name):
        for conn in self.connections:
            if conn.name == connection_name:
                return types.SimpleNamespace(status="success", message="Connection successful")
        return types.SimpleNamespace(status="error", message="Connection not found")

    def update_connection(self, connection_name, body):
        for conn in self.connections:
            if conn.name == connection_name:
                for key, value in body.items():
                    setattr(conn, key, value)
                return conn
        return None

    def delete_connection(self, connection_name):
        self.connections = [c for c in self.connections if c.name != connection_name]

    def all_connections(self):
        return self.connections

    # ========================================================================
    # LOOKML PROJECT OPERATIONS
    # ========================================================================

    def create_project(self, body):
        proj = types.SimpleNamespace(
            id=body["name"],
            name=body["name"],
            git_remote_url=body["git_remote_url"],
            git_service_name=body.get("git_service_name", "github"),
        )
        self.projects.append(proj)
        return proj

    def deploy_to_production(self, project_id):
        return types.SimpleNamespace(status="success")

    def validate_project(self, project_id):
        # Return success with no errors
        return types.SimpleNamespace(errors=[], warnings=[])

    def create_git_branch(self, project_id, body):
        branch = types.SimpleNamespace(name=body["name"], project_id=project_id)
        self.branches.append(branch)
        return branch

    # ========================================================================
    # SAML OPERATIONS
    # ========================================================================

    def saml_config(self):
        return self.saml_cfg

    def update_saml_config(self, body):
        self.saml_cfg.groups = [types.SimpleNamespace(**g) for g in body.get("groups", [])]
        return self.saml_cfg


# ============================================================================
# GROUP & USER MANAGEMENT TESTS
# ============================================================================


def test_add_user_to_group():
    """Test adding user to group."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    # Create group and user
    group_id = p.ensure_group("analysts@company.com")
    user_id = p.create_user("user@company.com", "John", "Doe")

    # Add user to group
    result = p.add_user_to_group(group_id, user_id)
    assert result is True

    # Adding again should return False (already in group)
    result = p.add_user_to_group(group_id, user_id)
    assert result is False


def test_remove_user_from_group():
    """Test removing user from group."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    group_id = p.ensure_group("analysts@company.com")
    user_id = p.create_user("user@company.com", "John", "Doe")
    p.add_user_to_group(group_id, user_id)

    # Remove user
    result = p.remove_user_from_group(group_id, user_id)
    assert result is True


def test_create_user_with_roles():
    """Test creating user with role assignment."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    user_id = p.create_user("user@company.com", "John", "Doe", role_ids=[1, 2, 3])

    assert user_id > 0
    # Check roles were assigned
    user = sdk.users[0]
    assert hasattr(user, "role_ids")
    assert user.role_ids == [1, 2, 3]


def test_bulk_provision_users():
    """Test bulk user provisioning."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    group_id = p.ensure_group("analysts@company.com")

    users = [
        {"email": "user1@company.com", "first_name": "User", "last_name": "One"},
        {"email": "user2@company.com", "first_name": "User", "last_name": "Two"},
        {"email": "user3@company.com", "first_name": "User", "last_name": "Three"},
    ]

    user_ids = p.bulk_provision_users(users, group_id=group_id)

    assert len(user_ids) == 3
    assert all(isinstance(uid, int) for uid in user_ids)

    # Verify all users added to group
    group_users = sdk.group_users[group_id]
    assert len(group_users) == 3


# ============================================================================
# CONNECTION MANAGEMENT TESTS
# ============================================================================


def test_create_connection():
    """Test creating database connection."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    conn_name = p.create_connection(
        name="bigquery_prod",
        host="bigquery.googleapis.com",
        database="my-project",
        dialect_name="bigquery_standard_sql",
        service_account_json='{"type": "service_account"}',
    )

    assert conn_name == "bigquery_prod"
    assert len(sdk.connections) == 1


def test_test_connection():
    """Test connection testing."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    p.create_connection("test_conn", "localhost", "testdb")

    result = p.test_connection("test_conn")

    assert result["status"] == "success"
    assert result["success"] is True


def test_update_connection():
    """Test updating connection configuration."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    p.create_connection("test_conn", "localhost", "testdb")
    p.update_connection("test_conn", host="newhost", port=5432)

    conn = sdk.connections[0]
    assert conn.host == "newhost"
    assert conn.port == 5432


def test_delete_connection():
    """Test deleting connection."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    p.create_connection("test_conn", "localhost", "testdb")
    assert len(sdk.connections) == 1

    result = p.delete_connection("test_conn")
    assert result is True
    assert len(sdk.connections) == 0


def test_list_connections():
    """Test listing all connections."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    p.create_connection("conn1", "host1", "db1", dialect_name="postgres")
    p.create_connection("conn2", "host2", "db2", dialect_name="mysql")

    connections = p.list_connections()

    assert len(connections) == 2
    assert connections[0]["name"] == "conn1"
    assert connections[0]["dialect"] == "postgres"
    assert connections[1]["name"] == "conn2"


# ============================================================================
# LOOKML PROJECT TESTS
# ============================================================================


def test_create_project():
    """Test creating LookML project."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    project_id = p.create_project(
        name="my_project", git_remote_url="https://github.com/company/repo.git"
    )

    assert project_id == "my_project"
    assert len(sdk.projects) == 1


def test_deploy_project_to_production():
    """Test deploying project to production."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    p.create_project("my_project", "https://github.com/company/repo.git")
    result = p.deploy_project_to_production("my_project")

    assert result is True


def test_validate_project():
    """Test project validation."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    p.create_project("my_project", "https://github.com/company/repo.git")
    result = p.validate_project("my_project")

    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_create_git_branch():
    """Test creating git branch."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    p.create_project("my_project", "https://github.com/company/repo.git")
    branch_name = p.create_git_branch("my_project", "feature/new-feature")

    assert branch_name == "feature/new-feature"
    assert len(sdk.branches) == 1


# ============================================================================
# CONTENT MANAGEMENT TESTS
# ============================================================================


def test_move_content_to_folder():
    """Test moving dashboard to different folder."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    folder_id = p.ensure_project_folder("project-1")
    new_folder_id = p.ensure_project_folder("project-2")

    # Create dashboard in first folder
    dash = types.SimpleNamespace(id=1, title="Test Dashboard", folder_id=folder_id)
    sdk.dashboards.append(dash)

    # Move to new folder
    result = p.move_content_to_folder(1, new_folder_id)

    assert result is True
    assert sdk.dashboards[0].folder_id == new_folder_id


def test_create_scheduled_plan():
    """Test creating scheduled dashboard delivery."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    folder_id = p.ensure_project_folder("project-1")
    dash_id = p.clone_dashboard_if_missing(101, folder_id, "project-1")

    plan_id = p.create_scheduled_plan(
        dashboard_id=dash_id,
        name="Daily Report",
        cron_schedule="0 9 * * *",
        destination_emails=["team@company.com"],
    )

    assert plan_id > 0
    assert len(sdk.scheduled_plans) == 1
    assert sdk.scheduled_plans[0].name == "Daily Report"


# ============================================================================
# DECOMMISSIONING TESTS
# ============================================================================


def test_decommission_project_archive_only():
    """Test decommissioning with folder archive."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    # Setup project
    folder_id = p.ensure_project_folder("test-project")
    p.clone_dashboard_if_missing(101, folder_id, "test-project")

    # Decommission (archive only)
    result = p.decommission_project("test-project", archive_folder=True, delete_dashboards=False)

    assert result["archived_folder"] is True
    assert result["deleted_dashboards"] == 0

    # Check folder was renamed
    folder = sdk.folders[0]
    assert folder.name == "Archived: Project: test-project"


def test_decommission_project_delete_all():
    """Test decommissioning with deletion."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    # Setup project with dashboards and schedules
    folder_id = p.ensure_project_folder("test-project")
    dash_id = p.clone_dashboard_if_missing(101, folder_id, "test-project")
    p.create_scheduled_plan(dash_id, "Daily Report", "0 9 * * *", ["team@company.com"])

    assert len(sdk.dashboards) == 1
    assert len(sdk.scheduled_plans) == 1

    # Decommission with full deletion
    result = p.decommission_project(
        "test-project", archive_folder=True, delete_dashboards=True, delete_schedules=True
    )

    assert result["archived_folder"] is True
    assert result["deleted_dashboards"] == 1
    assert result["deleted_schedules"] == 1
    assert len(sdk.dashboards) == 0
    assert len(sdk.scheduled_plans) == 0


def test_delete_group():
    """Test deleting group."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    group_id = p.ensure_group("test@company.com")
    assert len(sdk.groups) == 1

    result = p.delete_group(group_id)

    assert result is True
    assert len(sdk.groups) == 0


def test_disable_user():
    """Test disabling user (soft delete)."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    user_id = p.create_user("user@company.com", "John", "Doe")
    assert sdk.users[0].is_disabled is False

    result = p.disable_user(user_id)

    assert result is True
    assert sdk.users[0].is_disabled is True


def test_delete_user():
    """Test deleting user (hard delete)."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    user_id = p.create_user("user@company.com", "John", "Doe")
    assert len(sdk.users) == 1

    result = p.delete_user(user_id)

    assert result is True
    assert len(sdk.users) == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_complete_provisioning_workflow():
    """Test full provisioning workflow with all features."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    # 1. Provision project
    result = p.provision(
        project_id="analytics-project",
        group_email="analysts@company.com",
        template_dashboard_ids=[101, 102],
    )

    assert result["projectId"] == "analytics-project"
    assert result["groupEmail"] == "analysts@company.com"
    assert len(result["dashboardIds"]) == 2

    # 2. Add users to group
    user_ids = p.bulk_provision_users(
        [
            {"email": "user1@company.com", "first_name": "User", "last_name": "One"},
            {"email": "user2@company.com", "first_name": "User", "last_name": "Two"},
        ],
        group_id=result["groupId"],
    )

    assert len(user_ids) == 2

    # 3. Create database connection
    conn_name = p.create_connection("prod_bigquery", "bigquery.googleapis.com", "analytics-project")

    assert conn_name == "prod_bigquery"

    # 4. Create scheduled delivery
    plan_id = p.create_scheduled_plan(
        dashboard_id=result["dashboardIds"][0],
        name="Weekly Dashboard",
        cron_schedule="0 9 * * 1",
        destination_emails=["team@company.com"],
    )

    assert plan_id > 0

    # 5. Validate everything is created
    assert len(sdk.groups) == 1
    assert len(sdk.users) == 2
    assert len(sdk.folders) == 1
    assert len(sdk.dashboards) == 2
    assert len(sdk.connections) == 1
    assert len(sdk.scheduled_plans) == 1


def test_decommissioning_workflow():
    """Test complete decommissioning workflow."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    # Setup complete project
    result = p.provision("test-project", "team@company.com", [101, 102])

    group_id = result["groupId"]
    user_ids = p.bulk_provision_users(
        [{"email": "user@company.com", "first_name": "User", "last_name": "One"}], group_id=group_id
    )

    # Decommission everything
    decommission_result = p.decommission_project(
        "test-project", archive_folder=True, delete_dashboards=True, delete_schedules=False
    )

    assert decommission_result["archived_folder"] is True
    assert decommission_result["deleted_dashboards"] == 2

    # Remove users
    for user_id in user_ids:
        p.disable_user(user_id)

    # Delete group
    p.delete_group(group_id)

    # Verify cleanup
    assert all(u.is_disabled for u in sdk.users)
    assert len(sdk.groups) == 0
    assert len(sdk.dashboards) == 0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


def test_connection_error_handling():
    """Test error handling for connection operations."""
    sdk = MockSDK()

    # Simulate SDK error
    def failing_create(*args, **kwargs):
        raise TestSDKError("Connection creation failed")

    sdk.create_connection = failing_create  # type: ignore[method-assign]

    p = LookerProvisioner(sdk)

    with pytest.raises(ProvisioningError, match="create_connection failed"):
        p.create_connection("test", "host", "db")


def test_project_creation_error_handling():
    """Test error handling for project creation."""
    sdk = MockSDK()

    def failing_create_project(*args, **kwargs):
        raise TestSDKError("Project creation failed")

    sdk.create_project = failing_create_project  # type: ignore[method-assign]

    p = LookerProvisioner(sdk)

    with pytest.raises(ProvisioningError, match="create_project failed"):
        p.create_project("test", "https://github.com/test/repo.git")


def test_decommission_missing_folder():
    """Test decommissioning when folder doesn't exist."""
    sdk = MockSDK()
    p = LookerProvisioner(sdk)

    # Decommission non-existent project
    result = p.decommission_project("nonexistent-project")

    assert result["archived_folder"] is False
    assert result["deleted_dashboards"] == 0
