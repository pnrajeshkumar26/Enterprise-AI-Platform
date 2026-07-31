from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": "runtime-api",
        "version": "0.1.0",
        "environment": "development"
    }