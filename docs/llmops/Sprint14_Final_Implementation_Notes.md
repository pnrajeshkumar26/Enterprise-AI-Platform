# Sprint 14 - Final LLMOps Implementation Notes

## 1. Sprint Overview

Sprint 14 extended the Enterprise AI Platform from observability into operational LLMOps capabilities.

Completed stages:

| Stage | Capability | Status |
|---|---|---|
| 7 | Explainable Routing | Complete |
| 8 | Gateway Prometheus Metrics | Complete |
| 8A | Streamlit Request Telemetry | Complete |
| 9 | Grafana LLMOps Dashboard | Complete |
| 10 | Unit / Integration / E2E Testing | Complete |
| 11 | Restart / Recovery | Complete |

Current checkpoint:

```text
sprint-14-stage-11-restart-recovery
```

Sprint 14 progression:

```text
Gateway
  -> Telemetry
  -> Cost Estimation
  -> Latency / Capacity Signals
  -> Intelligent Routing
  -> Explainable Routing
  -> Prometheus Metrics
  -> Streamlit Telemetry
  -> Grafana LLMOps Dashboard
  -> Testing
  -> Restart / Recovery
```

The implementation focused on making routing decisions observable, explainable and testable while keeping the platform operationally practical.
## 2. Final Platform Architecture

```text
User / Browser
      |
      v
Streamlit :8501
      |
      v
Runtime API :8001
      |
      +--> Request Validation
      |
      +--> Custom LLM Gateway
      |
      +--> Intelligent Multi-Signal Router
      |
      +--> Quality Guard
      |
      +--> Prometheus Metrics
      |
      +--------------------------+
      |                          |
      v                          v
 TinyLlama                    Phi-3 Mini
 llama.cpp                    vLLM
 Tesla T4                     Tesla T4
      |
      +--------------------------+
                 |
                 v
            Prometheus :9090
                 |
                 v
             Grafana :3000

GPU telemetry:
DCGM Exporter :9400
```

Primary Docker network:

```text
enterprise-ai-net
```

Core containers:

```text
enterprise-runtime-api
enterprise-streamlit
enterprise-tinyllama-gpu
enterprise-vllm
enterprise-prometheus
enterprise-grafana
enterprise-dcgm-exporter
enterprise-ai-worker
enterprise-ai-control-plane
```

## 3. Stage 7 - Explainable Routing

### Objective

Make automatic model selection deterministic, explainable and observable.

The `auto` route evaluates multiple signals before inference.

### Routing Signals

Pre-routing signals include:

- request characteristics
- technical / factual indicators
- estimated input tokens
- requested output-token budget
- model context and token capacity
- historical latency
- shared GPU / resource pressure
- backend and model availability
- base router preference

The router produces a score for each configured model.

### Routing Score Breakdown

Each model decision exposes:

```text
base_preference
capacity
latency
gpu_pressure
total
```

The API exposes the final routing explanation through the request response.

Conceptual response structure:

```text
selected_model
reason
scores
breakdown
```

### Capacity-Aware Routing

Capacity is checked before inference.

If the preferred model cannot satisfy the requested token budget, the gateway can select an alternate model when sufficient capacity is available.

When neither configured model can safely satisfy the request, the gateway rejects the request rather than silently exceeding model context limits.

### Deterministic Behavior

The routing logic is intentionally deterministic.

This provides:

- repeatable decisions
- easier unit testing
- easier troubleshooting
- explainable model selection
- predictable operational behavior

Manual model selection remains available for controlled testing.
## 4. Stage 8 - Gateway Prometheus Metrics

### Objective

Expose routing and request behavior as Prometheus metrics so that operational decisions can be monitored over time.

### Routing Metrics

The gateway records metrics including:

- `llm_routing_capacity_overrides_total`
- `llm_routing_capacity_rejections_total`
- `llm_routing_selected_models_total`
- `llm_routing_outcomes_total`
- `llm_routing_score`
- `llm_routing_score_margin`

### Routing Outcomes

Routing outcomes capture how the final model decision was reached.

Examples include:

- explicit
- capacity_override
- tie_base_preserved
- multi_signal
- capacity_rejected

Capacity rejection is treated as a request-level routing outcome and does not represent a successful model generation.

Non-finite routing scores are sanitized before metric recording so that invalid numerical values do not propagate into the monitoring layer.

## 5. Stage 8A - Streamlit Request Telemetry

### Objective

Expose request-level telemetry in the Streamlit application so that users can observe the behavior of individual LLM requests.

Telemetry is collected from the Runtime API response and provides visibility into request execution without replacing the backend monitoring stack.

