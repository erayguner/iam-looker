import re

from pydantic import BaseModel, EmailStr, Field, PositiveInt, field_validator

PROJECT_ID_REGEX = re.compile(r"^[a-z][a-z0-9-]{4,61}[a-z0-9]$")


class ProvisionPayload(BaseModel):
    projectId: str = Field(...)
    groupEmail: EmailStr
    ancestryPath: str | None = None
    templateDashboardIds: list[PositiveInt] | None = None
    templateFolderId: PositiveInt | None = None
    tokens: dict[str, str] = Field(default_factory=dict)

    @field_validator("projectId")
    def validate_project_id(cls, v):
        if not PROJECT_ID_REGEX.match(v):
            raise ValueError("Invalid projectId format")
        return v


class ProvisionResult(BaseModel):
    status: str
    projectId: str
    groupEmail: str
    groupId: int | None = None
    folderId: int | None = None
    dashboardIds: list[int] = []
    correlationId: str | None = None
    error: str | None = None
