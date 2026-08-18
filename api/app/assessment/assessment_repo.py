from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Assessment


class AssessmentRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, assessment_id: str) -> Assessment | None:
        return await self.session.get(Assessment, assessment_id)

    async def list(
        self,
        *,
        status: str | None = None,
        clinician_username: str | None = None,
        sort_by: str = "assessed_at",
        descending: bool = True,
    ) -> list[Assessment]:
        statement = select(Assessment)
        if status is not None:
            statement = statement.where(Assessment.status == status)
        if clinician_username is not None:
            statement = statement.where(Assessment.clinician_username == clinician_username)
        sort_column = {
            "assessed_at": Assessment.assessed_at,
            "clinician_id": Assessment.clinician_username,
        }.get(sort_by, Assessment.assessed_at)
        statement = statement.order_by(
            sort_column.desc() if descending else sort_column.asc()
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def issue(
        self,
        assessment: Assessment,
        *,
        issued_at: datetime,
        issued_by: str,
    ) -> Assessment:
        assessment.status = "issued"
        assessment.issued_at = issued_at
        assessment.issued_by = issued_by
        await self.session.flush()
        return assessment

    async def update_summary(self, assessment: Assessment, summary: str) -> Assessment:
        assessment.summary = summary
        await self.session.flush()
        return assessment
