from pydantic import BaseModel


class GenerateRequest(BaseModel):
    """Request payload for text generation."""

    model: str
    prompt: str


class GenerateResponse(BaseModel):
    """Response payload for text generation."""

    model: str
    response: str
    status: str