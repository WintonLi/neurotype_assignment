from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    date_of_birth: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    nhs_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    guardian_contact: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    safeguarding_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    clinician_username: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.username"),
        nullable=False,
        index=True,
    )

    domains: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending_review",
        index=True,
    )

    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    issued_by: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("users.username"),
        nullable=True,
    )

    clinician: Mapped["User"] = relationship(
        "User",
        foreign_keys=[clinician_username],
        back_populates="assessments",
    )

    issuer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[issued_by],
    )
