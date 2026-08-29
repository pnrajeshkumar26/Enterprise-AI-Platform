from fastapi import APIRouter
from prometheus_client import make_asgi_app

from app.core.runtime_metrics import (
    LLM_MODELS_CONFIGURED,
    LLM_RUNTIME_UP,
)
from app.models.model_registry import list_models
from app.services.metrics_service import metrics_service


router = APIRouter(
    prefix="/runtime",
    tags=["Runtime"],
)


@router.get("/metrics")
def runtime_metrics():
    """
    Human-readable runtime metrics.

    Prometheus scraping is exposed separately at /metrics.
    """
    return metrics_service.get_metrics()


# Prometheus-native endpoint:
#
# /metrics
#
# This ASGI application is mounted from app.main.py.
prometheus_app = make_asgi_app()
