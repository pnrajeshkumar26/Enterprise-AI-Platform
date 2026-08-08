from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

@dataclass
class ModelInfo:
    name: str
    provider: str
    model_path: str
    quantization: str
    context_length: int
    enabled: bool

MODEL_REGISTRY = {

   "tinyllama": ModelInfo(
    name="TinyLlama",
    provider="HuggingFace",
    model_path=str(
        PROJECT_ROOT
        / "models"
        / "TinyLlama"
        / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    ),
    quantization="Q4_K_M",
    context_length=2048,
    enabled=True,
),

    "phi3": ModelInfo(
        name="Phi-3 Mini",
        provider="Microsoft",
        model_path="microsoft/Phi-3-mini-4k-instruct",
        quantization="Q4_K_M",
        context_length=4096,
        enabled=True,
    ),

    "gemma": ModelInfo(
        name="Gemma 2B",
        provider="Google",
        model_path="google/gemma-2b",
        quantization="Q4_K_M",
        context_length=8192,
        enabled=False,
    ),
}

def get_model(model_name: str):
    return MODEL_REGISTRY.get(model_name.lower())


def list_models():
    return list(MODEL_REGISTRY.values())