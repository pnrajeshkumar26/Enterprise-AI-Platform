from fastapi import APIRouter, HTTPException

from app.models.model_registry import (
    list_models,
    get_model,
)

router = APIRouter()


@router.get(
    "/models",
    tags=["Models"],
    summary="List Available Models",
)
def get_models():
    return list_models()


@router.get(
    "/models/{model_name}",
    tags=["Models"],
    summary="Get Model Details",
)
def get_model_details(model_name: str):

    model = get_model(model_name)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found",
        )

    return model