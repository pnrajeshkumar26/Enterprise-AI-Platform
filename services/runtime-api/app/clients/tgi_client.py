import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class TGIClient:
    """
    Client responsible for communicating with the
    Hugging Face Text Generation Inference server.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.7,
    ) -> str:
        """
        Send a text-generation request to the TGI server.
        """

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
            },
        }

        logger.info("Sending generation request to TGI: %s", self.base_url)

        response = requests.post(
            f"{self.base_url}/generate",
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        generated_text = data.get("generated_text")

        if generated_text is None:
            logger.error("Unexpected TGI response: %s", data)
            raise ValueError("TGI response did not contain 'generated_text'")

        return generated_text