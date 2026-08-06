from pathlib import Path

from llama_cpp import Llama


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

        print(f"Loading model from: {model_path}")

        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=2048,
            verbose=False,
        )

        print(f"Model loaded successfully: {model_path.name}")

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