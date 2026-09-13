# Enterprise AI Platform & Practical LLMOps Reference Architecture

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
| Testing | pytest | Unit, integration and controlled E2E validation |
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

The `auto` route uses a deterministic multi-signal routing pipeline.

Pre-routing signals include:

- request characteristics and technical/factual indicators
- estimated input tokens
- requested output-token budget
- model context/token capacity
- historical latency
- shared GPU/resource pressure
- backend/model availability
- base router preference

The final decision combines these signals into explainable per-model scores.

Capacity is enforced before inference. If the preferred model cannot satisfy the requested token budget, the gateway can automatically select an alternate model when capacity is available. If neither configured model has sufficient capacity, the request is rejected rather than silently exceeding the model context.

Manual model selection remains available for controlled testing.

The router is intentionally deterministic so behavior is testable and explainable. Routing decisions expose score contributions for base preference, capacity, latency and GPU pressure.
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
           prometheus/
             docker-compose.yml
             prometheus.yml
           grafana/
             docker-compose.yml
             dashboards/
               enterprise-ai-llmops.json
           provisioning/
             alerting/
             dashboards/
             datasources/
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

The current local test suite reached:

```text
86 passed
5 integration tests passed
3 E2E tests skipped by default
```

Run it with:

```bash
PYTHONPATH=services/runtime-api pytest -q
```

The repository also contains GitHub Actions workflow validation.

## Repository structure

```text
.
frontend/                    # Streamlit application
services/
runtime-api/                # FastAPI orchestration service
tinyllama/                  # llama.cpp TinyLlama backend
deployment/
frontend/                   # Streamlit Compose deployment
observability/              # Prometheus, Grafana and DCGM config
tests/                      # Automated tests
docs/
architecture/              # System and observability architecture
llmops/                    # Routing, metrics and quality guardrails
operations/                # Deployment and troubleshooting
interview/                 # Interview and learning notes
.github/workflows/         # CI/CD workflows
README.md
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
PYTHONPATH=services/runtime-api pytest -q
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
| [Sprint 14 Final Implementation Notes](docs/llmops/Sprint14_Final_Implementation_Notes.md) | Complete Sprint 14 implementation, testing, recovery and operational reference |

## Sprint 14 LLMOps status

Sprint 14 extends the platform from basic observability into operational LLMOps capabilities.

Completed milestones:

```text
Stage 7  -> Explainable Routing
Stage 8  -> Gateway Prometheus Metrics
Stage 8A -> Streamlit Request Telemetry
Stage 9  -> Grafana LLMOps Dashboard
Stage 10 -> Unit / Integration / E2E Testing
Stage 11 -> Restart / Recovery
```

Current Runtime API deployment:

```text
deployment/runtime-api/docker-compose.yml
```

```yaml
image: enterprise-runtime-api:3.19
restart: unless-stopped
```

The Runtime API image version and deployment image reference must remain synchronized whenever a new image is created.

Stage 10 uses unit, integration and explicitly gated E2E testing.

```bash
PYTHONPATH=services/runtime-api pytest -q
```

Live E2E tests require explicit opt-in.

```bash
RUN_E2E=1 PYTHONPATH=services/runtime-api pytest -m e2e -q
```

During periods without active development, Docker workloads should be intentionally stopped to control GPU and runtime cost.

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

- Evaluation and benchmark framework
- RAG / grounded knowledge workflows
- Fine-tuning with SFT + LoRA + QLoRA
- agentic / tool-using AI workflows
- Kubernetes-native application deployment
- stronger CI/CD and automated end-to-end validation
- quality / guardrail metrics with Prometheus and Grafana
- richer tracing, evaluation metrics and SLOs

### Later

- production-grade security, PII and safety controls
- model registry and model lifecycle management
- autoscaling and inference optimization
- advanced adaptive routing using quality / cost / latency / resource signals
- multimodal AI workflows
- enterprise RAG optimization with hybrid search and reranking

## Current portfolio milestone

Sprint 14 has extended the platform from observability into intelligent LLMOps operations.

Completed milestones:

```text
Stage 7  -> Explainable Routing
Stage 8  -> Gateway Prometheus Metrics
Stage 8A -> Streamlit Request Telemetry
Stage 9  -> Grafana LLMOps Dashboard
Stage 10 -> Unit / Integration / E2E Testing
Stage 11 -> Restart / Recovery
```

Current checkpoint:

```text
sprint-14-stage-11-restart-recovery
```

Stage 12 documentation and Stage 13 final release checkpoint are included in the final Sprint 14 release sequence.

## Learning path

A useful way to explore the project is to follow the platform in this order:

```text
LLM inference
    †
Runtime API
    +
Model routing
    †
Containerization
    †
GPU operations
    †
Metrics
    †
Observability
    †
Alerting
    †
Quality guardrails
    †
CI/CD
    †
Kubernetes evolution
```

## About

This project is part of a hands-on journey into **LLMOps, MLOps, GenAI infrastructure, GPU inference, observability and AI platform engineering**.

The repository intentionally documents both successful implementation and troubleshooting lessons so it can be useful to people learning these areasâ€”not only to people reviewing the final code.

## Repository

https://github.com/pnrajeshkumar26/Enterprise-AI-Platform
