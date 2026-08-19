from __future__ import annotations

from calendar import monthrange
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.audit_service import AuditService
from app.audit.schemas import AuditAction, AuditEntityType

from .assessment_repo import AssessmentRepo
from .models import Assessment
from .schemas import (
    AgeResponse,
    AssessmentDetailResponse,
    AssessmentItemResponse,
    AssessmentListItemResponse,
    AssessmentListResponse,
    AssessmentSortField,
    AssessmentStatus,
    ClientResponse,
    DomainName,
    DomainResultResponse,
    IssueAssessmentResponse,
    SortOrder,
    SummaryUpdateResponse,
    SupportNeedBand,
)


class AssessmentNotFoundError(Exception):
    pass


class AssessmentAlreadyIssuedError(Exception):
    pass


class AssessmentPermissionError(Exception):
    pass


class AssessmentService:
    def __init__(self, session: AsyncSession, audit_service: AuditService | None = None) -> None:
        self.session = session
        self.repo = AssessmentRepo(session)
        self.audit_service = audit_service or AuditService(session)

    async def list_assessments(
        self,
        *,
        status: AssessmentStatus | None = None,
        clinician_id: str | None = None,
        flagged: bool | None = None,
        domain: DomainName | None = None,
        band: SupportNeedBand | None = None,
        page: int = 1,
        page_size: int = 25,
        sort_by: AssessmentSortField = AssessmentSortField.ASSESSED_AT,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> AssessmentListResponse:
        assessments = await self.repo.list(
            status=status.value if status else None,
            clinician_username=clinician_id,
            sort_by=sort_by.value,
            descending=sort_order == SortOrder.DESC,
        )
        matching = [
            assessment
            for assessment in assessments
            if self._matches(assessment, flagged=flagged, domain=domain, band=band)
        ]
        start = (page - 1) * page_size
        return AssessmentListResponse(
            items=[
                self._to_list_item(item) for item in matching[start : start + page_size]
            ],
            page=page,
            page_size=page_size,
            total=len(matching),
        )

    async def get_assessment(
        self, assessment_id: str, *, actor_username: str
    ) -> AssessmentDetailResponse:
        assessment = await self._get(assessment_id)
        response = self._to_detail(assessment)
        self.audit_service.record(
            actor_username=actor_username,
            action=AuditAction.VIEW,
            entity_type=AuditEntityType.ASSESSMENT,
            entity_id=assessment_id,
        )
        await self.session.commit()
        return response

    async def issue_assessment(
        self,
        assessment_id: str,
        *,
        actor_username: str,
        actor_roles: set[str] | list[str],
    ) -> IssueAssessmentResponse:
        if "reviewer" not in actor_roles:
            raise AssessmentPermissionError
        assessment = await self._get(assessment_id)
        if assessment.status == AssessmentStatus.ISSUED.value:
            raise AssessmentAlreadyIssuedError
        issued_at = self._now()
        await self.repo.issue(assessment, issued_at=issued_at, issued_by=actor_username)
        self.audit_service.record(
            actor_username=actor_username,
            action=AuditAction.ISSUE,
            entity_type=AuditEntityType.ASSESSMENT,
            entity_id=assessment_id,
            occurred_at=issued_at,
        )
        await self.session.commit()
        return IssueAssessmentResponse(
            assessment_id=assessment.id,
            status=AssessmentStatus(assessment.status),
            issued_at=issued_at,
            issued_by=actor_username,
        )

    async def update_summary(
        self, assessment_id: str, summary: str, *, actor_username: str
    ) -> SummaryUpdateResponse:
        assessment = await self._get(assessment_id)
        before = assessment.summary
        await self.repo.update_summary(assessment, summary)
        self.audit_service.record(
            actor_username=actor_username,
            action=AuditAction.UPDATE,
            entity_type=AuditEntityType.ASSESSMENT,
            entity_id=assessment_id,
            changes=[{"field": "summary", "before": before, "after": summary}],
        )
        await self.session.commit()
        return SummaryUpdateResponse(
            assessment_id=assessment.id,
            summary=assessment.summary,
            flagged=self._flagged(assessment),
        )

    async def _get(self, assessment_id: str) -> Assessment:
        assessment = await self.repo.get(assessment_id)
        if assessment is None:
            raise AssessmentNotFoundError
        return assessment

    def _matches(
        self,
        assessment: Assessment,
        *,
        flagged: bool | None,
        domain: DomainName | None,
        band: SupportNeedBand | None,
    ) -> bool:
        if flagged is not None and self._flagged(assessment) != flagged:
            return False
        if domain is None and band is None:
            return True
        return any(
            (domain is None or result.domain == domain)
            and (band is None or result.band == band)
            for result in self._domain_results(assessment)
        )

    def _domain_results(self, assessment: Assessment) -> list[DomainResultResponse]:
        results = []
        for raw_domain in assessment.domains:
            items = [
                AssessmentItemResponse.model_validate(item)
                for item in raw_domain["items"]
            ]
            completed_items = [
                item for item in items if item.completed and item.raw is not None
            ]
            scores = [
                item.raw / item.max * 100
                for item in completed_items
                if item.raw is not None
            ]
            percentage = sum(scores) / len(scores) if scores else None
            results.append(
                DomainResultResponse(
                    domain=raw_domain["domain"],
                    percentage=round(percentage, 2) if percentage is not None else None,
                    band=self._band(percentage),
                    items=items,
                )
            )
        return results

    @staticmethod
    def _band(percentage: float | None) -> SupportNeedBand | None:
        if percentage is None:
            return None
        if percentage < 40:
            return SupportNeedBand.MINIMAL
        if percentage < 55:
            return SupportNeedBand.MILD
        if percentage < 85:
            return SupportNeedBand.MODERATE
        return SupportNeedBand.SUBSTANTIAL

    def _flagged(self, assessment: Assessment) -> bool:
        return (
            any(
                result.band == SupportNeedBand.SUBSTANTIAL
                for result in self._domain_results(assessment)
            )
            or any(
                not item.get("completed", False)
                for domain in assessment.domains
                for item in domain.get("items", [])
            )
            or len(assessment.summary) < 200
        )

    def _to_list_item(self, assessment: Assessment) -> AssessmentListItemResponse:
        return AssessmentListItemResponse(
            assessment_id=assessment.id,
            assessed_at=assessment.assessed_at,
            clinician_id=assessment.clinician_username,
            status=AssessmentStatus(assessment.status),
            flagged=self._flagged(assessment),
            domains=self._domain_results(assessment),
        )

    def _to_detail(self, assessment: Assessment) -> AssessmentDetailResponse:
        assessed_date = assessment.assessed_at.date()
        birth_date = date.fromisoformat(assessment.date_of_birth)
        years = assessed_date.year - birth_date.year
        if (assessed_date.month, assessed_date.day) < (
            birth_date.month,
            birth_date.day,
        ):
            years -= 1
        anniversary_year = birth_date.year + years
        anniversary_day = min(
            birth_date.day, monthrange(anniversary_year, birth_date.month)[1]
        )
        months = (
            (assessed_date.year - anniversary_year) * 12
            + assessed_date.month
            - birth_date.month
        )
        if assessed_date.day < anniversary_day:
            months -= 1
        return AssessmentDetailResponse(
            assessment_id=assessment.id,
            client=ClientResponse(
                date_of_birth=birth_date,
                nhs_number=assessment.nhs_number,
                guardian_contact=assessment.guardian_contact,
                safeguarding_notes=assessment.safeguarding_notes,
            ),
            assessed_at=assessment.assessed_at,
            clinician_id=assessment.clinician_username,
            age=AgeResponse(years=years, months=months),
            domains=self._domain_results(assessment),
            summary=assessment.summary,
            flagged=self._flagged(assessment),
            status=AssessmentStatus(assessment.status),
            issued_at=assessment.issued_at,
            issued_by=assessment.issued_by,
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
