from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request payload for text generation."""

    model: str
    prompt: str
    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Maximum number of tokens the selected model may generate. "
            "When omitted, the gateway uses the model-specific default."
        ),
    )


class GenerateResponse(BaseModel):
    """Response payload for text generation."""

    model: str
    response: str
    status: str
