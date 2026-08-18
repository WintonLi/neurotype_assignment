# Neurotype Engineering Take-Home — Requirements Summary

## 1. Project Overview

Build a small web application for reviewing neurodevelopmental assessments.

The system represents a simplified clinical workflow:

1. A clinician performs a structured assessment of a young person.
2. The assessment contains scores across several domains and a written summary.
3. A reviewing clinician reviews the assessment.
4. The reviewer can filter/narrow a queue of assessments.
5. The reviewer opens an individual assessment and sees the complete assessment information.
6. When satisfied, the reviewer issues the report.
7. Issuing the report is effectively final because copies are assumed to have already been sent to the family, school and GP.
8. A summary may nevertheless be corrected later if an occasional typo is discovered.
9. Client records must be auditable: the system must be able to show who looked at what, when, and what changed.

The clinical instrument and scoring system are **invented for this exercise**, and all supplied data is synthetic. No clinical knowledge is required.

---

# 2. Technology Requirements

The application must contain:

- Python backend
- React + TypeScript frontend
- Docker Compose

The application must run on a clean machine with only Docker installed.

The following must work:

```text
docker compose up
```

and:

```text
http://localhost:8000/health
```

must return HTTP `200`.

The frontend must be available at:

```text
http://localhost:5173
```

Everything else is an engineering choice.

The project uses:

- FastAPI for the backend
- Async Python / async SQLAlchemy
- SQLite initially
- SQLAlchemy ORM
- React + TypeScript frontend

The database model should remain database-agnostic so that SQLite can later be replaced by another relational database.

---

# 3. Supplied Assessment Data

The clinician application produces assessments as JSONL:

```text
assessments.jsonl
```

JSONL means there is one JSON assessment object per line.

The supplied sample contains approximately 100 assessments.

An assessment has approximately this structure:

```json
{
  "assessment_id": "a-00001",
  "client": {
    "date_of_birth": "2014-03-02",
    "nhs_number": "999 476 5919",
    "guardian_contact": "j.okafor@example.com",
    "safeguarding_notes": "Contact via mother only. Father not to be given dates."
  },
  "assessed_at": "2026-03-02T09:30:00+00:00",
  "clinician_id": "c-005",
  "domains": [
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
  ],
  "summary": "Free text, up to 8000 characters."
}
```

There are five fixed domains:

```text
social_communication
sensory_processing
executive_function
emotional_regulation
motor_coordination
```

Each domain contains between three and six items.

An item can be incomplete if the young person was unable or unwilling to complete it.

---

# 4. Assessment Terminology

## Assessment

One complete evaluation of a young person.

An assessment contains:

- client information
- assessment date/time
- clinician
- domains and their items
- written summary

## Domain

A broad area being assessed.

There are exactly five domains:

- Social communication
- Sensory processing
- Executive function
- Emotional regulation
- Motor coordination

## Item

An individual scored element within a domain.

An item contains:

- `code`
- `raw`
- `max`
- `completed`

## Raw score

The actual score obtained for an item.

## Max score

The maximum possible score for the item.

## Queue

The review queue is a **worklist of assessments waiting to be reviewed**.

It is not a technical message queue such as Kafka, RabbitMQ or Redis.

## Reviewer

The clinician who reviews an assessment and can issue its report.

---

# 5. Scoring Rules

The scoring rules are not contained in the JSONL input. The application must calculate them.

## Domain percentage

Each domain receives a percentage calculated as:

```text
mean(raw / max * 100)
```

across its items.

Example:

```text
Item 1: 10 / 20 = 50%
Item 2: 15 / 20 = 75%
Item 3: 12 / 20 = 60%

Domain percentage = mean(50, 75, 60)
                  = 61.67%
```

### Important ambiguity

The brief does not explicitly specify how an incomplete item with:

```text
raw = null
completed = false
```

should participate in the percentage calculation.

The implementation must make an explicit judgement about this and document it.

---

# 6. Support-Need Bands

Each domain percentage maps to a support-need band:

| Percentage | Band |
|---:|---|
| 0–39 | Minimal |
| 40–54 | Mild |
| 55–84 | Moderate |
| 85–100 | Substantial |

There is no overall assessment score defined by the brief.

Bands are calculated per domain.

---

# 7. Review Flag

Each assessment has a calculated review flag.

The flag is ON if **any** of these conditions is true:

```text
1. Any domain has the Substantial band
OR
2. Any item is incomplete
OR
3. The summary contains fewer than 200 characters
```

