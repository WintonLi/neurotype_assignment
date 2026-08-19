# Decisions

## What I built

I implemented the core assessment workflow with FastAPI, async SQLAlchemy, React/Vite, Ant Design and Zustand. The backend separates API, service and repository responsibilities, with business rules for scoring, support-need bands, review flags, assessment lifecycle, and audit events. I also added idempotent database/data migrations and seeded users.

The frontend provides login, an assessment queue with server-side filtering/pagination, assessment detail and issuing, issued assessments, and audit events.

## What I cut / simplified

I deliberately kept authentication simple. The current implementation identifies users through `X-Username` and applies role checks, rather than implementing production authentication/tokens. The existing login/me backend endpoints remain incomplete.

I also kept assessment domains as JSON rather than introducing a more complex relational model.

I rejected an initial Copilot-generated Zustand store because it was significantly over-engineered: it attempted to manage authentication, multiple lists, filters, pagination, selected assessments, audit state, mappings and extensive error/loading state in one large store. I simplified this to state required by the actual views.

## Ambiguities and agent overrides

For incomplete items, I excluded them from scoring but keep the assessment flagged. Issuing is treated as irreversible, while the summary remains editable.

I treated Copilot's output as implementation assistance rather than authority. I found and corrected issues through testing, including an audit timestamp mismatch and migration/SQLAlchemy issues. The assessment workflow was validated with an async SQLite smoke test covering filtering, scoring, auditing, issuing and summary updates.

## Known issues

Database not scalable, poor data migration management, no user management, fake authentication, zero security, docker image doing too much, front-end not responsive, many detailed implementations written by LLM left unreviewed, and many...

## Time

Approximately **one working day** in total, including setting up development environments and tools. The total coding/ reviewing time should be less than 4 hours. Most time went into understanding the existing skeleton and requirements, implementing the backend and frontend, and testing/reviewing agent-generated code rather than blindly accepting it (I would say 5% coding, 95% reviewing).
