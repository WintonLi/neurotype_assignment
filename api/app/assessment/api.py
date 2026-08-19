from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.audit_service import AuditService
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db_session

from .assessment_service import (
    AssessmentAlreadyIssuedError,
    AssessmentNotFoundError,
    AssessmentPermissionError,
    AssessmentService,
)
from .schemas import (
    AssessmentDetailResponse,
    AssessmentListResponse,
    AssessmentSortField,
    AssessmentStatus,
    DomainName,
    IssueAssessmentResponse,
    SortOrder,
    SummaryUpdateRequest,
    SummaryUpdateResponse,
    SupportNeedBand,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=AssessmentListResponse)
async def list_assessments(
    status: AssessmentStatus | None = None,
    clinician_id: str | None = None,
    flagged: bool | None = None,
    domain: DomainName | None = None,
    band: SupportNeedBand | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    sort_by: AssessmentSortField = AssessmentSortField.ASSESSED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AssessmentListResponse:
    return await AssessmentService(session).list_assessments(
        status=status,
        clinician_id=clinician_id,
        flagged=flagged,
        domain=domain,
        band=band,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment(
    assessment_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AssessmentDetailResponse:
    try:
        return await AssessmentService(session, AuditService(session)).get_assessment(
            assessment_id,
            actor_username=current_user.username,
        )
    except AssessmentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        ) from error


@router.post(
    "/{assessment_id}/issue",
    response_model=IssueAssessmentResponse,
)
async def issue_assessment(
    assessment_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> IssueAssessmentResponse:
    try:
        return await AssessmentService(session, AuditService(session)).issue_assessment(
            assessment_id,
            actor_username=current_user.username,
            actor_roles=current_user.roles,
        )
    except AssessmentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        ) from error
    except AssessmentAlreadyIssuedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Assessment already issued"
        ) from error
    except AssessmentPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Reviewer role required"
        ) from error


@router.patch(
    "/{assessment_id}/summary",
    response_model=SummaryUpdateResponse,
)
async def update_assessment_summary(
    assessment_id: str,
    request: SummaryUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> SummaryUpdateResponse:
    try:
        return await AssessmentService(session, AuditService(session)).update_summary(
            assessment_id,
            request.summary,
            actor_username=current_user.username,
        )
    except AssessmentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        ) from error