The request telemetry complements Prometheus and Grafana by presenting request-specific information at the application layer.

## 6. Stage 9 - Grafana LLMOps Dashboard

### Objective

Create an operational dashboard that combines request, routing, token, latency, resource and cost signals.

Dashboard configuration:

```text
deployment/observability/grafana/dashboards/enterprise-ai-llmops.json
```

### Dashboard Panels

The dashboard retains the existing platform observability panels and adds LLMOps-focused views for:

- routing outcomes
- capacity overrides
- capacity rejections
- final selected model
- routing score
- routing score margin
- input token throughput
- output token throughput
- total token throughput
- estimated cost rate
- cumulative estimated cost
- estimated cost per hour

### Operational Interpretation

The dashboard is intended to answer practical operational questions:

- Which model is being selected?
- Are capacity constraints forcing model changes?
- Are routing scores close or clearly separated?
- How much token traffic is being processed?
- What is the observed estimated cost?
- Are routing and infrastructure signals changing together?

The Grafana dashboard therefore acts as the operational LLMOps view while Prometheus provides the underlying metric storage and query layer.
## 7. Stage 10 - Unit, Integration and E2E Testing

### Objective

Validate the LLMOps capabilities at three levels without requiring repeated live GPU inference.

### Test Structure

The repository contains unit tests covering routing, capacity, latency, GPU state, token capacity, cost estimation, response guarding, routing explanations, Prometheus metrics and related gateway behavior.

Integration tests were added under:

```text
tests/integration/test_runtime_api_integration.py
```

The integration suite validates:

- Runtime API health
- models endpoint behavior
- generate request validation
- metrics endpoint availability and expected metric families

E2E smoke tests were added under:

```text
tests/e2e/test_live_smoke.py
```

E2E tests are explicitly gated by the `RUN_E2E` environment variable so they do not accidentally trigger live infrastructure usage.

### Test Results

The completed Stage 10 validation produced:

```text
86 passed
5 integration tests passed
3 E2E tests skipped by default
```

Full local test command:

```bash
PYTHONPATH=services/runtime-api pytest -q
```

Integration-only command:

```bash
PYTHONPATH=services/runtime-api pytest -m integration -q
```

Explicit E2E command:

```bash
RUN_E2E=1 PYTHONPATH=services/runtime-api pytest -m e2e -q
```

Only one controlled live generation was used during Stage 10 validation to confirm the deployed Runtime API and routing path. No repeated live generation was required.

## 8. Stage 11 - Restart and Recovery

### Objective

Make core application containers resilient to normal container restarts and document the recovery procedure.

### Permanent Restart Policy

The Runtime API deployment is defined in:

```text
deployment/runtime-api/docker-compose.yml
```

The deployment uses:

```yaml
restart: unless-stopped
```

Current Runtime API image:

```text
enterprise-runtime-api:3.19
```

The Runtime API image version and deployment image reference must remain synchronized whenever a new image is created.

### Controlled Restart Validation

The following controlled restart checks were completed:

```text
Runtime API container restart -> health endpoint returned healthy
Streamlit container restart -> Streamlit health endpoint returned ok
```

The restart policy was verified as:

```text
unless-stopped
```

### EC2 Recovery Procedure

Full EC2 stop/start recovery was documented as an operational procedure but was not repeatedly executed during Stage 11.

Typical recovery sequence:

```bash
aws ssm start-session --target i-0b91bf8e870419f83
sudo -iu ubuntu
source ~/gpu-env/bin/activate
cd ~/Enterprise-AI-Platform
docker ps -a
docker compose -f deployment/runtime-api/docker-compose.yml up -d
```

After recovery, validate the Runtime API and Streamlit health endpoints before performing any live inference test.

### Recovery Design Principle

Restart/recovery is treated as an operational concern separate from routing logic. The goal is to ensure that application services can be restarted predictably while the deployment configuration remains the source of truth.
## 9. Cost-Control Operating Model

The platform was developed with explicit AWS cost control because GPU compute and persistent infrastructure can continue to incur charges when left running.

Observed cost areas during the POC included:

- EC2 GPU compute
- EBS storage
- EBS snapshots
- public IPv4 usage
- ECR storage

The practical operating model is:

```text
Active development / validation
        -> Start only required services

Validation complete
        -> Stop unnecessary Docker workloads
        -> Stop the EC2 instance when no work is planned

Resume development
        -> Start EC2 / reconnect through SSM
        -> Start required services
        -> Validate health endpoints
        -> Perform live inference only when required
```

GPU inference should not be run repeatedly when unit and integration validation can provide equivalent confidence.

Persistent EBS, snapshot and public IPv4 resources should also be reviewed separately because stopping an EC2 instance does not eliminate every infrastructure charge.