Conceptually:

```python
flagged = (
    has_substantial_domain
    or has_incomplete_item
    or len(summary) < 200
)
```

The flag is a derived value and should not be treated as authoritative stored data.

---

# 8. Age Calculation

The report must show the young person's age in:

```text
years and months
```

at the date of assessment.

Age should be calculated from:

```text
date_of_birth
assessed_at
```

It should not be stored as a permanent database value.

---

# 9. Assessment Review Queue

Reviewing clinicians work through a queue containing assessments from the service.

The queue must allow reviewers to narrow assessments by:

1. **How the assessment scored**
2. **Whether it is flagged**
3. **Which clinician performed the assessment**

The current API interprets "how it scored" using the per-domain support-need bands.

Supported filters are therefore:

```text
status
clinician
flagged
domain
band
```

Example:

```text
GET /assessments?domain=social_communication&band=substantial
```

means:

> Find assessments where the social communication domain has a Substantial band.

If `band` is supplied without `domain`, it can mean:

> Find assessments where any domain has that band.

The application should not invent an overall assessment score because the brief does not define one.

The queue should support pagination and sorting.

---

# 10. Assessment Lifecycle

The current assessment statuses are:

```text
pending_review
issued
```

Normal lifecycle:

```text
pending_review
      |
      | issue report
      v
   issued
```

Once issued:

- the report cannot be un-issued;
- the status should remain `issued`;
- `issued_at` should record when it was issued;
- `issued_by` should record who issued it.

However, the written summary may still be corrected after issuance.

---

# 11. Core User Workflow

The most important end-to-end workflow is:

```text
Open review queue
      |
      v
Narrow/filter queue
      |
      v
Open an assessment
      |
      v
Review client information,
domain results and summary
      |
      v
Issue report
```

This workflow must work end to end.

The brief explicitly prioritises:

> A narrow path that works beats a broad one that does not.

Do not sacrifice the core workflow in order to implement a large number of secondary features.

---

# 12. Assessment Detail

Opening an assessment must show the whole assessment:

## Client

- date of birth
- NHS number
- guardian contact
- safeguarding notes

## Assessment

- assessment ID
- assessment date/time
- clinician
- status

## Age

Calculated age in years and months.

## Domains

For each domain:

- domain name
- calculated percentage
- calculated support-need band
- individual items

For each item:

- code
- raw score
- maximum score
- completion status

## Summary

The complete written summary.

## Review flag

The current calculated review flag.

## Issue information

If issued:

- issued timestamp
- user who issued it

---

# 13. Summary Editing

Clinicians may need to correct an occasional typo in the summary after the report has been issued.

Therefore the summary must remain editable.

The API exposes:

```text
PATCH /assessments/{assessment_id}/summary
```

Only the summary should be changed by this operation.

It must not:

- un-issue the report;
- modify the raw assessment items;
- modify the issue timestamp;
- modify who issued the report.

Because the review flag depends partly on summary length, changing the summary may change the calculated review flag.

---

# 14. Audit Requirements

Client records must be auditable.

The system must be able to answer:

```text
Who looked at what?
When?
What changed?
```

Important actions should create audit events.

At minimum, the assessment workflow should audit:

```text
VIEW
ISSUE
UPDATE
```

For a summary update, the audit event should preserve the change, conceptually:

```json
[
  {
    "field": "summary",
    "before": "old summary",
    "after": "new summary"
  }
]
```

Opening an individual assessment should generate a `VIEW` audit event.

Issuing an assessment should generate an `ISSUE` audit event.

Updating the summary should generate an `UPDATE` audit event.

The audit implementation should be kept separate from the assessment API implementation.

---

# 15. Authentication and Users

The application has two fixed user roles:

```text
clinician
reviewer
```

Users are provisioned and managed manually for this exercise.

There is no need to implement a user-management CRUD API.

The authentication API is deliberately simple:

```text
POST /auth/login
GET  /auth/me
```

The current user must be available to the service layer so that:

- permissions can be checked;
- audit events can identify the actor;
- issue operations can record `issued_by`.

Intended permissions:

| Operation | Clinician | Reviewer |
|---|:---:|:---:|
| View assessment queue | Yes | Yes |
| View assessment | Yes | Yes |
| Issue assessment | No | Yes |
| Update summary | Yes | Yes |

Authentication and authorization should be implemented separately from assessment business logic.

---

# 16. Database Design

The current database intentionally uses a simple model.

