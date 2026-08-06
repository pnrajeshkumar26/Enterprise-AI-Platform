from app.models.model_registry import get_model
from app.schemas.runtime import RuntimeStatusResponse


class RuntimeService:
    """Provides runtime engine information."""

    def get_status(self) -> RuntimeStatusResponse:

        model = get_model("TinyLlama")

        return RuntimeStatusResponse(
            status="running",
            engine="llama.cpp",
            model=model.name,
            provider=model.provider,
            quantization=model.quantization,
            context_length=model.context_length,
            cached=True,
            enabled=model.enabled,
        )


runtime_service = RuntimeService()
from app.services.runtime_service import runtime_service