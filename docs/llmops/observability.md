# LLMOps Observability

## Why observability is different for LLM systems

Traditional application health is not enough. An LLM service can be technically up while producing slow, expensive or low-quality responses.

This project therefore observes three dimensions:

```text
Service health
     +
Inference behavior
     +
GPU/resource state
```

## Service health

Prometheus tracks Runtime API and DCGM target health through the standard `up` metric and service-specific gauges.

## Inference behavior

The Runtime API records:

- total requests
- success/failure status
- selected model
- routing decisions
- request latency
- generation failures

## GPU state

DCGM supplies GPU-level telemetry including framebuffer memory and utilization.

## Dashboard questions

A useful LLMOps dashboard should answer:

1. Are requests succeeding?
2. Which model is serving them?
3. How much latency are users experiencing?
4. Is the backend healthy?
5. Is the GPU under memory or compute pressure?

## Alerting philosophy

Alerts should map to operational action. The current five-rule set is intentionally small and focuses on availability, failure rate, latency and GPU resource pressure.

## Next evolution

Add explicit quality-guard metrics, token/cost metrics and SLO-style panels once the core runtime remains stable.
