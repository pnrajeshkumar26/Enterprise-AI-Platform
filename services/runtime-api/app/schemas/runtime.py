from pydantic import BaseModel


class RuntimeStatusResponse(BaseModel):
    status: str
    engine: str
    model: str
    provider: str
    quantization: str
    context_length: int
    cached: bool
    enabled: bool