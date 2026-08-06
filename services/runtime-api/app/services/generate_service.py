import logging

from app.engines import LlamaEngine
from app.models.model_registry import get_model
from app.schemas.generate import GenerateResponse
from app.services.metrics_service import metrics_service

logger = logging.getLogger(__name__)


class GenerateService:
    """Business logic for text generation."""

    def __init__(self):
        pass

    def generate(self, model_name: str, prompt: str) -> GenerateResponse:
        model = get_model(model_name)

        if model is None:
            logger.warning("Requested model was not found: %s", model_name)
            raise ValueError(f"Model '{model_name}' not found")

        logger.info("Selected model: %s", model.name)
        logger.debug("Model metadata: %s", model)

        metrics_service.increment_requests()

        engine = LlamaEngine(model.model_path)
        generated_text = engine.generate(prompt)

        return GenerateResponse(
            model=model.name,
            response=generated_text,
            status="success",
        )


generate_service = GenerateService()