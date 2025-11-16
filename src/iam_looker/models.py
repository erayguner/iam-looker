from typing import List, Optional, Dict
from pydantic import BaseModel, Field, EmailStr, PositiveInt, field_validator
import re

PROJECT_ID_REGEX = re.compile(r"^[a-z][a-z0-9-]{4,61}[a-z0-9]$")

class ProvisionPayload(BaseModel):
    projectId: str = Field(...)
    groupEmail: EmailStr
    ancestryPath: Optional[str] = None
    templateDashboardIds: Optional[List[PositiveInt]] = None
    templateFolderId: Optional[PositiveInt] = None
    tokens: Dict[str, str] = Field(default_factory=dict)

    @field_validator("projectId")
    def validate_project_id(cls, v):
        if not PROJECT_ID_REGEX.match(v):
            raise ValueError("Invalid projectId format")
        return v

class ProvisionResult(BaseModel):
    status: str
    projectId: str
    groupEmail: str
    groupId: Optional[int] = None
    folderId: Optional[int] = None
    dashboardIds: List[int] = []
    correlationId: Optional[str] = None
    error: Optional[str] = None
