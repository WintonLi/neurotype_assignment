from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditEvent
from .schemas import (
    AuditAction,
    AuditActorResponse,
    AuditChange,
    AuditEntityType,
    AuditEventListResponse,
    AuditEventResponse,
)


class AuditService:
    """Records and lists audit events. Deliberately dumb: no business rules,
    just persists what callers tell it happened."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def record(
        self,
        *,
        actor_username: str,
        action: AuditAction | str,
        entity_type: AuditEntityType | str,
        entity_id: str,
        changes: list[dict[str, Any]] | None = None,
        occurred_at: datetime | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=str(uuid4()),
            occurred_at=occurred_at or datetime.now(UTC),
            actor_username=actor_username,
            action=AuditAction(action).value,
            entity_type=AuditEntityType(entity_type).value,
            entity_id=entity_id,
            changes=changes,
        )
        self.session.add(event)
        return event

    async def list_events(
        self,
        *,
        entity_type: AuditEntityType | None = None,
        entity_id: str | None = None,
        actor_id: str | None = None,
        action: AuditAction | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditEventListResponse:
        statement = select(AuditEvent)
        if entity_type is not None:
            statement = statement.where(AuditEvent.entity_type == entity_type.value)
        if entity_id is not None:
            statement = statement.where(AuditEvent.entity_id == entity_id)
        if actor_id is not None:
            statement = statement.where(AuditEvent.actor_username == actor_id)
        if action is not None:
            statement = statement.where(AuditEvent.action == action.value)
        if from_time is not None:
            statement = statement.where(AuditEvent.occurred_at >= from_time)
        if to_time is not None:
            statement = statement.where(AuditEvent.occurred_at <= to_time)
        statement = statement.order_by(AuditEvent.occurred_at.desc())

        events = list((await self.session.scalars(statement)).all())
        start = (page - 1) * page_size
        page_events = events[start : start + page_size]

        return AuditEventListResponse(
            items=[self._to_response(event) for event in page_events],
            page=page,
            page_size=page_size,
            total=len(events),
        )

    @staticmethod
    def _to_response(event: AuditEvent) -> AuditEventResponse:
        return AuditEventResponse(
            id=event.id,
            occurred_at=event.occurred_at,
            actor=AuditActorResponse(
                id=event.actor_username, display_name=event.actor_username
            ),
            action=AuditAction(event.action),
            entity_type=AuditEntityType(event.entity_type),
            entity_id=event.entity_id,
            changes=[AuditChange(**change) for change in (event.changes or [])],
        )
