# Runtime API

This service exposes the runtime endpoints for the Enterprise AI Platform. It provides model discovery, health checks, runtime status, metrics, and text generation using the configured llama.cpp engine.

## Structure

- app/main.py: FastAPI application entrypoint and global exception handlers.
- app/routers/: route definitions for health, models, generation, runtime, and metrics.
- app/services/: business logic separated from route handlers.
- app/engines/: runtime engine integrations.
- app/schemas/: request and response models.

## Run locally

```bash
cd services/runtime-api
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Key endpoints

- GET /health
- GET /models
- GET /models/{model_name}
- POST /generate
- GET /runtime/status
- GET /runtime/metrics

## Logging and error handling

The service uses structured logging via Python's logging module and centralized FastAPI exception handlers for validation and unexpected failures.
