import logging

from app.clients.vllm_client import VLLMClient
from app.core.config import settings
from app.models.model_registry import get_model
from app.schemas.generate import GenerateResponse
from app.services.metrics_service import metrics_service

logger = logging.getLogger(__name__)


class GenerateService:
    """
    Routes generation requests to the correct inference engine.

    tinyllama -> local llama.cpp
    phi3      -> vLLM

    TinyLlama is initialized lazily so that the Runtime API can start
    without consuming the GPU when vLLM is the active inference engine.
    """

    def __init__(self):
        self.llama_engine = None

        # vLLM is remote from the Runtime API perspective.
        # Runtime API itself does not initialize a GPU engine at startup.
        self.vllm_client = VLLMClient(
            settings.vllm_url,
            settings.vllm_model_id,
        )

        logger.info(
            "Runtime API initialized with vLLM endpoint: %s",
            settings.vllm_url,
        )

    def _initialize_tinyllama(self):
        """
        Lazily initialize the local TinyLlama llama.cpp engine.

        This keeps TinyLlama from consuming GPU memory during application
        startup when Phi-3/vLLM is the active inference backend.
        """

        if self.llama_engine is not None:
            return

        from app.engines.llama_engine import LlamaEngine

        tinyllama = get_model("tinyllama")

        if tinyllama is None:
            raise RuntimeError(
                "TinyLlama is not registered"
            )

        if not tinyllama.enabled:
            raise RuntimeError(
                "TinyLlama is disabled"
            )

        logger.info(
            "Lazily initializing local TinyLlama engine: %s",
            tinyllama.model_path,
        )

        self.llama_engine = LlamaEngine(
            tinyllama.model_path
        )

    def generate(
        self,
        model_name: str,
        prompt: str,
    ) -> GenerateResponse:

        model = get_model(model_name)

        if model is None:
            raise ValueError(
                f"Model '{model_name}' not found"
            )

        if not model.enabled:
            raise ValueError(
                f"Model '{model_name}' is disabled"
            )

        metrics_service.increment_requests()

        model_key = model_name.lower()

        if model_key == "tinyllama":

            logger.info(
                "Generating using local llama.cpp: %s",
                model.name,
            )

            self._initialize_tinyllama()

            generated_text = self.llama_engine.generate(
                prompt
            )

        elif model_key == "phi3":

            logger.info(
                "Generating using vLLM: %s",
                model.name,
            )

            generated_text = self.vllm_client.generate(
                prompt
            )

        else:
            raise ValueError(
                f"No inference engine configured for model '{model_name}'"
            )

        return GenerateResponse(
            model=model.name,
            response=generated_text,
            status="success",
        )


generate_service = GenerateService()
