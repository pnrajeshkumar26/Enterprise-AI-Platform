import logging

from app.models.model_registry import get_model
from app.schemas.generate import GenerateResponse
from app.services.metrics_service import metrics_service

logger = logging.getLogger(__name__)


class GenerateService:
    """Business logic for text generation."""

    def generate(self, model_name: str, prompt: str) -> GenerateResponse:

        model = get_model(model_name)

        if model is None:
            raise ValueError(f"Model '{model_name}' not found")

        metrics_service.increment_requests()

        logger.info("Received prompt for model %s", model_name)

        return GenerateResponse(
            model=model.name,
            response="Inference server integration will be added in Sprint 8.",
            status="success",
        )


generate_service = GenerateService()