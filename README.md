# Enterprise AI Platform & Practical LLMOps Reference Architecture

[![CI](https://github.com/pnrajeshkumar26/Enterprise-AI-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/pnrajeshkumar26/Enterprise-AI-Platform/actions/workflows/ci.yml)

> **A hands-on Enterprise AI / LLMOps engineering project demonstrating deterministic multi-signal model routing, GPU inference, containerized model serving, request/token/cost telemetry, Prometheus/Grafana observability, response-quality guardrails, LLM-as-a-Judge evaluation, model benchmarking, evaluation observability, automated testing, restart/recovery, and CI/CD quality gates.**

This repository documents and implements an evolving **Enterprise AI / LLMOps reference platform** built as a practical engineering, learning, and portfolio project.

The goal is to explore the engineering challenges involved in operating LLM inference systems end to end — not simply calling a model API.

The project addresses questions such as:

- How should requests be routed across multiple models using deterministic signals?
- How can different inference backends remain isolated behind a stable runtime API?
- How can request volume, latency, failures, token usage, estimated inference cost, routing decisions and GPU health be measured?
- How can the platform recover predictably after container or host restarts?
- How can known model-quality failure patterns be reduced with bounded runtime guardrails without claiming that an LLM is always factual?
- How can LLM responses be evaluated systematically instead of treating model output as ground truth?
- How can **LLM-as-a-Judge** be combined with deterministic metrics and a defined scoring rubric?
- How can candidate models be benchmarked using a versioned evaluation dataset?
- How can evaluation results be exposed through Prometheus/Grafana and used as a CI/CD quality gate?
- How can experimentation be converted into reproducible, testable and operational LLMOps workflows?

## Why this project is useful

For **AI/ML engineers, LLMOps and MLOps learners, platform engineers, DevOps engineers, recruiters and hiring managers**, this repository provides a concrete example of how an AI platform can evolve from model serving into a broader **LLMOps engineering lifecycle**.

The implementation intentionally focuses on a constrained GPU environment and a relatively small technology stack so that the end-to-end system can be understood, measured, tested and troubleshot rather than hidden behind managed services.

The platform demonstrates the progression:

```text
LLM Inference
    ->
Model Serving
    ->
Runtime API
    ->
Intelligent Model Routing
    ->
GPU Operations
    ->
Token / Cost Telemetry
    ->
Prometheus / Grafana Observability
    ->
Response-Quality Guardrails
    ->
LLM Evaluation
    ->
LLM-as-a-Judge
    ->
Model Benchmarking
    ->
Evaluation Observability
    ->
CI/CD Quality Gate
```

## Current platform

| Layer | Technology | Role |
|---|---|---|
| UI | Streamlit | Interactive inference client and explicit evaluation flow |
| API | FastAPI | Stable runtime orchestration layer |
| Routing | Python ModelRouter | Deterministic multi-signal model selection |
| Lightweight inference | TinyLlama + llama.cpp | Lower-complexity workload path |
| Higher-capability inference | Phi-3 Mini + vLLM | Technical/complex workload path |
| Evaluation Judge | Qwen/Qwen2.5-1.5B-Instruct | Dedicated offline LLM-as-a-Judge |
| Evaluation dataset | JSONL v1.0 | Versioned evaluation cases and criteria |
| Evaluation metrics | Python + prometheus-client | Evaluation score, pass rate, latency, cases and token metrics |
| GPU | NVIDIA Tesla T4 | Shared inference accelerator |
| GPU telemetry | NVIDIA DCGM Exporter | GPU utilization and resource telemetry |
| Metrics | Prometheus | Runtime, GPU and evaluation metrics collection |
| Visualization | Grafana | LLMOps, GPU and evaluation dashboards |
| Packaging | Docker / Docker Compose | Service isolation and lifecycle management |
| Testing | pytest | Unit, integration, evaluation and controlled E2E validation |
| CI/CD | GitHub Actions | Repository validation, image delivery and evaluation quality gate |

## Architecture

The platform separates **online inference operations** from **offline evaluation and quality engineering**.

```text
                                      ENTERPRISE AI PLATFORM
                                              |
                 +----------------------------+----------------------------+
                 |                            |                            |
                 v                            v                            v
           User / Browser              Observability                  Evaluation
                 |                            |                            |
                 v                            |                            v
          Streamlit :8501                    |                  Evaluation Dataset
                 |                            |                            |
                 v                            |                            v
         Runtime API :8001                   |                 Evaluation Runner
                 |                            |                            |
      +----------+-----------+                |                            v
      |                      |                |                   Candidate Responses
      v                      v                |                            |
Request validation    Model Router            |                            v
      |                      |                |                    Qwen Judge Model
      |          +-----------+                |                     (offline judge)
      |          |                            |                            |
      v          v                            +-------------+--------------+
  Capacity   Routing                                      |
  checks     decision                                     v
      |          |                                Evaluation Results
      |          +-----> TinyLlama / llama.cpp            |
      |          |                                        v
      |          +-----> Phi-3 / vLLM             Prometheus / Grafana
      |                        |
      |                        v
      +-------------------- Tesla T4

Runtime API ---------------------> Prometheus :9090
DCGM Exporter :9400 ------------> Prometheus
Evaluation Exporter :9108 -------> Prometheus
Prometheus ----------------------> Grafana :3000
```

### Online inference architecture

```text
Browser
   |
   v
Streamlit
   |
   v
Runtime API
   |
   +--> Request validation
   +--> Token estimation / capacity checks
   +--> Deterministic multi-signal router
   +--> TinyLlama / llama.cpp
   +--> Phi-3 / vLLM
   +--> Response-quality guard
   +--> Request / token / latency / cost telemetry
   |
   v
Response
```

### Offline evaluation architecture

```text
Versioned Evaluation Dataset
          |
          v
   Evaluation Runner
          |
          v
   Candidate Model
          |
          v
   Candidate Response
          |
          +-----------------------+
          |                       |
          v                       v
Deterministic Metrics       LLM-as-a-Judge
                                  |
                                  v
                    Qwen/Qwen2.5-1.5B-Instruct
                                  |
                                  v
                       Structured Evaluation Result
                                  |
                                  v
                      Benchmark / Evaluation Report
                                  |
                                  v
                     Prometheus / Grafana + Quality Gate
```

The evaluation judge is deliberately separated from the runtime routing candidates. **Qwen/Qwen2.5-1.5B-Instruct is the dedicated evaluation judge**, while TinyLlama and Phi-3 remain candidate generation models.

## Request flow

```text
User prompt
    |
    v
Streamlit
    |
    v
Runtime API
    |
    +--> Validate request
    |
    +--> Estimate token requirements
    |
    +--> Check model context / capacity
    |
    +--> Evaluate routing signals
    |       |
    |       +--> request characteristics
    |       +--> token requirements
    |       +--> latency
    |       +--> GPU / resource pressure
    |       +--> backend availability
    |       +--> model capacity
    |       +--> base router preference
    |
    +--> Calculate explainable model scores
    |
    +-----> TinyLlama / llama.cpp
    |
    +-----> Phi-3 / vLLM
    |
    +--> Response-quality guard
    |       |
    |       +--> accept response
    |       |
    |       +--> one bounded corrective retry for configured contradictions
    |
    +--> Record request, token, latency and estimated cost telemetry
    |
    v
Response to user
```

### Explicit evaluation flow

Evaluation is an explicit offline or controlled activity. The judge is not placed on the synchronous `/generate` hot path.

```text
Evaluation Case
     |
     v
Candidate Model
     |
     v
Generated Response
     |
     +--> Deterministic metrics
     |
     +--> LLM-as-a-Judge
     |       |
     |       v
     |   Qwen Judge
     |
     v
Weighted Evaluation Score
     |
     +--> PASS
     |
     +--> FAIL
```

## Observability flow

The platform has separate observability paths for **runtime operations, infrastructure telemetry and evaluation quality**.

### Runtime observability

```text
Runtime API
    |
    +--> request / status metrics
    +--> routing outcomes and scores
    +--> input / output / total token metrics
    +--> latency and failure metrics
    +--> estimated cost metrics
    |
    v
Prometheus :9090
    |
    v
Grafana :3000
```

### GPU observability

```text
DCGM Exporter :9400
        |
        v
Prometheus
        |
        v
Grafana GPU / resource views
```

### Evaluation observability

```text
Evaluation Runner
        |
        v
model_benchmark.json
        |
        v
Evaluation Metrics Exporter :9108
        |
        v
Prometheus
        |
        v
Grafana Evaluation Panels
```

Evaluation metrics currently include:

```text
evaluation_score
evaluation_pass_rate
evaluation_generation_latency_seconds
evaluation_cases_total
evaluation_generation_tokens_total
```

## LLMOps capabilities demonstrated

### 1. Deterministic intelligent model routing

The `auto` route uses a deterministic multi-signal routing pipeline.

Signals include:

- request characteristics and technical/factual indicators
- estimated input tokens
- requested output-token budget
- model context/token capacity
- historical latency
- shared GPU/resource pressure
- backend/model availability
- base router preference

The router produces explainable per-model scores.

Capacity is checked before inference. When the preferred model cannot satisfy the requested token budget, the platform can select an alternate configured model when capacity is available. If neither configured model can safely satisfy the request, the request is rejected instead of silently exceeding model capacity.

Manual model selection remains available for controlled testing.

### 2. Multiple inference backends

The Runtime API provides one stable generation interface over multiple inference implementations:

- **TinyLlama** through `llama.cpp`
- **Phi-3 Mini** through vLLM's OpenAI-compatible API

This separates application orchestration from backend-specific inference implementation.

### 3. Request, token and cost telemetry

The runtime records operational signals including:

- request volume
- request status
- selected model
- input tokens
- output tokens
- total tokens
- generation latency
- generation failures
- routing decisions
- estimated self-hosted inference cost

### 4. GPU observability

NVIDIA DCGM Exporter feeds GPU telemetry into Prometheus, allowing application behavior to be correlated with infrastructure signals such as:

- GPU utilization
- GPU memory usage
- framebuffer pressure
- GPU temperature
- GPU power/resource state

### 5. Prometheus and Grafana observability

The platform contains provisioned dashboards and operational alerting for runtime and infrastructure behavior.

The dashboard covers areas such as:

- runtime API health
- request rate
- latency
- routing outcomes
- routing scores and margins
- token throughput
- estimated inference cost
- GPU utilization and memory
- evaluation score
- evaluation pass rate
- evaluation latency
- evaluation case coverage

### 6. Response-quality guardrails

The project encountered a model-quality issue where a model could confidently invent technical definitions.

The runtime therefore uses bounded quality protection including:

- compact verified enterprise context
- conservative generation parameters
- deterministic terminology checks
- at most one corrective regeneration for configured contradictions

This is **not** a general hallucination detector and does not claim to guarantee factual correctness.

### 7. LLM evaluation and LLM-as-a-Judge

Phase 15 introduces a dedicated evaluation layer with a versioned **40-case dataset** spanning:

```text
Factual
Reasoning
Instruction Following
Explanation
Summarization
Safety
```

The rubric uses four dimensions:

```text
Correctness            40%
Relevance              25%
Completeness           20%
Instruction Following  15%
```

Scores use a 1–5 scale with an initial configurable pass threshold of **3.5**.

The dedicated evaluation judge is:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

The judge receives the evaluation inputs and candidate response and returns structured rubric scores with concise evidence.

Judge outputs are treated as **measurements rather than ground truth**. The repository includes a calibration framework, and the current calibration data is documented as provisional pending independent human annotation.

### 8. Model benchmarking

The initial POC benchmark evaluated 10 cases for each candidate generation model.

| Model | Cases | Average Score | Pass Rate | Avg Generation Latency |
|---|---:|---:|---:|---:|
| TinyLlama | 10 | 3.4 | 60% | 0.712 s |
| Phi-3 | 10 | 4.2 | 80% | 2.304 s |

This is a **small POC smoke benchmark**, not a statistically strong production evaluation. Its purpose is to validate the evaluation architecture, model-comparison workflow and quality-gate mechanics.

### 9. Evaluation observability

Evaluation results are exported separately from the Runtime API and exposed through Prometheus and Grafana so that quality can be viewed alongside latency, token usage and infrastructure telemetry.

The current Grafana dashboard includes dedicated evaluation panels for:

- evaluation score
- evaluation pass rate
- generation latency
- evaluated cases

### 10. CI/CD evaluation quality gate

Phase 15 adds a manually triggered GitHub Actions workflow for evaluation quality enforcement:

```text
.github/workflows/evaluation-quality-gate.yml
```

The workflow validates the evaluation test suite and checks a selected benchmark report against a configurable minimum score.

With the current benchmark:

```text
Phi-3
4.2 >= 3.5  -> PASS

TinyLlama
3.4 < 3.5   -> FAIL
```

Normal pull-request CI does not run live GPU inference or LLM evaluation. Expensive inference remains an explicit evaluation activity.

### 11. Automated testing and reproducibility

The repository includes:

- unit tests
- integration tests
- controlled E2E tests
- evaluation dataset validation
- deterministic metric tests
- judge parser tests
- vLLM judge client tests
- benchmark validation
- Prometheus evaluation metric tests
- quality-gate tests
- GitHub Actions CI validation

The current Phase 15 local regression baseline is:

```text
122 passed
3 skipped
2 warnings
```

The two warnings are existing Starlette deprecation warnings from the integration test environment.

### 12. Containerized operational recovery

The platform uses Docker service isolation and restart policies to support recovery after normal container restarts.

The project documents controlled restart recovery and distinguishes that from an unverified claim of full production disaster recovery.

### 13. Practical LLMOps engineering lifecycle

```text
Model Inference
      ->
Serving
      ->
Routing
      ->
Resource Awareness
      ->
Telemetry
      ->
Observability
      ->
Guardrails
      ->
Evaluation
      ->
LLM-as-a-Judge
      ->
Benchmarking
      ->
Quality Metrics
      ->
Quality Gate
      ->
CI/CD
      ->
Operational LLMOps
```

This repository therefore focuses on **how to engineer around LLMs**, not only how to invoke them.

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

The validated Prometheus scrape jobs are:

```text
runtime-api
prometheus
dcgm
evaluation
```

The evaluation exporter is deployed separately from the Runtime API so that offline quality measurements do not alter the runtime generation hot path.

## Security and exposure model

The current development/reference environment deliberately restricts host exposure of selected metrics endpoints:

```text
Prometheus  -> 127.0.0.1:9090
DCGM        -> 127.0.0.1:9400
Evaluation  -> 127.0.0.1:9108
```

The services communicate through the private Docker network using service names rather than container IP addresses.

This is a development/reference configuration, not a substitute for production ingress, authentication, TLS, secret management, network policy, or workload identity design.

## Reliability and recovery

The Runtime API, Streamlit and supporting deployment definitions use Docker `restart: unless-stopped` where applicable so services can recover from normal container restarts.

Controlled restart recovery has been validated for core services, including health endpoint checks after restart.

A complete EC2 stop/start recovery procedure is documented, but a full EC2 stop/start recovery test is not claimed as validated.

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
   +--> Evaluation Metrics Exporter
```

Operational recovery should validate service health before performing live inference or evaluation workloads.

## Testing

The current Phase 15 local regression baseline is:

```text
122 passed
3 skipped
2 warnings
```

Run the standard test suite with:

```bash
PYTHONPATH=services/runtime-api pytest -q
```

Evaluation tests can be run directly with:

```bash
PYTHONPATH=. pytest -q evaluation/tests
```

Live E2E tests require explicit opt-in:

```bash
RUN_E2E=1 PYTHONPATH=services/runtime-api pytest -m e2e -q
```

During periods without active development, GPU and other Docker workloads should be intentionally stopped to control runtime cost.

## Repository structure

```text
.
|-- frontend/
|-- services/
|   `-- runtime-api/
|-- evaluation/
|   |-- datasets/
|   |-- judges/
|   |-- metrics/
|   |-- calibration/
|   |-- reports/
|   |-- schemas/
|   |-- tests/
|   |-- benchmark.py
|   `-- quality_gate.py
|-- deployment/
|   |-- frontend/
|   |-- runtime-api/
|   |-- observability/
|   `-- k8s/
|-- tests/
|-- docs/
|   |-- architecture/
|   |-- llmops/
|   |-- operations/
|   `-- interview-notes/
|-- .github/
|   `-- workflows/
`-- README.md
```

The repository separates application code, evaluation code, deployment configuration, automated tests and operational documentation so the platform can be explored component by component.

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
- NVIDIA GPU and NVIDIA Container Toolkit/runtime for GPU inference
- a GPU-capable host for TinyLlama and vLLM execution

### 3. Run the standard tests

```bash
PYTHONPATH=services/runtime-api pytest -q
```

### 4. Review the deployment definitions

Runtime API, frontend and observability deployment definitions are kept under `deployment/`.

The Runtime API deployment definition is:

```text
deployment/runtime-api/docker-compose.yml
```

The observability stack is under:

```text
deployment/observability/
```

The validated Docker deployment uses the external network:

```text
enterprise-ai-net
```

Review environment variables, external network requirements and GPU runtime assumptions before starting services.

### 5. Validate health

Typical checks include:

```bash
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8501/_stcore/health
curl -s http://127.0.0.1:9090/-/healthy
curl -s http://127.0.0.1:3000/api/health
curl -s http://127.0.0.1:9108/metrics
```

## Evaluation workflow

The Phase 15 evaluation workflow is intentionally separated from normal runtime serving.

### Dataset

The versioned dataset is:

```text
evaluation/datasets/v1.0/evaluation_dataset.jsonl
```

It contains 40 cases covering factual, reasoning, instruction-following, explanation, summarization and safety scenarios.

### Candidate generation

The current candidate models are:

```text
TinyLlama
Phi-3 Mini
```

### Evaluation judge

The dedicated judge is:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

### Benchmark report

The current benchmark report is:

```text
evaluation/reports/model_benchmark.json
```

### Quality gate

The local quality gate can be run with:

```bash
PYTHONPATH=. python evaluation/quality_gate.py \
  --report evaluation/reports/model_benchmark.json \
  --model phi3
```

The GitHub Actions quality gate is manually triggered through:

```text
.github/workflows/evaluation-quality-gate.yml
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
| [Restart Recovery](docs/operations/restart-recovery.md) | Container and EC2 recovery guidance |
| [Interview Notes](docs/interview-notes/llmops-interview-notes.md) | Interview questions and talking points |

## What this project does not claim

This repository is a **learning and portfolio reference implementation**, not a claim of production readiness.

The current validated work should not be described as:

- a production EKS deployment
- a production-scale inference service
- a multi-GPU benchmarked platform
- an SLA/SLO-backed service
- a generally hallucination-free LLM system
- a production-grade human-calibrated evaluation program

The current benchmark is a small POC smoke benchmark, and the current judge calibration data is explicitly provisional pending independent human annotation.

Future production hardening would require additional controls such as identity/authentication, TLS, secrets management, ingress/API gateway, infrastructure-as-code, centralized logging, distributed tracing, production-grade evaluation pipelines, capacity planning, model lifecycle management, security scanning and disaster recovery.

## Roadmap

### Next engineering areas

- stronger human-calibrated evaluation datasets and judge reliability analysis
- richer tracing and production SLOs
- RAG / grounded knowledge workflows
- fine-tuning with SFT + LoRA + QLoRA
- agentic / tool-using AI workflows
- Kubernetes-native application deployment
- stronger automated end-to-end validation
- model registry and model lifecycle management

### Longer-term areas

- production-grade security, PII and safety controls
- autoscaling and inference optimization
- advanced adaptive routing using quality / cost / latency / resource signals
- multimodal AI workflows
- enterprise RAG optimization with hybrid search and reranking

## Current portfolio milestone

**Sprint 15 — LLM Evaluation & Quality Engineering** is the current completed portfolio milestone.

The previous Sprint 14 release remains preserved and is tagged:

```text
sprint-14-final
```

Sprint 15 adds:

```text
15.1 -> Evaluation Foundation
15.2 -> Deterministic Evaluation
15.3 -> LLM-as-a-Judge
15.4 -> TinyLlama / Phi-3 Model Benchmark
15.5 -> Judge Calibration Framework
15.6 -> Prometheus / Grafana Evaluation Observability
15.7 -> CI/CD Evaluation Quality Gate
```

The completed Sprint 15 implementation includes a versioned 40-case evaluation dataset, deterministic quality metrics, a dedicated LLM-as-a-Judge workflow using Qwen/Qwen2.5-1.5B-Instruct, candidate-model benchmarking, judge calibration scaffolding, Prometheus/Grafana evaluation telemetry and a configurable evaluation quality gate.

The final release tag for this milestone is intended to be:

```text
sprint-15-final
```

## Learning path

A useful way to explore the project is to follow the platform in this order:

```text
LLM inference
    ->
Runtime API
    ->
Model routing
    ->
Containerization
    ->
GPU operations
    ->
Metrics
    ->
Observability
    ->
Quality guardrails
    ->
LLM evaluation
    ->
LLM-as-a-Judge
    ->
Model benchmarking
    ->
Evaluation observability
    ->
CI/CD quality gate
    ->
RAG
    ->
Fine-tuning
    ->
Agentic AI
    ->
Kubernetes and production hardening
```

## About

This project is part of a hands-on journey into **LLMOps, MLOps, GenAI infrastructure, GPU inference, observability, evaluation and AI platform engineering**.

The repository intentionally documents both successful implementation and troubleshooting lessons so it can be useful to people learning these areas — not only to people reviewing the final code.

## Repository

https://github.com/pnrajeshkumar26/Enterprise-AI-Platform
