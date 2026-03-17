from fastapi import APIRouter

from app.models.response_models import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
