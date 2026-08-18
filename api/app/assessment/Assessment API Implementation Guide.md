# Assessment API — Implementation Guide

## 1. Purpose

This document describes the REST API for the assessment module and defines how each endpoint should interact with the SQLAlchemy database models and the assessment business logic.

The purpose of this document is to provide enough context for an implementation agent to implement the assessment service layer without having to infer the intended behaviour from the FastAPI route definitions alone.

The assessment API is the core business API of the application. It supports the reviewer's workflow:

1. Retrieve the assessment review queue.
2. Filter and sort the queue.
3. Open an individual assessment.
4. Review the calculated results.
5. Issue the report.
6. Correct the summary when necessary, including after the report has been issued.

The API itself should remain thin. Business rules and database operations belong in the assessment service/repository layers rather than inside the FastAPI route functions.

---

# 2. Current API

The router is defined as:

```python
router = APIRouter(
    prefix="/assessments",
    tags=["assessments"],
)
```

Therefore the endpoints are:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/assessments` | Retrieve and filter the assessment review queue |
| `GET` | `/assessments/{assessment_id}` | Retrieve one complete assessment |
| `POST` | `/assessments/{assessment_id}/issue` | Issue an assessment/report |
| `PATCH` | `/assessments/{assessment_id}/summary` | Correct the assessment summary |

All endpoint functions are asynchronous and should remain `async`.

---

# 3. Database model

The current design intentionally keeps the database simple.

There is one primary assessment table:

```text
assessments
```

The assessment contains both ordinary scalar columns and a JSON column containing the original domain/item structure.

Conceptually:

```text
Assessment
├── id
├── date_of_birth
├── nhs_number
├── guardian_contact
├── safeguarding_notes
├── assessed_at
├── clinician_username
├── domains              <-- JSON
├── summary
├── status
├── issued_at
└── issued_by
```

The assessment does **not** have separate database tables for:

- clients
- domains
- assessment items

The reason is that domains and items are structural parts of an assessment rather than independent business entities for this application.

The `domains` JSON field preserves the structure received from the clinician application.

Example:

```json
[
  {
    "domain": "social_communication",
    "items": [
      {
        "code": "SC1",
        "raw": 12,
        "max": 20,
        "completed": true
      },
      {
        "code": "SC2",
        "raw": null,
        "max": 20,
        "completed": false
      }
    ]
  }
]
```

The database should therefore be treated as the source of the assessment's raw/source data.

---

# 4. Derived assessment values

The following values are **calculated by the business logic** and should not be treated as authoritative database fields:

- Young person's age
- Domain percentage
- Domain support-need band
- Review flag

The scoring rules are defined by the original take-home brief.

For each domain:

```text
domain percentage =
    mean(raw / max * 100)
```

The percentage is converted into a support-need band:

| Percentage | Band |
|---:|---|
| 0–39 | Minimal |
| 40–54 | Mild |
| 55–84 | Moderate |
| 85–100 | Substantial |

The review flag is ON when:

- any domain has the `Substantial` band;
- any item is incomplete; or
- the summary contains fewer than 200 characters.

These calculations should live in the assessment service/business-logic layer, not in the API route and preferably not in the SQLAlchemy model.

---

# 5. Assessment status

An assessment has a lifecycle status.

The currently supported statuses are:

```text
pending_review
issued
```

The normal lifecycle is:

```text
pending_review
      |
      | POST /assessments/{id}/issue
      v
   issued
```

An issued assessment must not be returned to `pending_review`.

The brief states that once a report is issued, it is fixed because copies have already been sent.

However, the summary may still be corrected after issuance. Therefore:

- issuing the report is effectively irreversible;
- the summary remains editable;
- calculated values may change when the underlying summary changes.

---

# 6. `GET /assessments`

## Purpose

Retrieve the reviewer's assessment queue.

This is the primary endpoint for the application's main screen.

The reviewer needs to be able to narrow the queue by:

- assessment status;
- clinician;
- review flag;
- score/domain;
- support-need band.

The endpoint also supports pagination and sorting.

## Signature

```python
@router.get(
    "",
    response_model=AssessmentListResponse,
)
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
) -> AssessmentListResponse:
    ...
