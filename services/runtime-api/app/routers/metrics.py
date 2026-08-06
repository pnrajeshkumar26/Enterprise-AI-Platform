from fastapi import APIRouter

from app.services.metrics_service import metrics_service

router = APIRouter(
    prefix="/runtime",
    tags=["Runtime"],
)


@router.get("/metrics")
def runtime_metrics():
    return metrics_service.get_metrics()