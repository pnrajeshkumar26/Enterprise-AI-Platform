from app.engines import LlamaEngine
from app.models.model_registry import get_model
from app.schemas.generate import GenerateResponse


class GenerateService:
    """Business logic for text generation."""

    def __init__(self):
        pass

    def generate(self, model_name: str, prompt: str) -> GenerateResponse:
        # Fetch model metadata from the centralized registry
        model = get_model(model_name)

        print("MODEL =", model)
        print("TYPE =", type(model))

        if model is None:
            raise ValueError(f"Model '{model_name}' not found")

        # Create engine using the model path from the registry
        engine = LlamaEngine(model.model_path)

        # Generate text
        generated_text = engine.generate(prompt)

        # Build API response
        return GenerateResponse(
            model=model.name,
            response=generated_text,
            status="success",
        )


generate_service = GenerateService()