```

---

## Query parameters

### `status`

Optional assessment status filter.

Possible values are defined by `AssessmentStatus`, currently:

```text
pending_review
issued
```

Example:

```text
GET /assessments?status=pending_review
```

This should filter the database by:

```text
Assessment.status
```

---

### `clinician_id`

Filters assessments by the clinician who performed the assessment.

In the current database model, the clinician is represented by:

```text
Assessment.clinician_username
```

Therefore the service should map the API parameter to that database field.

Example:

```text
GET /assessments?clinician_id=c-005
```

If the implementation ultimately changes the API parameter name to `clinician_username`, the service/schema/API should be kept internally consistent.

Do not introduce a separate clinician table solely for this endpoint.

---

### `flagged`

Filters assessments according to the calculated review flag.

Example:

```text
GET /assessments?flagged=true
```

Important:

`flagged` is not a database field.

It must be calculated from the assessment's source data:

```text
any substantial domain
OR
any incomplete item
OR
summary length < 200
```

For the current small take-home dataset, it is acceptable to retrieve the relevant assessments and perform this calculation in Python before applying the filter.

Do not add a persisted `flagged` column merely to make this query easier unless there is a strong implementation reason.

---

### `domain`

Identifies a particular assessment domain.

The supported domain names are:

```text
social_communication
sensory_processing
executive_function
emotional_regulation
motor_coordination
```

The domain exists inside the `Assessment.domains` JSON structure.

Example:

```text
GET /assessments?domain=social_communication
```

When `domain` is combined with `band`, the intended meaning is:

> Return assessments where the specified domain has the specified support-need band.

---

### `band`

Filters by support-need band:

```text
minimal
mild
moderate
substantial
```

Example:

```text
GET /assessments?domain=social_communication&band=substantial
```

This means:

> Return assessments whose `social_communication` domain has a `Substantial` calculated band.

If `band` is supplied without `domain`, it can mean:

> Return assessments where any domain has the specified band.

There is no overall assessment score defined by the requirements, so the implementation should not invent one.

---

## Pagination

The endpoint supports:

```text
page
page_size
```

with:

```text
page >= 1
1 <= page_size <= 100
```

The default is:

```text
page = 1
page_size = 25
```

The response should include:

```text
items
page
page_size
total
```

The database query should ideally use pagination at the database level for filters that can be performed directly in SQL.

However, because the domain scoring and review flag are calculated from JSON data, some filtering may need to occur in Python for this take-home implementation.

The implementation should favour correctness and simplicity over premature database optimisation.

---

## Sorting

The endpoint supports:

```text
sort_by
sort_order
```

The current default is:

```text
sort_by = assessed_at
sort_order = desc
```

Therefore, the default queue should show the most recently assessed records first.

Sorting should be implemented against the corresponding database field where possible.

---

## Response

The endpoint returns:

```text
AssessmentListResponse
```

The list response should be relatively lightweight.

It should contain enough information for the queue UI, but should not unnecessarily return the complete item-level assessment structure.

A queue item should conceptually contain:

```text
assessment_id
assessed_at
clinician
status
flagged
domain results
```

The domain results should contain:

```text
domain
percentage
band
```

but not necessarily the individual items.

---

# 7. `GET /assessments/{assessment_id}`

## Purpose

Retrieve the complete assessment for review.

This endpoint is called when the reviewer opens an assessment from the queue.

## Signature

```python
@router.get(
    "/{assessment_id}",
    response_model=AssessmentDetailResponse,
)
async def get_assessment(
    assessment_id: str,
) -> AssessmentDetailResponse:
    ...
```

---

## Database operation

Retrieve:

```text
Assessment
WHERE Assessment.id == assessment_id
```

If no assessment exists, the service should cause the API to return:

```text
404 Not Found
```

Do not silently return an empty object.

---

## Response

The detail response should contain the complete information required by the reviewer:

### Client information

```text
date_of_birth
nhs_number
guardian_contact
safeguarding_notes
```

### Assessment information

```text
assessment_id
assessed_at
clinician
status
```

### Calculated age

Calculate age from:

```text
date_of_birth
assessed_at
```

The result should be expressed as:

```text
years
months
```

Do not store the calculated age in the database.

### Domain results

For every domain:

```text
domain
percentage
band
items
```

The items come directly from the `Assessment.domains` JSON structure.

Each item contains:

```text
code
raw
max
completed
```

### Summary

Return the current assessment summary.

### Review flag

Calculate it from the current assessment data.

### Issue information

For an issued assessment:

```text
issued_at
issued_by
```

should be populated.

For an unissued assessment:

```text
issued_at = null
issued_by = null
```

---

# 8. Audit behaviour when opening an assessment

Opening an individual assessment represents viewing sensitive client information.

Therefore, after successfully retrieving an assessment, the service layer should create an audit event representing:

```text
action = VIEW
entity_type = assessment
entity_id = assessment_id
actor = current user
```

The API route itself should not directly construct or persist the audit event.

Instead, the assessment service should coordinate with the audit service.

Conceptually:

```text
GET /assessments/{id}
        |
        v
