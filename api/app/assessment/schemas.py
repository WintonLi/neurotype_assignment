from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AssessmentStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    ISSUED = "issued"


class DomainName(StrEnum):
    SOCIAL_COMMUNICATION = "social_communication"
    SENSORY_PROCESSING = "sensory_processing"
    EXECUTIVE_FUNCTION = "executive_function"
    EMOTIONAL_REGULATION = "emotional_regulation"
    MOTOR_COORDINATION = "motor_coordination"


class SupportNeedBand(StrEnum):
    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    SUBSTANTIAL = "substantial"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class AssessmentSortField(StrEnum):
    ASSESSED_AT = "assessed_at"
    CLINICIAN_ID = "clinician_id"


class ClientResponse(BaseModel):
    date_of_birth: date
    nhs_number: str
    guardian_contact: str
    safeguarding_notes: str | None


class AgeResponse(BaseModel):
    years: int
    months: int


class AssessmentItemResponse(BaseModel):
    code: str
    raw: float | None
    max: float
    completed: bool


class DomainResultResponse(BaseModel):
    domain: DomainName
    percentage: float | None
    band: SupportNeedBand | None
    items: list[AssessmentItemResponse]


class AssessmentListItemResponse(BaseModel):
    assessment_id: str
    assessed_at: datetime
    clinician_id: str
    status: AssessmentStatus
    flagged: bool
    domains: list[DomainResultResponse]


class AssessmentListResponse(BaseModel):
    items: list[AssessmentListItemResponse]
    page: int
    page_size: int
    total: int


class AssessmentDetailResponse(BaseModel):
    assessment_id: str
    client: ClientResponse
    assessed_at: datetime
    clinician_id: str
    age: AgeResponse
    domains: list[DomainResultResponse]
    summary: str
    flagged: bool
    status: AssessmentStatus
    issued_at: datetime | None = None
    issued_by: str | None = None


class IssueAssessmentResponse(BaseModel):
    assessment_id: str
    status: AssessmentStatus
    issued_at: datetime
    issued_by: str


class SummaryUpdateRequest(BaseModel):
    summary: str = Field(max_length=8000)


class SummaryUpdateResponse(BaseModel):
    assessment_id: str
    summary: str
    flagged: bool
    