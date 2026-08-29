import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.core.config import settings
from app.routers import generate, health, metrics, models
from app.routers.runtime import router as runtime_router
from app.routers.metrics import prometheus_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Runtime API for Enterprise AI Platform",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "details": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    logger.warning("HTTP error %s: %s", exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    logger.warning("Value error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": str(exc)},
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(_: Request, exc: FileNotFoundError):
    logger.warning("Resource not found: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )

app.include_router(health.router)
app.include_router(models.router)
app.include_router(generate.router)
app.include_router(runtime_router)
app.include_router(metrics.router)
app.mount('/metrics', prometheus_app)


@app.get("/", tags=["Home"])
def root():
    return {
        "message": f"Welcome to {settings.app_name}"
    }