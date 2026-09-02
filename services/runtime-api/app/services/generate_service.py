import logging
import os
import time

import requests

from app.clients.vllm_client import VLLMClient
from app.core.config import settings
from app.core.generation_result import GenerationResult
from app.core.runtime_metrics import (
    LLM_BACKEND_UP,
    LLM_GENERATION_DURATION_SECONDS,
    LLM_GENERATION_FAILURES_TOTAL,
    LLM_INPUT_TOKENS_TOTAL,
    LLM_OUTPUT_TOKENS_TOTAL,
    LLM_REQUESTS_TOTAL,
    LLM_ROUTING_DECISIONS_TOTAL,
    LLM_TOKENS_TOTAL,
)
from app.gateway.gateway import llm_gateway
from app.models.model_registry import get_model
from app.quality.response_guard import response_guard
from app.schemas.generate import GenerateResponse

logger = logging.getLogger(__name__)


class GenerateService:
    """
    Runtime API generation service.

    Modes:
      tinyllama -> TinyLlama backend
      phi3      -> Phi-3/vLLM backend
      auto      -> LLM Gateway selects a backend

    Runtime API itself does not run llama.cpp.
    It orchestrates the GPU backend and calls the backend over HTTP.

    Prometheus instrumentation:
      - request count
      - routing decisions
      - generation failures
      - request latency
      - backend health
      - input/output/total token counts

    Quality protection:
      - Phi-3 responses pass through a narrow deterministic terminology
        guard.
      - At most one corrective regeneration is attempted.

    Gateway:
      - request context normalization
      - request ID generation
      - existing model-router decision
      - explainable routing metadata
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

    def _generate_tinyllama(
        self,
        prompt: str,
    ) -> GenerationResult:
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

            usage = data.get("usage") or {}

            input_tokens = int(
                usage.get("prompt_tokens", 0)
            )
            output_tokens = int(
                usage.get("completion_tokens", 0)
            )
            total_tokens = int(
                usage.get(
                    "total_tokens",
                    input_tokens + output_tokens,
                )
            )

            result = GenerationResult(
                text=data.get("response", "").strip(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )

            LLM_BACKEND_UP.labels(
                backend="tinyllama"
            ).set(1)

            return result

        except Exception:
            LLM_BACKEND_UP.labels(
                backend="tinyllama"
            ).set(0)
            raise

    def _generate_phi3(
        self,
        prompt: str,
    ) -> GenerationResult:
        try:
            result = self.vllm_client.generate(prompt)

            guard = response_guard.validate(result.text)

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

            retry_guard = response_guard.validate(result.text)

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

    @staticmethod
    def _record_token_metrics(
        selected_model: str,
        result: GenerationResult,
    ) -> None:
        LLM_INPUT_TOKENS_TOTAL.labels(
            selected_model=selected_model
        ).inc(result.input_tokens)

        LLM_OUTPUT_TOKENS_TOTAL.labels(
            selected_model=selected_model
        ).inc(result.output_tokens)

        LLM_TOKENS_TOTAL.labels(
            selected_model=selected_model
        ).inc(result.total_tokens)

        logger.info(
            "Token usage: model=%s input=%d output=%d total=%d",
            selected_model,
            result.input_tokens,
            result.output_tokens,
            result.total_tokens,
        )

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
            # Gateway routing
            # -------------------------------------------------------
            context = llm_gateway.create_context(
                requested_model=requested_model,
                prompt=prompt,
            )

            decision = llm_gateway.decide(context)
            selected_model = decision.selected_model

            if requested_model == "auto":
                LLM_ROUTING_DECISIONS_TOTAL.labels(
                    requested_model="auto",
                    selected_model=selected_model,
                ).inc()

                logger.info(
                    "GATEWAY routing: request_id=%s model=%s score=%s reason=%s",
                    decision.request_id,
                    selected_model,
                    decision.routing_score,
                    decision.routing_reason,
                )
            else:
                logger.info(
                    "GATEWAY explicit model: request_id=%s model=%s",
                    decision.request_id,
                    selected_model,
                )

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
                result = self._generate_tinyllama(
                    prompt
                )

            elif selected_model == "phi3":
                result = self._generate_phi3(
                    prompt
                )

            else:
                raise ValueError(
                    f"No inference engine configured for "
                    f"'{selected_model}'"
                )

            # -------------------------------------------------------
            # Token metrics
            # -------------------------------------------------------
            self._record_token_metrics(
                selected_model,
                result,
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
                "request_id=%s requested=%s selected=%s duration=%.3fs",
                decision.request_id,
                requested_model,
                selected_model,
                duration,
            )

            return GenerateResponse(
                model=model.name,
                response=result.text,
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
                "request_id=%s requested=%s selected=%s duration=%.3fs",
                (
                    decision.request_id
                    if "decision" in locals()
                    else "unavailable"
                ),
                requested_model,
                failure_model,
                duration,
            )

            raise


generate_service = GenerateService()
