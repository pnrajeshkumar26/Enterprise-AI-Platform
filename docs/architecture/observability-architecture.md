# Observability Architecture

## Objective

The observability layer connects application behavior and GPU infrastructure so operational issues can be diagnosed using correlated evidence.

## Metrics pipeline

```text
Runtime API
  |
  +--> request counters
  +--> routing counters
  +--> latency histograms
  +--> failure counters
  +--> backend gauges
  +--> runtime/model gauges
  |
  v
Prometheus
  ^
  |
DCGM Exporter
  |
  +--> GPU utilization
  +--> framebuffer memory used/free
  +--> other NVIDIA telemetry
  |
  v
Grafana
  |
  +--> dashboards
  +--> alert rules
```

## Key application metrics

```text
llm_requests_total
llm_request_duration_seconds
llm_generation_failures_total
llm_routing_decisions_total
llm_backend_up
llm_models_configured
llm_runtime_up
```

## Operational alerts

The current Grafana alert group contains:

1. Runtime API Down — critical
2. DCGM Exporter Down — critical
3. High LLM Failure Rate — warning
4. High LLM P95 Latency — warning
5. GPU Memory Critical — critical

## Why GPU metrics matter

LLM inference is constrained by GPU memory, compute utilization and workload behavior. Application latency without resource context is often insufficient for root-cause analysis.

Example diagnostic relationship:

```text
P95 latency rises
      |
      +--> request volume changed?
      +--> model routing changed?
      +--> GPU utilization saturated?
      +--> GPU framebuffer memory pressure?
      +--> backend availability degraded?
```

## Current security posture

Prometheus and DCGM host ports are bound to localhost in the validated runtime. Internal Docker-network connectivity remains available to the services that need it.
