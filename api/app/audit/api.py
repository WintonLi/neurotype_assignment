from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db_session

from .audit_service import AuditService
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
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AuditEventListResponse:
    _ = current_user
    return await AuditService(session).list_events(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        action=action,
        from_time=from_time,
        to_time=to_time,
        page=page,
        page_size=page_size,
    )

