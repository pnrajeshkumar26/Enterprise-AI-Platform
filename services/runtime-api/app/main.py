import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.core.config import settings
from app.routers import generate, health, metrics, models
from app.routers.runtime import router as runtime_router
from app.routers.metrics import prometheus_app

from app.observability.tracing import (
    initialize_tracing,
    instrument_fastapi_app,
)

tracer_provider = initialize_tracing()

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s %(levelname)s %(name)s "
        "trace_id=%(otelTraceID)s "
        "span_id=%(otelSpanID)s "
        "service=%(otelServiceName)s %(message)s"
    ),
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Runtime API for Enterprise AI Platform",
)

def _safe_route_template(request: Request) -> str:
    """Return the route template, never a user-supplied path value."""

    route = request.scope.get("route")
    route_path = getattr(route, "path", None)

    return route_path if isinstance(route_path, str) else "unmatched"


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    # Avoid logging frequent Prometheus scrapes.
    if request.url.path.rstrip("/") == "/metrics":
        return await call_next(request)

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            "http_request_failed method=%s route=%s "
            "status_code=500 error_type=%s",
            request.method,
            _safe_route_template(request),
            type(exc).__name__,
        )
        raise

    logger.info(
        "http_request_completed method=%s route=%s status_code=%s",
        request.method,
        _safe_route_template(request),
        response.status_code,
    )

    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.warning("Request validation failed error_count=%s", len(exc.errors()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "details": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    logger.warning("HTTP exception response status_code=%s", exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    logger.warning("Value error response error_type=ValueError")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": str(exc)},
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(_: Request, exc: FileNotFoundError):
    logger.warning("Resource not found error_type=FileNotFoundError")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.error("Unhandled exception response status_code=500")
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

instrument_fastapi_app(app, tracer_provider)