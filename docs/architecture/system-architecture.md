# System Architecture

## Purpose

The platform is designed around a stable application-facing Runtime API that separates client/UI behavior from the implementation details of individual LLM inference backends.

## High-level design

```text
Browser
  |
  v
Streamlit
  |
  v
Runtime API
  |
  +--> Model Registry
  |
  +--> Model Router
  |
  +--> Backend Clients
  |       |
  |       +--> TinyLlama / llama.cpp
  |       |
  |       +--> Phi-3 / vLLM
  |
  +--> Prometheus instrumentation

GPU layer
  |
  +--> NVIDIA Tesla T4
  |
  +--> DCGM Exporter
  |
  +--> Prometheus
  |
  +--> Grafana
```

## Design principles

### Stable API boundary

Clients call one Runtime API instead of knowing whether a request was served by llama.cpp or vLLM.

### Explicit routing

`auto` routing is deterministic and explainable. Manual model selection remains available for controlled diagnostics.

### Backend isolation

Inference-specific behavior lives in backend services/clients, keeping orchestration separate from model execution.

### Observability as a platform capability

Metrics are generated at the Runtime API and GPU layers and collected centrally by Prometheus.

### Service-name networking

Docker service names are used for internal communication instead of hard-coded container IP addresses.

## Current deployment boundary

The validated Docker-based runtime is the primary reference path. Kubernetes work exists in the broader learning journey, but this public README should not imply that the Docker deployment is an EKS production deployment.
