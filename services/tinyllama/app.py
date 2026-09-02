import logging
import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from llama_cpp import Llama


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tinyllama-service")


MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/models/TinyLlama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
)


app = FastAPI(
    title="TinyLlama Inference Service",
)


llm = None


class GenerateRequest(BaseModel):
    prompt: str


@app.on_event("startup")
def load_model():
    global llm

    path = Path(MODEL_PATH)

    if not path.is_file():
        raise FileNotFoundError(
            f"TinyLlama model not found: {path}"
        )

    logger.info(
        "Loading TinyLlama from %s",
        path,
    )

    llm = Llama(
        model_path=str(path),
        n_ctx=2048,
        n_gpu_layers=-1,
        verbose=False,
    )

    logger.info(
        "TinyLlama loaded successfully"
    )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "tinyllama",
        "model": "TinyLlama",
        "loaded": llm is not None,
    }


@app.post("/generate")
def generate(request: GenerateRequest):
    if llm is None:
        return {
            "status": "error",
            "error": "TinyLlama model is not loaded",
        }

    logger.info(
        "Generating response for prompt: %s",
        request.prompt[:120],
    )

    response = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise enterprise AI assistant. "
                    "Answer the user's question directly and clearly. "
                    "Provide factual information only when reasonably "
                    "confident. Do not invent facts, definitions, "
                    "products, people, or technical details. "
                    "If you are unsure, say that you are unsure. "
                    "Prefer a short, accurate answer."
                ),
            },
            {
                "role": "user",
                "content": request.prompt,
            },
        ],
        max_tokens=256,
        temperature=0.2,
        top_p=0.9,
        repeat_penalty=1.1,
    )

    text = (
        response["choices"][0]["message"]["content"]
        .strip()
    )

    usage = response.get("usage", {})

    prompt_tokens = int(
        usage.get("prompt_tokens", 0)
    )
    completion_tokens = int(
        usage.get("completion_tokens", 0)
    )
    total_tokens = int(
        usage.get(
            "total_tokens",
            prompt_tokens + completion_tokens,
        )
    )

    return {
        "status": "success",
        "model": "TinyLlama",
        "response": text,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
    }
