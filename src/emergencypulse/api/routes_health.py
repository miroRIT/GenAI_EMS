from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from emergencypulse.db.session import get_session

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns ok when the API process is running.",
    responses={200: {"description": "API process is live."}},
)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/readyz",
    response_model=HealthResponse,
    summary="Readiness check",
    description="Verifies the API can reach the database before receiving traffic.",
    responses={
        200: {"description": "API and database are ready."},
        503: {"description": "Database is unavailable."},
    },
)
async def readyz(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    await session.execute(text("SELECT 1"))
    return HealthResponse(status="ready")
