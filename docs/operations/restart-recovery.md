# Restart Recovery

## Objective

The platform should recover from container restarts and EC2 stop/start events without manual service launches.

## Why Streamlit was changed

The frontend originally ran as a process in an interactive environment. After the environment/session ended, Streamlit had to be started manually.

It is now a Docker service with:

```yaml
restart: unless-stopped
```

and a health check against:

```text
/_stcore/health
```

## Recovery validation

After EC2 restart:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Confirm Streamlit is present and healthy, then:

```bash
curl -s http://127.0.0.1:8501/_stcore/health
```

Expected:

```text
ok
```

Validate the Runtime API:

```bash
curl -s http://127.0.0.1:8001/health
```

Validate Prometheus targets:

```bash
curl -s http://127.0.0.1:9090/api/v1/targets | python3 -m json.tool
```

## Architecture lesson

A frontend that depends on a manually attached shell is operationally different from a container-managed service. For a portfolio platform, containerizing the frontend makes the lifecycle consistent with the rest of the stack.
