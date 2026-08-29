# Troubleshooting Runbook

## Principle: isolate the failing layer

Use this sequence:

```text
UI
 ↓
Runtime API
 ↓
Router
 ↓
Backend
 ↓
GPU
 ↓
Metrics
```

## Runtime API unavailable

```bash
docker ps --filter name=enterprise-runtime-api
docker logs --tail=100 enterprise-runtime-api
curl -s http://127.0.0.1:8001/health
```

## Streamlit unavailable

```bash
docker ps --filter name=enterprise-streamlit
docker inspect enterprise-streamlit --format '{{json .HostConfig.RestartPolicy}}'
curl -s http://127.0.0.1:8501/_stcore/health
```

Verify that Streamlit uses:

```text
RUNTIME_API_URL=http://enterprise-runtime-api:8000
```

## Prometheus target is down

```bash
curl -s http://127.0.0.1:9090/api/v1/targets | python3 -m json.tool
```

Then test the target from the Prometheus container/network if appropriate.

## DCGM target is down

```bash
docker logs --tail=100 enterprise-dcgm-exporter
curl -s http://127.0.0.1:9400/metrics | head -40
nvidia-smi
```

## GPU memory pressure

```bash
nvidia-smi
```

Compare the GPU memory picture with:

```text
DCGM_FI_DEV_FB_USED
DCGM_FI_DEV_FB_FREE
```

Do not increase vLLM GPU memory allocation blindly. Confirm the actual workload, model footprint and available headroom first.

## Model-quality issue

Bypass layers where possible:

```text
Streamlit -> Runtime API -> vLLM
```

Test vLLM directly. If the same quality issue appears there, it is not a routing/HTTP integration defect.

## Common lessons learned

- operational health does not prove model quality
- service names are more robust than container IPs
- backups should not sit in live provisioning directories
- localhost binding can harden host exposure without breaking internal Docker connectivity
