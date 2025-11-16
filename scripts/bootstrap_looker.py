"""Optional helper script for manual provisioning dry-runs using new 2025 structure."""

import json
import os

from iam_looker.handler import handle_event


def main() -> None:
    event = {
        "projectId": os.getenv("BOOTSTRAP_PROJECT_ID", "demo-project"),
        "groupEmail": os.getenv("BOOTSTRAP_GROUP_EMAIL", "analysts@company.com"),
        "templateDashboardIds": [101, 202],
    }
    print(json.dumps(handle_event(event), indent=2))


if __name__ == "__main__":
    main()
