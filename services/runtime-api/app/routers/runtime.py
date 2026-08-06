from fastapi import APIRouter

from app.services.runtime_service import runtime_service

router = APIRouter(
    prefix="/runtime",
    tags=["Runtime"],
)


@router.get(
    "/status",
)
def runtime_status():
    return runtime_service.get_status()