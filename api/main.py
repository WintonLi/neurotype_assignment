from app.assessment.api import router as assessment_router
from app.audit.api import router as audit_router
from app.auth.api import auth_router, users_router
from fastapi import FastAPI

app = FastAPI()

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(assessment_router, prefix=API_PREFIX)
app.include_router(audit_router, prefix=API_PREFIX)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
