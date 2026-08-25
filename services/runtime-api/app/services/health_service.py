from app.core.config import settings
from app.models.model_registry import list_models

try:
    from llama_cpp import llama_supports_gpu_offload
except ImportError:
    llama_supports_gpu_offload = None


class HealthService:

    def get_health(self):

        gpu_available = False

        if llama_supports_gpu_offload is not None:
            try:
                gpu_available = bool(llama_supports_gpu_offload())
            except Exception:
                gpu_available = False

        return {
            "status": "healthy",
            "service": "runtime-api",
            "version": settings.app_version,
            "environment": settings.app_env,
            "inference_engine": "llama.cpp",
            "models_loaded": len(list_models()),
            "gpu_available": gpu_available,
        }


health_service = HealthService()
