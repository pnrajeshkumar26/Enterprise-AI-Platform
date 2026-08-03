from fastapi import FastAPI

from app.core.config import settings
from app.routers import health
from app.routers import models
from app.routers import generate

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Runtime API for Enterprise AI Platform",
)

app.include_router(health.router)
app.include_router(models.router)
app.include_router(generate.router)


@app.get("/", tags=["Home"])
def root():
    return {
        "message": f"Welcome to {settings.app_name}"
    }