AssessmentService.get_assessment()
        |
        +---- retrieve assessment
        |
        +---- calculate response
        |
        +---- record VIEW audit event
        |
        v
AssessmentDetailResponse
```

The exact transaction strategy can be decided when implementing the service layer.

---

# 9. `POST /assessments/{assessment_id}/issue`

## Purpose

Issue the assessment/report after the reviewer is satisfied.

This is a business operation rather than a generic update, so it is represented by `POST`.

## Signature

```python
@router.post(
    "/{assessment_id}/issue",
    response_model=IssueAssessmentResponse,
)
async def issue_assessment(
    assessment_id: str,
) -> IssueAssessmentResponse:
    ...
```

---

## Database operation

Retrieve:

```text
Assessment
WHERE Assessment.id == assessment_id
```

If it doesn't exist:

```text
404 Not Found
```

If its status is already:

```text
issued
```

the operation must not issue it again.

A suitable response is:

```text
409 Conflict
```

because the requested business operation conflicts with the current state.

---

## Issuing behaviour

When successfully issuing:

```text
Assessment.status = issued
Assessment.issued_at = current UTC timestamp
Assessment.issued_by = current user's username
```

The current user must have the appropriate permission, which should be checked by the authentication/authorization layer.

For the current role model, the intended role is:

```text
reviewer
```

---

## Audit event

Issuing the assessment must create an audit event:

```text
action = ISSUE
entity_type = assessment
entity_id = assessment_id
actor = current user
```

The audit event should be created as part of the same logical operation.

---

## Response

Return:

```text
IssueAssessmentResponse
```

containing at least:

```text
assessment_id
status
issued_at
issued_by
```

---

# 10. `PATCH /assessments/{assessment_id}/summary`

## Purpose

Correct the written summary.

The requirements explicitly allow clinicians to correct an occasional typo in the summary **after the report has been issued**.

Therefore this endpoint must work for both:

```text
pending_review
```

and:

```text
issued
```

assessments.

## Signature

```python
@router.patch(
    "/{assessment_id}/summary",
    response_model=SummaryUpdateResponse,
)
async def update_assessment_summary(
    assessment_id: str,
    request: SummaryUpdateRequest,
) -> SummaryUpdateResponse:
    ...
```

---

## Request

The request contains:

```text
summary
```

The maximum summary length is 8000 characters according to the supplied assessment format.

Pydantic validation should enforce the maximum length.

---

## Database operation

Retrieve:

```text
Assessment
WHERE Assessment.id == assessment_id
```

If it does not exist:

```text
404 Not Found
```

Then replace:

```text
Assessment.summary
```

with the new summary.

The operation must not modify:

```text
Assessment.status
Assessment.issued_at
Assessment.issued_by
Assessment.domains
```

---

## Recalculation

Changing the summary may change the calculated review flag.

For example:

```text
old summary length = 150
```

means:

```text
flagged = true
```

If the new summary contains 300 characters and there are no other flag conditions:

```text
flagged = false
```

Therefore the response must calculate the flag from the updated assessment rather than relying on a persisted value.

---

## Audit event

The update must create an audit event:

```text
action = UPDATE
entity_type = assessment
entity_id = assessment_id
actor = current user
```

The audit event should record the change:

```json
[
  {
    "field": "summary",
    "before": "...",
    "after": "..."
  }
]
```

Do not expose or log sensitive information unnecessarily elsewhere.

---

## Response

Return:

```text
SummaryUpdateResponse
```

containing:

```text
assessment_id
summary
flagged
```

The updated `flagged` value should be calculated using the new summary.

---

# 11. Authentication and authorization

The assessment API should not implement authentication itself.

The application has an authentication module providing:

```text
GET /auth/login
GET /auth/me
```

and users have two possible roles:

```text
clinician
reviewer
```

The assessment endpoints should obtain the current authenticated user through FastAPI dependency injection.

Conceptually:

```text
current_user = Depends(get_current_user)
```

The exact authentication implementation is outside this module.

The intended permissions are:

| Operation | Clinician | Reviewer |
|---|---:|---:|
| View assessment queue | Yes | Yes |
| View assessment | Yes | Yes |
| Issue assessment | No | Yes |
| Update summary | Yes | Yes |

If the actual authorization policy changes, it should be implemented in the authorization/service layer rather than by duplicating role checks throughout the route functions.

---

# 12. Service-layer responsibility

The FastAPI routes should remain thin.

For example, `list_assessments()` should conceptually become:

```text
API endpoint
    ↓
