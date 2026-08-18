from __future__ import annotations

from typing import TYPE_CHECKING

from app.database import Base
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.assessment.models import Assessment


class UserRole:
    CLINICIAN = "clinician"
    REVIEWER = "reviewer"


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    roles: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment",
        foreign_keys="Assessment.clinician_username",
        back_populates="clinician",
    )