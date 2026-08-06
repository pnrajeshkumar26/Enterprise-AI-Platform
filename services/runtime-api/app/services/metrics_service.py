from datetime import datetime

from app.models.model_registry import get_model


class MetricsService:
    """Provides runtime metrics."""

    def __init__(self):
        self.started_at = datetime.utcnow()
        self.total_requests = 0

    def increment_requests(self):
        self.total_requests += 1

    def get_metrics(self):
        model = get_model("TinyLlama")

        uptime = (
            datetime.utcnow() - self.started_at
        ).total_seconds()

        return {
            "status": "running",
            "engine": "llama.cpp",
            "model": model.name,
            "provider": model.provider,
            "quantization": model.quantization,
            "context_length": model.context_length,
            "cached": True,
            "enabled": model.enabled,
            "uptime_seconds": int(uptime),
            "total_requests": self.total_requests,
        }


metrics_service = MetricsService()