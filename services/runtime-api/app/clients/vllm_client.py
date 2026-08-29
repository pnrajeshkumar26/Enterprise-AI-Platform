import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class VLLMClient:
    """
    Client for communicating with vLLM's OpenAI-compatible API.

    The client applies a compact verified enterprise context for the
    platform's core technologies to reduce terminology hallucination.
    """

    SYSTEM_PROMPT = (
        "You are an enterprise AI assistant focused on accurate, "
        "technical, and factual answers. "
        "Answer the user's question directly and clearly. "
        "Use standard, well-established terminology. "
        "Do not invent acronym expansions, product definitions, "
        "software capabilities, hardware specifications, or technical facts. "
        "Do not present guesses as facts. "
        "When a detail is uncertain, say so briefly instead of guessing. "
        "For technical questions, prefer concise structured explanations."
    )

    ENTERPRISE_CONTEXT = (
        "Verified terminology for this platform: "
        "LLMOps means Large Language Model Operations. "
        "vLLM is an LLM inference and serving framework. "
        "llama.cpp is a C/C++ library for running LLMs. "
        "Prometheus is a metrics and time-series monitoring system. "
        "Grafana is an observability and visualization platform. "
        "Kubernetes is an open-source container orchestration platform. "
        "NVIDIA Tesla T4 has 16 GB of GDDR6 GPU memory. "
        "Use these definitions when these technologies are discussed. "
        "Do not redefine them differently."
    )

    def __init__(self, base_url: str, model_id: str):
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.2,
    ) -> str:

        system_prompt = (
            f"{self.SYSTEM_PROMPT} "
            f"{self.ENTERPRISE_CONTEXT}"
        )

        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
        }

        logger.info(
            "Sending generation request to vLLM: %s",
            self.base_url,
        )

        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Unexpected vLLM response: %s", data)
            raise ValueError(
                "vLLM response did not contain a valid completion"
            ) from exc
