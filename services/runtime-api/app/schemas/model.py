from pydantic import BaseModel


class ModelResponse(BaseModel):
    name: str
    provider: str
    model_path: str
    quantization: str
    context_length: int
    enabled: bool