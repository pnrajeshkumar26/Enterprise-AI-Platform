# Enterprise AI Platform â€” Practical LLMOps Reference Architecture

[![CI](https://github.com/pnrajeshkumar26/Enterprise-AI-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/pnrajeshkumar26/Enterprise-AI-Platform/actions/workflows/ci.yml)

> **A hands-on LLMOps engineering project demonstrating model routing, GPU inference, containerized serving, observability, reliability, and response-quality guardrails.**

This repository documents and implements an evolving **Enterprise AI / LLMOps reference platform** built as a practical learning and portfolio project.

The goal is to explore the engineering problems around operating LLM inference systemsâ€”not just calling a model API:

- How should requests be routed to different models?
- How do inference backends remain isolated behind a stable API?
- How do we monitor request volume, latency, failures, routing and GPU health?
- How do we recover the platform after container or EC2 restarts?
- How do we reduce known model-quality failures without pretending an LLM is always factual?
- How do we turn experimentation into reproducible deployment and CI workflows?

## Why this project is useful

For **AI engineers, MLOps/LLMOps learners, platform engineers, recruiters and hiring managers**, this repository provides a concrete example of the journey from model serving to operational observability.

The implementation currently focuses on a constrained GPU environment and uses a deliberately small set of technologies so the end-to-end system can be understood and troubleshot rather than hidden behind managed services.

## Current platform

| Layer | Technology | Role |
|---|---|---|
| UI | Streamlit | Interactive inference client |
| API | FastAPI | Runtime orchestration layer |
| Routing | Python ModelRouter | Deterministic request classification and model selection |
| Lightweight inference | TinyLlama + llama.cpp | Lower-complexity workload path |
| Higher-capability inference | Phi-3 + vLLM | Technical/complex workload path |
| GPU | NVIDIA Tesla T4 | Shared inference accelerator |
| Metrics | Prometheus | Time-series metrics collection |
| GPU telemetry | NVIDIA DCGM Exporter | GPU utilization and memory metrics |
| Visualization | Grafana | Dashboards and alerting |
| Packaging | Docker / Docker Compose | Service isolation and lifecycle |
| Testing | pytest | Unit/integration-oriented validation |
| CI/CD | GitHub Actions | Automated repository validation and delivery workflow |

## Architecture

```text
                                      Browser
                                         |
                           +-------------+-------------+
                           |                           |
                           v                           v
                    Streamlit :8501              Grafana :3000
                           |                           |
                           | Docker network           |
                           v                           v
                    Runtime API :8000 ----------> Prometheus :9090*
                           |
                     +-----+------+
                     |            |
                     v            v
                TinyLlama       Phi-3
                llama.cpp       vLLM
                     |            |
                     +-----+------+
                           |
                           v
                       Tesla T4
                           ^
                           |
                    DCGM Exporter :9400*

* Prometheus and DCGM host ports are localhost-restricted.
```

### Request flow

```text
User prompt
    |
    v
Streamlit
    |
    v
Runtime API
    |
    v
Model Router
    |
    +---- simple/casual ----------> TinyLlama / llama.cpp
    |
    +---- technical/complex ------> Phi-3 / vLLM
                                      |
                                      v
                               Response Quality Guard
                                      |
                                +-----+-----+
                                |           |
                              valid     known contradiction
                                |           |
                                v           v
                             response   one corrective retry
```

### Observability flow

```text
Runtime API metrics ------------------+
                                     |
DCGM GPU metrics --------------------+--> Prometheus --> Grafana --> Alerts
                                     |
Prometheus self-metrics -------------+
```

## LLMOps capabilities demonstrated

### 1. Intelligent model routing

The `auto` route uses a deterministic score based on request characteristics such as technical indicators, complexity language, prompt length and multi-step structure.

Current high-level behavior:

```text
score < 3  -> TinyLlama
score >= 3 -> Phi-3
```

Manual model selection remains available for controlled testing.

The router is intentionally deterministic so behavior is testable and explainable. It can later evolve toward routing based on latency, cost, GPU pressure, model availability or workload classification.

### 2. Multiple inference backends

The Runtime API hides backend-specific details behind one generation endpoint.

- **TinyLlama** is served through `llama.cpp` for lightweight requests.
- **Phi-3** is served through vLLM's OpenAI-compatible chat-completions interface for more technical/complex workloads.

The architecture therefore separates application orchestration from inference implementation.

### 3. Prometheus metrics

The Runtime API exposes a Prometheus-native endpoint at `/metrics/` and instruments areas including:

- request count
- request status
- selected model
- routing decisions
- generation latency
- generation failures
- backend availability
- configured model count
- runtime health

### 4. GPU observability

NVIDIA DCGM Exporter publishes GPU metrics into Prometheus, including framebuffer memory and GPU utilization.

This allows infrastructure signals to be correlated with application behavior instead of troubleshooting inference from logs alone.

### 5. Grafana dashboards and alerts

The repository contains a provisioned LLMOps dashboard and five operational alert rules covering:

1. Runtime API availability
2. DCGM exporter availability
3. LLM generation failure rate
4. LLM P95 latency
5. GPU framebuffer memory pressure

Alert rules are maintained as configuration files so the observability layer can be reproduced rather than manually rebuilt in the UI.

### 6. Response-quality guardrails

The project encountered a real model-quality issue during observability validation: the model could confidently invent technical definitions.

The response path therefore adds:

- a compact verified enterprise context
- conservative generation parameters
- a narrow deterministic terminology guard
- at most one corrective regeneration for known platform-critical contradictions

This is **not** a general hallucination detector. It is intentionally limited and documented as such.

### 7. Containerized Streamlit frontend

The Streamlit frontend is containerized and uses Docker service discovery to reach the Runtime API:

```text
RUNTIME_API_URL=http://enterprise-runtime-api:8000
```

The container uses `restart: unless-stopped` and a health check so the frontend automatically recovers with the Docker workload after a host restart.

This removes the previous dependency on manually launching Streamlit from an interactive shell after EC2 restart/session expiry.

## Observability implementation

The main observability configuration is under:

```text
deployment/observability/
â”œâ”€â”€ prometheus/
â”‚   â”œâ”€â”€ docker-compose.yml
â”‚   â””â”€â”€ prometheus.yml
â””â”€â”€ grafana/
    â”œâ”€â”€ docker-compose.yml
    â”œâ”€â”€ dashboards/
    â”‚   â””â”€â”€ enterprise-ai-llmops.json
    â””â”€â”€ provisioning/
        â”œâ”€â”€ alerting/
        â”œâ”€â”€ dashboards/
        â””â”€â”€ datasources/
```

The validated scrape jobs are:

```text
runtime-api
prometheus
dcgm
```

## Security and exposure model

The current development environment deliberately restricts the host exposure of the metrics endpoints:

```text
Prometheus  -> 127.0.0.1:9090
DCGM        -> 127.0.0.1:9400
```

The services continue communicating through the private Docker network using service names rather than container IP addresses.

This is a development/reference configuration, not a substitute for a production ingress, authentication, TLS, secret management or network policy design.

## Reliability and recovery

The containers use Docker restart policies and were validated through container restart and EC2 stop/start scenarios.

The intended recovery chain is:

```text
EC2 starts
   |
   v
Docker daemon
   |
   +--> Runtime API
   +--> Streamlit
   +--> TinyLlama
   +--> vLLM
   +--> Prometheus
   +--> DCGM Exporter
   +--> Grafana
```

The Streamlit frontend specifically no longer requires a manual `streamlit run` command after host recovery.

## Testing

The current local suite reached:

```text
13 passed
```

Run it with:

```bash
PYTHONPATH=services/runtime-api python -m pytest -q
```

The repository also contains GitHub Actions workflow validation.

## Repository structure

```text
.
â”œâ”€â”€ frontend/                       # Streamlit application
â”œâ”€â”€ services/
â”‚   â”œâ”€â”€ runtime-api/                # FastAPI orchestration service
â”‚   â””â”€â”€ tinyllama/                  # llama.cpp TinyLlama backend
â”œâ”€â”€ deployment/
â”‚   â”œâ”€â”€ frontend/                   # Streamlit Compose deployment
â”‚   â””â”€â”€ observability/              # Prometheus, Grafana and DCGM config
â”œâ”€â”€ tests/                           # Automated tests
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ architecture/              # System and observability architecture
â”‚   â”œâ”€â”€ llmops/                    # Routing, metrics and quality guardrails
â”‚   â”œâ”€â”€ operations/                # Deployment and troubleshooting
â”‚   â””â”€â”€ interview/                 # Interview and learning notes
â”œâ”€â”€ .github/workflows/              # CI/CD workflows
â””â”€â”€ README.md
```

## Quick start

### 1. Clone

```bash
git clone https://github.com/pnrajeshkumar26/Enterprise-AI-Platform.git
cd Enterprise-AI-Platform
```

### 2. Review prerequisites

The validated reference environment uses:

- Linux
- Python 3.11 for the containerized frontend/runtime components
- Docker and Docker Compose
- NVIDIA GPU + NVIDIA Container Toolkit/runtime for GPU inference
- a GPU-capable host for TinyLlama/vLLM execution

### 3. Run the tests

```bash
PYTHONPATH=services/runtime-api python -m pytest -q
```

### 4. Start the deployment components

The repository keeps frontend and observability Compose definitions under `deployment/`. Review the environment variables and external Docker network assumptions before starting services.

The validated deployment uses the external network:

```text
enterprise-ai-net
```

### 5. Validate health

Typical local checks:

```bash
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8501/_stcore/health
curl -s http://127.0.0.1:9090/-/healthy
curl -s http://127.0.0.1:3000/api/health
```

## Operational documentation

| Document | Purpose |
|---|---|
| [System Architecture](docs/architecture/system-architecture.md) | End-to-end platform design |
| [Inference Architecture](docs/architecture/inference-architecture.md) | Runtime API, router, llama.cpp and vLLM |
| [Observability Architecture](docs/architecture/observability-architecture.md) | Prometheus, DCGM, Grafana and alerting |
| [Model Routing](docs/llmops/model-routing.md) | Routing rules and design decisions |
| [LLMOps Observability](docs/llmops/observability.md) | Metrics, dashboards and alert model |
| [Quality Guardrails](docs/llmops/quality-guardrails.md) | Grounding and bounded response validation |
| [Deployment](docs/operations/deployment.md) | Deployment and service startup |
| [Troubleshooting](docs/operations/troubleshooting.md) | Common failure isolation workflow |
| [Restart Recovery](docs/operations/restart-recovery.md) | EC2/container recovery validation |
| [Interview Notes](docs/interview-notes/llmops-interview-notes.md) | Interview questions and talking points |

## What this project does not claim

This repository is a **learning and portfolio reference implementation**, not a claim of production readiness.

The current validated work should not be described as:

- a production EKS deployment
- a production-scale inference service
- a multi-GPU benchmarked platform
- an SLA/SLO-backed service
- a generally hallucination-free LLM system

Future production hardening would require additional controls such as identity/authentication, TLS, secrets management, ingress/API gateway, infrastructure-as-code, centralized logging, distributed tracing, evaluation pipelines, capacity planning, model lifecycle management, security scanning and disaster recovery.

## Roadmap

### Near term

- Kubernetes-native application deployment
- stronger automated end-to-end smoke testing
- richer request/token/cost telemetry
- benchmark harness for latency, throughput and GPU pressure
- quality-guard metrics in Prometheus/Grafana

### Later

- RAG/grounded knowledge workflows
- advanced routing based on cost/latency/resource state
- production-grade security controls
- autoscaling
- model registry/lifecycle integration
- richer tracing and SLOs

## Portfolio milestone

The completed Sprint 13 observability milestone is tagged:

```text
sprint-13-llmops-observability
```

The corresponding commit is:

```text
7ad8840  Sprint 13 - Complete LLMOps observability
```

## Learning path

A useful way to explore the project is to follow the platform in this order:

```text
LLM inference
    â†“
Runtime API
    â†“
Model routing
    â†“
Containerization
    â†“
GPU operations
    â†“
Metrics
    â†“
Observability
    â†“
Alerting
    â†“
Quality guardrails
    â†“
CI/CD
    â†“
Kubernetes evolution
```

## About

This project is part of a hands-on journey into **LLMOps, MLOps, GenAI infrastructure, GPU inference, observability and AI platform engineering**.

The repository intentionally documents both successful implementation and troubleshooting lessons so it can be useful to people learning these areasâ€”not only to people reviewing the final code.

## Repository

https://github.com/pnrajeshkumar26/Enterprise-AI-Platform
