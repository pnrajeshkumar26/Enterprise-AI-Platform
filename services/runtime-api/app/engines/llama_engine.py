from pathlib import Path

from llama_cpp import Llama


class LlamaEngine:
    """Enterprise wrapper around llama.cpp."""

    def __init__(self):
        project_root = Path(__file__).resolve().parents[4]

        model_path = (
            project_root
            / "models"
            / "TinyLlama"
            / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        )

        print(f"Loading model from: {model_path}")

        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=2048,
            verbose=False,
        )

        print("TinyLlama loaded successfully.")

    def generate(self, prompt: str) -> str:
        response = self.llm(
            prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.95,
            stop=["</s>"],
        )

        return response["choices"][0]["text"].strip()