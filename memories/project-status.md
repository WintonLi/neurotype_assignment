# Neurotype take-home — status summary (2026-08-19)

## Stack / structure
- Backend: FastAPI + async SQLAlchemy, `api/` folder. Layering: `api.py` (routes, thin) → `*_service.py` (business logic) → `*_repo.py`/direct session (persistence).
- Frontend: React + Vite + TypeScript + Ant Design + Zustand, `web/` folder.
- DB (local dev): SQLite via `aiosqlite`, hardcoded in `api/app/database.py` as `sqlite+aiosqlite:///./data/app.db`.

## ⚠️ Known gap — DATABASE_URL not wired
`docker-compose.yml` sets `DATABASE_URL: postgresql://app:app@db:5432/app` for the `api` service and runs a `db` (Postgres) container, but `api/app/database.py` **hardcodes** the SQLite URL and never reads `DATABASE_URL` from the environment. So `docker compose up` currently would NOT actually use Postgres — the api container would use its own local SQLite file instead. Needs fixing before submission: either read `os.getenv("DATABASE_URL", sqlite_fallback)` in `database.py`, or remove the `db`/Postgres service from docker-compose if SQLite is the intended final choice.

## Backend — implemented
- `app/assessment/`: `models.py` (Assessment ORM, JSON `domains` column), `schemas.py`, `assessment_repo.py` (AsyncSession queries), `assessment_service.py` (scoring: domain % = mean of raw/max over *completed, non-null* items only; bands 0-39/40-54/55-84/85-100; flagged = any substantial band OR any incomplete item OR summary <200 chars; age calc; issue lifecycle; summary PATCH), `api.py` (routes wired to service, HTTP error translation for 404/409/403).
- `app/audit/`: `audit_service.py` (dumb recorder + `list_events` with SQL filters), `api.py` wired. `AssessmentService` takes an injected `AuditService` (constructed explicitly in `assessment/api.py` routes) and records VIEW/ISSUE/UPDATE events.
- `app/auth/`: `models.py`, `schemas.py`, `dependencies.py` (`get_current_user` — reads `X-Username` header, looks up user in DB, no real login/token check). `auth/api.py` routes (`/auth/login`, `/auth/me`) are still `NotImplementedError` — not needed since the frontend never calls them (see below).
- `app/migrations/` (plain async scripts, not Alembic despite it being a dependency):
  - `m01_create_tables.py` — idempotent `create_all` for missing tables only, logs and skips if all exist.
  - `m02_populate_data.py` — loads `data/assessments.jsonl`, validates `client`/`domains` shape strictly, discards+logs invalid lines, auto-creates any missing clinician `User` rows (role `clinician`, password `123` hashed) before inserting assessments so the FK is satisfied, skips duplicates on rerun.
  - `m03_create_users.py` — creates/overwrites two fixed users: `test` (clinician), `reviewer` (reviewer), both password `123`, hashed via local PBKDF2-SHA256 helper (salted, `pbkdf2_sha256$600000$salt$hash` format — duplicated in m02 and m03, could be extracted to a shared helper later).
  - Run order: `m01` then `m03` (or `m02`) — `python -m app.migrations.mNN_...`.
- CORS: `main.py` adds `CORSMiddleware` reading `WEB_ORIGIN` env var (default `http://localhost:5173`), `allow_headers=["*"]` (needed for custom `X-Username` header).

## Frontend — implemented
- `store/assessmentStore.ts` — **deliberately minimal**, only `username`/`login`/`logout`, persisted to `localStorage` under key from `api/client.ts`. User explicitly rejected a larger all-in-one Zustand store design; all list/detail data fetching lives in component-local state + `services/`, not the store.
- `api/client.ts` — axios instance, baseURL `${VITE_API_URL ?? '/api/v1'}` (relative by default so the Vite dev proxy works; docker sets `VITE_API_URL` absolute). Request interceptor attaches `X-Username` from `localStorage`.
- `services/assessmentService.ts` — `listAssessments`, `getAssessment`, `issueAssessment`, `updateAssessmentSummary`. Types mirror backend snake_case field names directly (no camelCase mapping layer).
- `services/auditService.ts` — `listAuditEvents`.
- `components/AssessmentTable.tsx` — shared table (filters: clinician/flagged/domain/band, server-side pagination, sort desc by assessed_at, auto-selects first row / keeps selection valid on refetch). `AssessmentQueue.tsx` (`status=pending_review`) and `IssusedAssessment.tsx` (`status=issued`, filename has a typo "Issused" — not renamed) are thin wrappers around it.
- `components/DetailedAssessment.tsx` — Descriptions-based detail view; Issue button (Popconfirm-guarded, hidden via `showIssueButton={false}` prop when used from the Issued view); Edit Summary reveals inline `TextArea` (not a modal); action errors (issue/summary save) shown via closable `notification.error`, load errors via persistent `Alert`. `onChanged` callback fires after issue or summary save so parent can bump a `refreshToken` to refetch the list.
- `views/Queue.tsx` / `views/Assessment.tsx` (issued page) — own `selectedAssessmentId`/`refreshToken` state, wire the table + detail components together.
- `views/Audit.tsx` — filters (entity type/id, actor, action) + paginated table of audit events.
- `views/Login.tsx` — username/password form, **no backend call** — just calls `store.login(username)`; password field is decorative only. Tells user valid usernames are `test`/`reviewer`. Already-logged-in users redirected to `/queue`.
- `App.tsx` — `RequireAuth` wrapper redirects to `/login` when `username` is null (also triggers automatically on logout since it's a subscribed hook).
- `views/AppLayout.tsx` — side menu defaults collapsed; Logout item pinned to bottom of Sider showing current username.

## Known simple/decorative pieces (by design, not bugs)
- Login page doesn't validate password or call any auth endpoint — auth is effectively "any known username in the `users` table".
- `auth/api.py` login/me endpoints unimplemented — not currently required by the frontend.
- No Alembic migrations despite the dependency being listed; `app/migrations/*.py` are plain idempotent async scripts run manually.

## Suggested next steps
1. Fix `DATABASE_URL` wiring in `database.py` (see gap above) — important before `docker compose up` is used for real evaluation.
2. Decide whether to keep Postgres in docker-compose or drop it for SQLite-only, and update `docker-compose.yml`/`Dockerfile` accordingly.
3. Extract the duplicated password-hash helper from `m02_populate_data.py`/`m03_create_users.py` if touched again.
4. Write `DECISIONS.md` per the brief (ambiguities: incomplete-item scoring exclusion, flagged definition, simple header-based auth) before submission.
