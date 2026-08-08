# Sprint 7 – Docker Runtime API Troubleshooting Guide

## Objective

Containerize the Enterprise AI Platform Runtime API using Docker and verify that the API runs successfully inside a Docker container.

---

# Environment

| Component | Version |
|-----------|----------|
| OS | Windows 11 |
| Python | 3.11 |
| Docker Desktop | 27.4 |
| FastAPI | 0.140.13 |
| Runtime | Docker Desktop (Linux Container) |

---

# Issue 1 – Docker container exited immediately

## Symptom

```bash
docker ps
```

returned

```text
No running containers
```

Container exited immediately after starting.

---

## Root Cause

The application failed during startup.

Checking logs revealed:

```bash
docker logs runtime-api-container
```

---

# Issue 2 – ModuleNotFoundError: llama_cpp

## Error

```text
ModuleNotFoundError: No module named 'llama_cpp'
```

---

## Root Cause

The Runtime API imported

```
Generate Service
    ↓
LlamaEngine
    ↓
llama_cpp
```

The Docker image was intentionally built without the inference engine package.

Since FastAPI imports every module during startup, the application failed before serving any requests.

---

## Resolution

Refactored the Runtime API.

Removed:

```python
from app.engines import LlamaEngine
```

Replaced runtime inference with a temporary response:

```python
return GenerateResponse(
    model=model.name,
    response="Inference server integration will be added in Sprint 8.",
    status="success",
)
```

---

## Lesson Learned

The Runtime API should not directly depend on the inference engine.

A production architecture separates:

```
Runtime API
      ↓ HTTP
Inference Server
(TGI / Ollama / vLLM)
```

---

# Issue 3 – requirements.txt contained unnecessary packages

## Problem

The Docker image attempted to install

```
llama-cpp-python
```

which required lengthy native compilation.

---

## Resolution

Created

```
requirements-docker.txt
```

containing only Runtime API dependencies.

```
FastAPI
Uvicorn
Pydantic
python-dotenv
```

Inference packages were excluded.

---

## Lesson Learned

Production Docker images should contain only the dependencies required for the deployed service.

---

# Issue 4 – Docker build failed while compiling llama-cpp-python

## Error

```text
Building wheel for llama-cpp-python...

ERROR:
failed to receive status:
rpc error:
code = Unavailable
desc = error reading from server: EOF
```

---

## Root Cause

Docker Desktop lost connection while compiling a large native package.

This package is unnecessary for the Runtime API container.

---

## Resolution

Removed

```
llama-cpp-python
```

from the Docker build.

The Runtime API will communicate with an external inference server in Sprint 8.

---

# Issue 5 – Docker Desktop API Internal Server Error

## Error

```text
request returned Internal Server Error
```

---

## Root Cause

Docker Desktop daemon temporarily became unstable after long-running native compilation.

---

## Resolution

Restarted Docker Desktop.

Removed stale containers.

Removed stale images.

Rebuilt the Docker image.

---

# Issue 6 – IndexError while loading model registry

## Error

```python
PROJECT_ROOT = Path(__file__).resolve().parents[4]

IndexError: 4
```

---

## Root Cause

The local development directory structure differed from the Docker container structure.

Inside Docker:

```
/app
    app/
        models/
```

The code attempted to navigate beyond the available parent directories.

---

## Resolution

Modified the project path resolution logic to work correctly inside the Docker container.

---

# Final Result

Docker image successfully built.

```bash
docker build -t runtime-api:0.1 .
```

Container started successfully.

```bash
docker run -d \
--name runtime-api-container \
-p 8000:8000 \
runtime-api:0.1
```

Verification:

```bash
docker ps
```

Output:

```text
STATUS

Up
```

The Runtime API successfully runs inside a Docker container.

---

# Key LLM Ops Learning

This sprint demonstrates an important production principle:

```
Application Code
        ↓

Docker Image
        ↓

Docker Container
        ↓

Runtime API
        ↓ HTTP

Inference Server
(TGI / Ollama / vLLM)
```

The Runtime API is responsible for API management.

The Inference Server is responsible for model execution.

Keeping these components independent improves scalability, maintainability, deployment flexibility, and production reliability.

---

# Commands Used

Build image

```bash
docker build --no-cache -t runtime-api:0.1 .
```

Run container

```bash
docker run -d --name runtime-api-container -p 8000:8000 runtime-api:0.1
```

List running containers

```bash
docker ps
```

View logs

```bash
docker logs runtime-api-container
```

Remove container

```bash
docker rm -f runtime-api-container
```

Remove image

```bash
docker rmi runtime-api:0.1
```

---

# Sprint Status

| Task | Status |
|------|--------|
| Dockerfile Created | ✅ |
| Docker Ignore Configured | ✅ |
| Runtime Dependencies Separated | ✅ |
| Docker Image Built | ✅ |
| Runtime API Container Started | ✅ |
| Runtime API Running in Docker | ✅ |