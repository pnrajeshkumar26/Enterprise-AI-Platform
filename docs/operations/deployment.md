# Deployment Guide

## Reference deployment model

The validated environment uses Docker services connected to the external network:

```text
enterprise-ai-net
```

Key services include:

```text
enterprise-streamlit
enterprise-runtime-api
enterprise-tinyllama-gpu
enterprise-vllm
enterprise-prometheus
enterprise-dcgm-exporter
enterprise-grafana
```

## Startup order

A practical startup sequence is:

1. ensure the Docker network exists
2. start inference backends
3. start Runtime API
4. start Prometheus and DCGM Exporter
5. start Grafana
6. start Streamlit

The individual Compose definitions live under `deployment/`.

## Health validation

```bash
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8501/_stcore/health
curl -s http://127.0.0.1:9090/-/healthy
curl -s http://127.0.0.1:3000/api/health
```

## Container networking

Inside Docker, use service names such as:

```text
enterprise-runtime-api
enterprise-dcgm-exporter
prometheus
```

Do not hard-code ephemeral container IP addresses.
