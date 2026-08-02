# Genearte Request Schema   
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    model: str
    prompt: str