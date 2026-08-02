from app.core.config import settings
from app.models.model_registry import list_models


class HealthService:

    def get_health(self):

        return {
            "status": "healthy",
            "service": "runtime-api",
            "version": settings.app_version,
            "environment": settings.app_env,
            "inference_engine": "llama.cpp",
            "models_loaded": len(list_models()),
            "gpu_available": False,
        }


health_service = HealthService()