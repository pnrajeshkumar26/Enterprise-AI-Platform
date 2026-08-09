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
    ) -> str:

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens
            }
        }

        logger.info("Sending request to TGI")

        response = requests.post(
            f"{self.base_url}/generate",
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        return data["generated_text"]