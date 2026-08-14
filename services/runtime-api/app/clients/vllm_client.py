import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class VLLMClient:
    """
    Client for communicating with vLLM's OpenAI-compatible API.
    """

    def __init__(self, base_url: str, model_id: str):
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id

    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.7,
    ) -> str:

        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
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
