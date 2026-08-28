import logging
import os

import requests

from app.clients.vllm_client import VLLMClient
from app.core.config import settings
from app.models.model_registry import get_model
from app.routing.model_router import model_router
from app.schemas.generate import GenerateResponse

logger = logging.getLogger(__name__)


class GenerateService:
    """
    Runtime API generation service.

    Modes:
      tinyllama -> TinyLlama backend
      phi3      -> Phi-3/vLLM backend
      auto      -> ModelRouter selects a backend

    Runtime API itself does not run llama.cpp.
    It orchestrates the GPU backend and calls the backend over HTTP.
    """

    TINYLLAMA_URL = os.getenv(
        "TINYLLAMA_URL",
        "http://enterprise-tinyllama-gpu:8000",
    )

    VLLM_URL = os.getenv(
        "VLLM_URL",
        settings.vllm_url,
    )

    def __init__(self):
        self.vllm_client = VLLMClient(
            self.VLLM_URL,
            settings.vllm_model_id,
        )

        self.http = requests.Session()

        logger.info(
            "Runtime API initialized: tinyllama=%s vllm=%s",
            self.TINYLLAMA_URL,
            self.VLLM_URL,
        )

    def _generate_tinyllama(self, prompt: str) -> str:
        response = self.http.post(
            f"{self.TINYLLAMA_URL}/generate",
            json={"prompt": prompt},
            timeout=360,
        )

        if not response.ok:
            raise RuntimeError(
                f"TinyLlama backend failed: "
                f"{response.status_code} {response.text}"
            )

        data = response.json()

        if data.get("status") != "success":
            raise RuntimeError(
                f"TinyLlama backend returned an error: {data}"
            )

        return data.get("response", "")

    def _generate_phi3(self, prompt: str) -> str:
        return self.vllm_client.generate(prompt)

    def generate(
        self,
        model_name: str,
        prompt: str,
    ) -> GenerateResponse:

        requested_model = (
            model_name or "auto"
        ).lower().strip()

        if requested_model == "auto":
            decision = model_router.route(prompt)
            selected_model = decision.selected_model

            logger.info(
                "AUTO routing: model=%s score=%s reason=%s",
                selected_model,
                decision.score,
                decision.reason,
            )
        else:
            decision = None
            selected_model = requested_model

        model = get_model(selected_model)

        if model is None:
            raise ValueError(
                f"Model '{selected_model}' not found"
            )

        if not model.enabled:
            raise ValueError(
                f"Model '{selected_model}' is disabled"
            )

        if selected_model == "tinyllama":

            generated_text = self._generate_tinyllama(
                prompt
            )

        elif selected_model == "phi3":

            generated_text = self._generate_phi3(
                prompt
            )

        else:
            raise ValueError(
                f"No inference engine configured for '{selected_model}'"
            )

        logger.info(
            "Generation completed: requested=%s selected=%s",
            requested_model,
            selected_model,
        )

        return GenerateResponse(
            model=model.name,
            response=generated_text,
            status="success",
        )


generate_service = GenerateService()
