from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": "runtime-api",
        "version": settings.app_version,
        "environment": settings.app_env,
    }