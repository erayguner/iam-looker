import types

import pytest

from iam_looker.exceptions import ValidationError
from iam_looker.handler import handle_event
from iam_looker.models import ProvisionPayload

# NOTE: Legacy test coverage; see test_handler.py for new handler tests.
from iam_looker.provisioner import LookerProvisioner


class MockSDK:
    def __init__(self):
        self.groups = []
        self.folders = []
        self.dashboards = []
        self.saml_cfg = types.SimpleNamespace(groups=[])

    # GROUPS
    def search_groups(self, name):
        return [g for g in self.groups if g.name == name]

    def create_group(self, body):
        g = types.SimpleNamespace(id=len(self.groups) + 1, name=body["name"])
        self.groups.append(g)
        return g

    # FOLDERS
    def search_folders(self, name):
        return [f for f in self.folders if f.name == name]

    def create_folder(self, body):
        f = types.SimpleNamespace(id=len(self.folders) + 1, name=body["name"])
        self.folders.append(f)
        return f

    # DASHBOARDS
    def dashboard(self, dashboard_id):
        return types.SimpleNamespace(id=dashboard_id, title=f"Template {dashboard_id}")

    def search_dashboards(self, title):
        return [d for d in self.dashboards if d.title == title]

    def dashboard_copy(self, dashboard_id, body):
        d = types.SimpleNamespace(
            id=len(self.dashboards) + 100, title=body["name"], folder_id=body["folder_id"]
        )
        self.dashboards.append(d)
        return d

    # SAML
    def saml_config(self):
        return self.saml_cfg

    def update_saml_config(self, body):
        # just replace groups
        self.saml_cfg.groups = [types.SimpleNamespace(**g) for g in body.get("groups", [])]
        return self.saml_cfg


def test_provision_happy_path():
    sdk = MockSDK()
    p = LookerProvisioner(sdk)
    result = p.provision(
        project_id="demo-project",
        group_email="analysts@company.com",
        template_dashboard_ids=[1, 2],
    )
    assert result["projectId"] == "demo-project"
    assert len(result["dashboardIds"]) == 2
    # second run should not duplicate dashboards
    result2 = p.provision(
        project_id="demo-project",
        group_email="analysts@company.com",
        template_dashboard_ids=[1, 2],
    )
    assert len(result2["dashboardIds"]) == 2  # reused
    assert sdk.dashboard_copy  # ensure method exists


def test_validation_error():
    sdk = MockSDK()
    p = LookerProvisioner(sdk)
    with pytest.raises(ValidationError):
        p.provision(
            project_id="",
            group_email="no-at-sign",
            template_dashboard_ids=[],
        )


def test_provision_happy_path_old():
    sdk = MockSDK()
    p = LookerProvisioner(sdk)
    result = p.provision(
        project_id="demo-project",
        group_email="analysts@company.com",
        template_dashboard_ids=[1, 2],
    )
    assert result["projectId"] == "demo-project"
    assert len(result["dashboardIds"]) == 2
    result2 = p.provision(
        project_id="demo-project",
        group_email="analysts@company.com",
        template_dashboard_ids=[1, 2],
    )
    assert len(result2["dashboardIds"]) == 2


def test_pydantic_model_validation():
    payload = {"projectId": "demo-project", "groupEmail": "analysts@company.com"}
    model = ProvisionPayload(**payload)
    assert model.projectId == "demo-project"
    assert model.groupEmail == "analysts@company.com"


def test_handler_validation_error():
    # invalid project id (too short)
    event = {"projectId": "abc", "groupEmail": "bad-email"}
    result = handle_event(event)
    assert result["status"] == "validation_error"
