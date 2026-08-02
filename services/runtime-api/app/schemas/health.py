from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    inference_engine: str
    models_loaded: int
    gpu_available: bool