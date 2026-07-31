from fastapi import FastAPI

from app.core.config import settings
from app.routers import health

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Runtime API for Enterprise AI Platform",
)

app.include_router(health.router)


@app.get("/", tags=["Home"])
def root():
    return {
        "message": f"Welcome to {settings.app_name}"
    }