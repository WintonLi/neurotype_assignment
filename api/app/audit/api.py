from datetime import datetime

from fastapi import APIRouter, Query

from .schemas import (
    AuditAction,
    AuditEntityType,
    AuditEventListResponse,
)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=AuditEventListResponse)
async def list_audit_events(
    entity_type: AuditEntityType | None = None,
    entity_id: str | None = None,
    actor_id: str | None = None,
    action: AuditAction | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> AuditEventListResponse:
    raise NotImplementedError
