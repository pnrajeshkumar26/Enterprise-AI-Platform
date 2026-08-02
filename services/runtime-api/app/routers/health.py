from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import health_service

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Runtime Health Check",
)
def health():
    return health_service.get_health()