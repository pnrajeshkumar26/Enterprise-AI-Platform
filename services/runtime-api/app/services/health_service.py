from app.core.config import settings
from app.models.model_registry import list_models


class HealthService:
    """
    Runtime API health service.

    The Runtime API is an orchestration/routing layer.
    GPU-specific health is owned by the inference backends.
    """

    def get_health(self):
        return {
            "status": "healthy",
            "service": "runtime-api",
            "version": settings.app_version,
            "environment": settings.app_env,
            "inference_engine": "orchestrator",
            "models_configured": len(list_models()),
            "gpu_available": None,
        }


health_service = HealthService()
