import os
from dataclasses import dataclass

# DEPRECATION: Replace with iam_looker.settings.Settings in new code paths.

@dataclass
class AppConfig:
    base_url: str
    client_id: str
    client_secret: str
    verify_ssl: bool = True
    default_template_folder_id: int | None = None
    default_template_dashboard_ids: list[int] = None

    @staticmethod
    def load() -> "AppConfig":
        folder_ids_raw = os.getenv("DEFAULT_TEMPLATE_DASHBOARD_IDS", "").strip()
        dashboard_ids = []
        if folder_ids_raw:
            for item in folder_ids_raw.split(","):
                item = item.strip()
                if item:
                    try:
                        dashboard_ids.append(int(item))
                    except ValueError:
                        pass  # ignore invalid
        return AppConfig(
            base_url=os.getenv("LOOKERSDK_BASE_URL", ""),
            client_id=os.getenv("LOOKERSDK_CLIENT_ID", ""),
            client_secret=os.getenv("LOOKERSDK_CLIENT_SECRET", ""),
            verify_ssl=os.getenv("LOOKERSDK_VERIFY_SSL", "true").lower() == "true",
            default_template_folder_id=int(os.getenv("DEFAULT_TEMPLATE_FOLDER_ID", "0")) or None,
            default_template_dashboard_ids=dashboard_ids or [],
        )
