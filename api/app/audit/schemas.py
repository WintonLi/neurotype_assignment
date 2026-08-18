from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class AuditAction(StrEnum):
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    ISSUE = "issue"
    DEACTIVATE = "deactivate"


class AuditEntityType(StrEnum):
    ASSESSMENT = "assessment"
    USER = "user"


class AuditChange(BaseModel):
    field: str
    before: Any | None = None
    after: Any | None = None


class AuditActorResponse(BaseModel):
    id: str
    display_name: str


class AuditEventResponse(BaseModel):
    id: str
    occurred_at: datetime
    actor: AuditActorResponse
    action: AuditAction
    entity_type: AuditEntityType
    entity_id: str
    changes: list[AuditChange] = []


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    page: int
    page_size: int
    total: int
    