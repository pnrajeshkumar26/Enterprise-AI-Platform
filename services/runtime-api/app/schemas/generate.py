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


class RoutingScoreBreakdown(BaseModel):
    """Explainable score contributions for one routed model."""

    base_preference: float
    capacity: float
    latency: float
    gpu_pressure: float
    total: float


class RoutingExplanation(BaseModel):
    """Explainable routing decision exposed by the API."""

    selected_model: str
    reason: str
    scores: dict[str, float] = Field(default_factory=dict)
    breakdown: dict[str, RoutingScoreBreakdown] = Field(
        default_factory=dict,
    )


class GenerateResponse(BaseModel):
    """Response payload for text generation."""

    model: str
    response: str
    status: str
    routing: RoutingExplanation | None = None
