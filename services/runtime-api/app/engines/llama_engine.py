import logging
from pathlib import Path

from llama_cpp import Llama

logger = logging.getLogger(__name__)


class LlamaEngine:
    """Enterprise wrapper around llama.cpp."""

    def __init__(self, model_path):
        """
        Initialize the Llama engine with the supplied GGUF model path.
        """

        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}"
            )

        logger.info("Loading model from: %s", model_path)

        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=2048,
            n_gpu_layers=-1,
            verbose=False,
        )

        logger.info("Model loaded successfully: %s", model_path.name)

    def generate(self, prompt: str) -> str:
        """
        Generate text using the loaded model.
        """

        response = self.llm(
            prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.95,
            stop=["</s>"],
        )

        return response["choices"][0]["text"].strip()