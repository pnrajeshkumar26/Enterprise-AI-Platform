from app.models.model_registry import get_model
from app.schemas.generate import GenerateResponse


class GenerateService:
    """Business logic for text generation."""

    def generate(self, model_name: str, prompt: str) -> GenerateResponse:
        model = get_model(model_name)

        if model is None:
            raise ValueError(f"Model '{model_name}' not found")

        # Mock inference response
        generated_text = (
            f"This is a simulated response from {model.name} "
            f"for prompt: '{prompt}'"
        )

        return GenerateResponse(
            model=model.name,
            response=generated_text,
            status="success",
        )


generate_service = GenerateService()