AssessmentService.list_assessments(...)
    ↓
repository/database access
    ↓
business calculations
    ↓
AssessmentListResponse
```

Similarly:

```text
issue_assessment()
    ↓
AssessmentService.issue_assessment(...)
    ↓
load assessment
    ↓
validate state
    ↓
update status
    ↓
create audit event
    ↓
return result
```

The API layer should **not** contain:

- SQLAlchemy queries
- scoring algorithms
- review-flag logic
- status-transition rules
- audit-record construction
- transaction management

Those belong in the appropriate lower layers.

---

# 13. Important implementation rules

## Do not persist calculated values unnecessarily

Do not add these columns to `Assessment` merely because they appear in API responses:

```text
age
flagged
percentage
band
```

They are derived from the source data.

---

## Keep the raw domain structure

The `domains` JSON field should preserve the source assessment structure:

```text
domain
  └── items
       ├── code
       ├── raw
       ├── max
       └── completed
```

The service layer transforms this structure into API response models containing calculated results.

---

## Do not create independent CRUD APIs for domains/items

There is no requirement for:

```text
GET /domains
GET /items
POST /items
PATCH /items
DELETE /items
```

Domains and items are components of an assessment, not independent resources in the current design.

---

## Do not allow arbitrary assessment updates

There should not be a generic:

```text
PATCH /assessments/{assessment_id}
```

endpoint.

The requirements distinguish between different business operations.

Currently the supported mutation is specifically:

```text
PATCH /assessments/{assessment_id}/summary
```

and issuing is a separate business action:

```text
POST /assessments/{assessment_id}/issue
```

This makes the allowed state transitions explicit.

---

# 14. Expected endpoint workflow

The main user workflow should be:

```text
1. GET /assessments
        |
        | reviewer filters queue
        v
2. GET /assessments/{assessment_id}
        |
        | reviewer reviews details
        v
3. POST /assessments/{assessment_id}/issue
        |
        v
   Report is issued
```

A later summary correction follows:

```text
PATCH /assessments/{assessment_id}/summary
        |
        v
Summary updated
        |
        v
Derived values recalculated
        |
        v
Audit event recorded
```

This is the primary end-to-end path required by the take-home.

---

# 15. Error handling expectations

The service implementation should translate normal business failures into appropriate HTTP errors.

At minimum:

| Situation | HTTP status |
|---|---:|
| Assessment does not exist | `404 Not Found` |
| Assessment already issued | `409 Conflict` |
| User not authenticated | `401 Unauthorized` |
| User lacks required role | `403 Forbidden` |
| Invalid request data | `422 Unprocessable Entity` |

FastAPI/Pydantic will handle most request-validation errors automatically.

Business validation should remain in the service layer.

---

# 16. Async implementation

All database access must use the asynchronous SQLAlchemy stack.

The expected architecture is:

```text
FastAPI async endpoint
        ↓
async service method
        ↓
async repository/database operation
        ↓
AsyncSession
```

Do not introduce synchronous SQLAlchemy sessions into the assessment module.

The endpoint definitions are already asynchronous and should remain so.

---

# 17. Design philosophy

This module deliberately favours a simple design appropriate for the take-home exercise.

The important architectural boundaries are:

```text
API
 ↓
Service / business logic
 ↓
SQLAlchemy / persistence
```

The assessment itself is the primary aggregate. Its domain/item structure is stored as JSON because those objects are not independently managed resources in this application.

The implementation should prioritize:

1. Correct business logic.
2. The complete review workflow.
3. Clear separation of API and business logic.
4. Auditability.
5. Correct handling of edge cases.
6. Simplicity appropriate to the four-hour scope.

Do not introduce additional infrastructure or database normalization unless a concrete requirement justifies it.