## 10. Important Operational Commands

### Connect to the EC2 instance

```bash
aws ssm start-session --target i-0b91bf8e870419f83
sudo -iu ubuntu
source ~/gpu-env/bin/activate
cd ~/Enterprise-AI-Platform
```

### Check containers

```bash
docker ps
docker ps -a
```

### Runtime API health

```bash
curl -fsS http://127.0.0.1:8001/health
```

### Streamlit health

```bash
curl -fsS http://127.0.0.1:8501/_stcore/health
```

### Runtime API deployment

```bash
docker compose -f deployment/runtime-api/docker-compose.yml up -d
```

The Runtime API deployment definition is the source of truth for the container restart policy and image reference.

## 11. Runtime API Image Versioning Rule

Current image reference:

```text
enterprise-runtime-api:3.19
```

Whenever a new Runtime API image is created, the image tag in `deployment/runtime-api/docker-compose.yml` must be updated to the same tag before deployment.

Example:

```text
New image created:
enterprise-runtime-api:3.20

Deployment file updated:
enterprise-runtime-api:3.20
```

This prevents the built image and deployment definition from drifting apart.

## 12. Git Checkpoints

The Sprint 14 implementation was checkpointed incrementally so every major capability remains independently recoverable.

| Stage | Commit | Tag |
|---|---|---|
| 7 | `09fa3f2` | `sprint-14-stage-7-explainable-routing` |
| 8 | `7e23220` | `sprint-14-stage-8-prometheus-routing-metrics` |
| 8A | `0204410` | `sprint-14-stage-8a-streamlit-request-telemetry` |
| 9 | `281fbab` | `sprint-14-stage-9-grafana-llmops-dashboard` |
| 10 | `1158ecf` | `sprint-14-stage-10-testing` |
| 11 | `558531a` | `sprint-14-stage-11-restart-recovery` |

The Stage 12 documentation commit and final Sprint 14 release tag are created after this document and README are reviewed and validated.

## 13. Interview Talking Points

### How does the router choose a model?

The `auto` route combines deterministic signals such as prompt characteristics, token capacity, latency history, GPU pressure and backend availability. Each model receives an explainable score and the final decision is exposed through the routing explanation.

### Why is capacity checked before inference?

The gateway should avoid sending a request to a model that cannot safely satisfy the requested token budget. Capacity-aware routing can redirect the request to an alternate model or reject it when no safe model is available.

### Why use Prometheus and Grafana?

Prometheus provides the metric collection and query layer. Grafana provides the operational visualization layer for routing, token, latency, resource and cost signals.

### Why gate E2E tests?

Live E2E tests can trigger actual infrastructure and GPU usage. Explicit gating keeps the default test suite fast, repeatable and cost-conscious while still allowing controlled live validation.

### How is restart recovery handled?

Restart behavior is defined in deployment configuration using `restart: unless-stopped`. Controlled container restart checks were validated, while the full EC2 stop/start recovery procedure was documented separately.

### What is intentionally not claimed?

Stage 11 did not claim a full EC2 stop/start recovery validation. The validation performed was controlled container restart testing plus documented recovery procedures.

Cost estimation is an operational estimate based on runtime and configured infrastructure assumptions; it is not a replacement for the authoritative AWS billing system.

Latency history is maintained in the application runtime and is therefore reset when the service process restarts.

GPU pressure is treated as a shared infrastructure signal rather than a per-model utilization measurement.

## 14. Final Sprint 14 Checklist
The checklist below represents the intended final release state and is completed as part of the Stage 12 commit and Stage 13 release tagging sequence.

- [x] Explainable multi-signal routing implemented
- [x] Capacity-aware routing implemented
- [x] Routing outcomes exposed as Prometheus metrics
- [x] Streamlit request telemetry implemented
- [x] Grafana LLMOps dashboard updated
- [x] Unit tests validated
- [x] Integration tests validated
- [x] E2E tests explicitly gated
- [x] Controlled Runtime API restart validated
- [x] Controlled Streamlit restart validated
- [x] Permanent Runtime API restart policy documented
- [x] Runtime API image/deployment synchronization rule documented
- [x] Cost-control operating model documented
- [x] Git checkpoints recorded
- [x] Stage 12 documentation commit
- [x] Stage 13 final release tag

## 15. Conclusion

Sprint 14 transformed the platform from a system with basic observability into a more complete LLMOps-oriented platform with intelligent routing, explainability, telemetry, operational dashboards, automated testing and restart/recovery practices.

The resulting design emphasizes deterministic behavior, operational visibility, controlled live validation and explicit cost awareness.
