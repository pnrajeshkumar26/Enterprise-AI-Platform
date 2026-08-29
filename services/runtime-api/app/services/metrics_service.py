from datetime import datetime

from app.core.runtime_metrics import (
    LLM_MODELS_CONFIGURED,
    LLM_RUNTIME_UP,
)
from app.models.model_registry import list_models


class MetricsService:
    """
    Provides human-readable runtime metrics.

    Prometheus-native metrics are exposed separately at /metrics.
    """

    def __init__(self):
        self.started_at = datetime.utcnow()

        # Initialize runtime-level Prometheus gauges immediately.
        LLM_MODELS_CONFIGURED.set(len(list_models()))
        LLM_RUNTIME_UP.set(1)

    def get_metrics(self):
        return {
            "status": "running",
            "engine": "orchestrator",
            "models_configured": len(list_models()),
            "uptime_seconds": int(
                (datetime.utcnow() - self.started_at).total_seconds()
            ),
        }


metrics_service = MetricsService()
