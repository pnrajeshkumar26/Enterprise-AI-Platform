import logging
import os
import time

import requests

from app.clients.vllm_client import VLLMClient
from app.core.config import settings
from app.core.runtime_metrics import (
    LLM_BACKEND_UP,
    LLM_GENERATION_DURATION_SECONDS,
    LLM_GENERATION_FAILURES_TOTAL,
    LLM_REQUESTS_TOTAL,
    LLM_ROUTING_DECISIONS_TOTAL,
)
from app.models.model_registry import get_model
from app.quality.response_guard import response_guard
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

    Prometheus instrumentation:
      - request count
      - routing decisions
      - generation failures
      - request latency
      - backend health

    Quality protection:
      - Phi-3 responses pass through a narrow deterministic terminology
        guard.
      - At most one corrective regeneration is attempted.
    """

    TINYLLAMA_URL = os.getenv(
        "TINYLLAMA_URL",
        "http://enterprise-tinyllama-gpu:8000",
    )

    VLLM_URL = os.getenv(
        "VLLM_URL",
        settings.vllm_url,
    )

    QUALITY_RETRY_SYSTEM_PROMPT = (
        "The previous answer contained an incorrect technical definition. "
        "Use these exact verified definitions: "
        "LLMOps means Large Language Model Operations. "
        "vLLM is an LLM inference and serving framework. "
        "llama.cpp is a C/C++ library for running LLMs. "
        "NVIDIA Tesla T4 has 16 GB of GDDR6 GPU memory. "
        "Do not invent alternative acronym expansions or technical facts. "
        "Answer the user's question directly and concisely."
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
        try:
            response = self.http.post(
                f"{self.TINYLLAMA_URL}/generate",
                json={"prompt": prompt},
                timeout=360,
            )

            if not response.ok:
                LLM_BACKEND_UP.labels(
                    backend="tinyllama"
                ).set(0)

                raise RuntimeError(
                    f"TinyLlama backend failed: "
                    f"{response.status_code} {response.text}"
                )

            data = response.json()

            if data.get("status") != "success":
                LLM_BACKEND_UP.labels(
                    backend="tinyllama"
                ).set(0)

                raise RuntimeError(
                    f"TinyLlama backend returned an error: {data}"
                )

            LLM_BACKEND_UP.labels(
                backend="tinyllama"
            ).set(1)

            return data.get("response", "")

        except Exception:
            LLM_BACKEND_UP.labels(
                backend="tinyllama"
            ).set(0)
            raise

    def _generate_phi3(self, prompt: str) -> str:
        try:
            result = self.vllm_client.generate(prompt)

            guard = response_guard.validate(result)

            if guard.valid:
                LLM_BACKEND_UP.labels(
                    backend="phi3"
                ).set(1)

                return result

            logger.warning(
                "Phi-3 response failed quality guard: %s; retrying once",
                guard.reason,
            )

            retry_prompt = (
                f"{self.QUALITY_RETRY_SYSTEM_PROMPT}\n\n"
                f"User question:\n{prompt}"
            )

            result = self.vllm_client.generate(
                retry_prompt,
                max_tokens=256,
                temperature=0.1,
            )

            retry_guard = response_guard.validate(result)

            if not retry_guard.valid:
                raise RuntimeError(
                    "Phi-3 response failed quality validation after retry: "
                    f"{retry_guard.reason}"
                )

            LLM_BACKEND_UP.labels(
                backend="phi3"
            ).set(1)

            return result

        except Exception:
            LLM_BACKEND_UP.labels(
                backend="phi3"
            ).set(0)
            raise

    def generate(
        self,
        model_name: str,
        prompt: str,
    ) -> GenerateResponse:

        requested_model = (
            model_name or "auto"
        ).lower().strip()

        selected_model = None
        start = time.perf_counter()

        try:
            # -------------------------------------------------------
            # Model routing
            # -------------------------------------------------------
            if requested_model == "auto":
                decision = model_router.route(prompt)
                selected_model = decision.selected_model

                LLM_ROUTING_DECISIONS_TOTAL.labels(
                    requested_model="auto",
                    selected_model=selected_model,
                ).inc()

                logger.info(
                    "AUTO routing: model=%s score=%s reason=%s",
                    selected_model,
                    decision.score,
                    decision.reason,
                )

            else:
                decision = None
                selected_model = requested_model

            # -------------------------------------------------------
            # Model validation
            # -------------------------------------------------------
            model = get_model(selected_model)

            if model is None:
                raise ValueError(
                    f"Model '{selected_model}' not found"
                )

            if not model.enabled:
                raise ValueError(
                    f"Model '{selected_model}' is disabled"
                )

            # -------------------------------------------------------
            # Inference
            # -------------------------------------------------------
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
                    f"No inference engine configured for "
                    f"'{selected_model}'"
                )

            # -------------------------------------------------------
            # Success metrics
            # -------------------------------------------------------
            duration = time.perf_counter() - start

            LLM_REQUESTS_TOTAL.labels(
                requested_model=requested_model,
                selected_model=selected_model,
                status="success",
            ).inc()

            LLM_GENERATION_DURATION_SECONDS.labels(
                selected_model=selected_model
            ).observe(duration)

            logger.info(
                "Generation completed: "
                "requested=%s selected=%s duration=%.3fs",
                requested_model,
                selected_model,
                duration,
            )

            return GenerateResponse(
                model=model.name,
                response=generated_text,
                status="success",
            )

        except Exception:
            # -------------------------------------------------------
            # Failure metrics
            # -------------------------------------------------------
            duration = time.perf_counter() - start

            failure_model = selected_model or requested_model

            LLM_REQUESTS_TOTAL.labels(
                requested_model=requested_model,
                selected_model=failure_model,
                status="failure",
            ).inc()

            LLM_GENERATION_FAILURES_TOTAL.labels(
                selected_model=failure_model
            ).inc()

            LLM_GENERATION_DURATION_SECONDS.labels(
                selected_model=failure_model
            ).observe(duration)

            logger.exception(
                "Generation failed: "
                "requested=%s selected=%s duration=%.3fs",
                requested_model,
                failure_model,
                duration,
            )

            raise


generate_service = GenerateService()
