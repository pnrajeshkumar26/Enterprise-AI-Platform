from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODELS = {
    "TinyLlama": {
        "name": "TinyLlama",
        "path": PROJECT_ROOT / "models" / "TinyLlama" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "description": "TinyLlama 1.1B Chat",
        "quantization": "Q4_K_M",
    }
}

def get_model(model_name: str):
    return MODELS.get(model_name)