There are three main tables:

```text
users
assessments
audit_events
```

## Users

The user model contains only:

```text
username
password_hash
roles
assessments
```

`username` is the user identifier.

Roles are the two fixed values:

```text
clinician
reviewer
```

Roles can be stored as a JSON list.

---

## Assessments

The assessment is the main business aggregate.

It contains:

```text
id
date_of_birth
nhs_number
guardian_contact
safeguarding_notes
assessed_at
clinician_username
domains
summary
status
issued_at
issued_by
```

The nested domain/item structure is stored in the `domains` JSON field.

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
      }
    ]
  }
]
```

There are deliberately no separate database tables for:

- clients
- assessment domains
- assessment items

These are considered components of an assessment rather than independent resources.

This keeps the implementation simple and appropriate for the scope of the exercise.

---

# 17. Derived Values and Database Source of Truth

The database stores the assessment's source facts.

The following should be calculated by the business logic:

```text
age
domain percentage
support-need band
review flag
```

Do not create redundant persistent columns for these values unless there is a compelling reason.

The API should calculate them when constructing its response.

This avoids stale derived values, particularly because the summary can change after an assessment has been issued.

---

# 18. REST API Summary

## Authentication

```text
POST /auth/login
GET  /auth/me
```

## Assessments

```text
GET   /assessments
GET   /assessments/{assessment_id}
POST  /assessments/{assessment_id}/issue
PATCH /assessments/{assessment_id}/summary
```

## Audit

```text
GET /audit/events
```

---

# 19. Assessment API Details

### `GET /assessments`

Returns the review queue.

Supported query parameters:

```text
status
clinician_id
flagged
domain
band
page
page_size
sort_by
sort_order
```

Default pagination:

```text
page = 1
page_size = 25
```

Maximum page size:

```text
100
```

Default sorting:

```text
assessed_at DESC
```

The queue response should contain lightweight domain results rather than all item-level details.

---

### `GET /assessments/{assessment_id}`

Returns the complete assessment.

It should:

1. Retrieve the assessment from the database.
2. Calculate age.
3. Calculate domain percentages.
4. Calculate domain bands.
5. Calculate the review flag.
6. Return the complete domain/item structure.
7. Record an audit `VIEW` event.

Return `404` if the assessment does not exist.

---

### `POST /assessments/{assessment_id}/issue`

Issues the report.

It should:

1. Retrieve the assessment.
2. Check that it exists.
3. Check that it is not already issued.
4. Check the current user's permission.
5. Set status to `issued`.
6. Set `issued_at`.
7. Set `issued_by`.
8. Record an audit `ISSUE` event.
9. Return the issue result.

If already issued, return `409 Conflict`.

There is no un-issue operation.

---

### `PATCH /assessments/{assessment_id}/summary`

Updates only the written summary.

It should:

1. Retrieve the assessment.
2. Check that it exists.
3. Replace the summary.
4. Leave issue status unchanged.
5. Recalculate the review flag when constructing the response.
6. Record an audit `UPDATE` event containing the before/after summary.
7. Return the updated summary and review flag.

This endpoint must work even if the assessment has already been issued.

---

# 20. Backend Architecture

The backend should maintain a clear separation between:

```text
FastAPI API
      |
      v
Service / Business Logic
      |
      v
SQLAlchemy ORM / Database
```

The API layer should be thin.

Do not put:

- SQL queries
- scoring algorithms
- state-transition rules
- audit persistence
- complex business logic

directly into FastAPI route functions.

The service layer should own the business rules.

Database access should use asynchronous SQLAlchemy.

Expected flow:

```text
async FastAPI endpoint
        |
        v
async service
        |
        v
Async SQLAlchemy session
        |
        v
