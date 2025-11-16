from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    LOOKERSDK_BASE_URL: str = ""
    LOOKERSDK_CLIENT_ID: str = ""
    LOOKERSDK_CLIENT_SECRET: str = ""
    LOOKERSDK_VERIFY_SSL: bool = True
    DEFAULT_TEMPLATE_FOLDER_ID: Optional[int] = None
    DEFAULT_TEMPLATE_DASHBOARD_IDS: List[int] = []

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def template_dashboard_ids(self) -> List[int]:
        return self.DEFAULT_TEMPLATE_DASHBOARD_IDS or []


settings = Settings()
