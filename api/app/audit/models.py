from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.database import Base
from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.auth.models import User


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    actor_username: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.username"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    changes: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    actor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[actor_username],
    )
    