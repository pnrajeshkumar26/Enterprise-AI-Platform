from fastapi import APIRouter, HTTPException

from app.schemas.generate import (
    GenerateRequest,
    GenerateResponse,
)
from app.services.generate_service import generate_service

router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerateResponse,
    tags=["Generation"],
    summary="Generate Text",
)
def generate(request: GenerateRequest):
    try:
        return generate_service.generate(
            request.model,
            request.prompt,
            request.max_output_tokens,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )