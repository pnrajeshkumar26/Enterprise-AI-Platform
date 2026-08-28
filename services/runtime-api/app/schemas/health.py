from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    inference_engine: str
    models_configured: int
    gpu_available: Optional[bool] = None