SQLite
```

The ORM models should avoid database-specific features so the application can later move from SQLite to another relational database.

---

# 21. Error Handling

At minimum:

| Situation | HTTP status |
|---|---:|
| Assessment not found | `404 Not Found` |
| Already issued | `409 Conflict` |
| Not authenticated | `401 Unauthorized` |
| Insufficient permission | `403 Forbidden` |
| Invalid request | `422 Unprocessable Entity` |

FastAPI/Pydantic should handle request-schema validation.

Business errors should be handled by the service layer and translated into appropriate HTTP responses.

---

# 22. Edge Cases to Consider

The implementation should not only handle the happy path.

Important cases include:

- assessment does not exist;
- assessment is already issued;
- no assessments match a filter;
- incomplete assessment items;
- incomplete items with `raw = null`;
- summary shorter than 200 characters;
- summary exactly 200 characters;
- summary at the maximum length;
- domain score exactly on band boundaries;
- malformed or unexpected input JSON;
- missing assessment fields;
- invalid domain names;
- invalid status values;
- invalid clinician/user references;
- empty result sets;
- pagination beyond the available results.

The scoring boundaries are particularly important:

```text
39 → Minimal
40 → Mild
54 → Mild
55 → Moderate
84 → Moderate
85 → Substantial
```

---

# 23. Explicit Requirements vs Engineering Decisions

The following are explicitly required by the brief:

- Python backend
- React + TypeScript frontend
- Docker Compose
- `/health` returns 200
- frontend on port 5173
- assessment queue
- queue filtering
- assessment detail view
- domain scoring
- support-need bands
- review flag
- age calculation
- report issuing
- post-issue summary correction
- auditability
- working end-to-end reviewer workflow

The following are implementation decisions rather than explicit requirements:

- FastAPI
- async SQLAlchemy
- SQLite
- simple login implementation
- two roles: clinician and reviewer
- flat assessment database model
- storing domains/items as JSON
- Python-side calculation/filtering for the small dataset
- exact API structure
- exact audit schema
- exact authentication mechanism

Where the original brief is unclear, make a reasonable judgement and document it rather than pretending the requirement is unambiguous.

---

# 24. Scope and Prioritisation

The exercise is intentionally larger than what can reasonably be completed in approximately four hours.

The expected approach is therefore to prioritise.

The most important functionality is:

```text
Reviewer opens queue
        ↓
Reviewer narrows queue
        ↓
Reviewer opens assessment
        ↓
Reviewer issues report
```

A smaller, reliable implementation is preferable to a larger implementation with incomplete functionality.

Do not spend significant time implementing features that do not contribute to this workflow.

---

# 25. Docker / Submission Requirements

The final repository must work from a clean clone on a machine with only Docker installed.

The evaluator should be able to run:

```bash
docker compose up
```

and then:

```text
http://localhost:5173
```

should serve the frontend.

```text
http://localhost:8000/health
```

should return HTTP 200.

The repository should retain its Git history.

The submission should contain:

```text
README.md
DECISIONS.md
agent/
```

`README.md` should explain how to run the application.

`DECISIONS.md` should be one page or less and explain:

- what was built;
- what was intentionally omitted;
- why;
- ambiguous/incomplete requirements;
- judgement calls;
- places where the AI-generated implementation was overridden;
- known problems;
- approximate time spent and where it went.

The `agent/` directory should contain the AI coding-agent session transcripts/configuration as requested by the interviewers.

---

# 26. AI-Assisted Development Requirement

Use of an AI coding agent is **required**, not merely permitted.

The interviewers are evaluating approximately equally:

1. The quality of the resulting software.
2. The ability to work effectively with an AI coding agent.

The agent should be used as part of normal development.

The developer is expected to:

- provide useful context;
- decompose the problem;
- direct the agent;
- verify generated code;
- test the implementation;
- identify incorrect assumptions;
- reject bad output;
- make engineering decisions independently;
- understand and defend the final implementation.

Do not blindly accept generated code.

The follow-up interview will specifically examine how the solution was produced and whether the developer understands the resulting code.

---

# 27. Follow-Up Interview

The second-stage interview includes approximately 60 minutes of screen sharing.

The interviewers may:

1. Ask for a walkthrough of the implementation.
2. Ask what was deliberately left out.
3. Select specific code and ask why it was implemented that way.
4. Ask for a new change that was not in the original requirements.
5. Ask the candidate to implement that change live using their normal AI coding setup.
6. Discuss missing functionality, failure modes and future improvements.

Therefore the implementation should be understandable and easy to modify.

The candidate should be able to explain the important architectural and business-logic decisions without relying on the AI agent.

---

# 28. Key Design Principle

The implementation should be **simple but deliberate**.

The goal is not to build a production-scale clinical information system within four hours.

The goal is to demonstrate that the developer can:

- understand an ambiguous problem;
- choose sensible boundaries;
- implement the core workflow;
- use AI effectively;
- verify AI-generated code;
- handle important edge cases;
- make reasonable trade-offs;
- explain those trade-offs clearly.

The primary success criterion is therefore:

```text
Queue
  ↓
Filter
  ↓
Assessment
  ↓
Issue
  ↓
Audit
```

working correctly end to end.