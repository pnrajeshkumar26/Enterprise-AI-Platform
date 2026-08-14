import logging

from app.clients.vllm_client import VLLMClient
from app.core.config import settings
from app.models.model_registry import get_model
from app.schemas.generate import GenerateResponse
from app.services.metrics_service import metrics_service

logger = logging.getLogger(__name__)


class GenerateService:
    """
    Business logic for text generation.
    """

    def __init__(self):
        self.client = VLLMClient(settings.vllm_url, settings.vllm_model_id)

    def generate(
        self,
        model_name: str,
        prompt: str,
    ) -> GenerateResponse:

        model = get_model(model_name)

        if model is None:
            raise ValueError(f"Model '{model_name}' not found")

        metrics_service.increment_requests()

        logger.info("Sending request to vLLM for model %s", model_name)

        generated_text = self.client.generate(prompt)

        return GenerateResponse(
            model=model.name,
            response=generated_text,
            status="success",
        )


generate_service = GenerateService()