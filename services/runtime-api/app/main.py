from fastapi import FastAPI

from app.routers import health

app = FastAPI(
    title="Enterprise AI Platform Runtime API",
    version="0.1.0",
    description="Production-grade Runtime API for Enterprise AI Platform",
)

app.include_router(health.router)

@app.get("/", tags=["Home"])
def root():
    return {
        "message": "Welcome to Enterprise AI Platform Runtime API"
    }