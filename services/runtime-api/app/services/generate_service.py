from app.engines import LlamaEngine
from app.models.model_registry import get_model
from app.schemas.generate import GenerateResponse


class GenerateService:
    """Business logic for text generation."""

    def __init__(self):
        pass

    def generate(self, model_name: str, prompt: str) -> GenerateResponse:
        model = get_model(model_name)

        if model is None:
            raise ValueError(f"Model '{model_name}' not found")

        # Create an engine using the selected model path
        engine = LlamaEngine(model["path"])

        generated_text = engine.generate(prompt)

        return GenerateResponse(
            model=model["name"],
            response=generated_text,
            status="success",
        )


generate_service = GenerateService()