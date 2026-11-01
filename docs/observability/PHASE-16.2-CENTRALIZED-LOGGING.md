# Phase 16.2 — Centralized Logging with Grafana Alloy and Loki

**Project:** Enterprise AI Platform
**Implementation environment:** Windows PowerShell + Docker Desktop (Linux containers)
**Status:** Implemented and end-to-end validated for Runtime API `/health` and `/models` requests
**Related phase:** Phase 16.1 — OpenTelemetry Tracing

---

## 1. Executive summary

Phase 16.2 adds centralized application-log collection to the existing observability stack. Grafana Alloy reads the container logs for the Enterprise Runtime API and forwards them to Loki. Grafana Explore can query those logs and correlate them with traces stored in Tempo.

The implementation was validated with two API endpoints:

- `GET /health` — matching Runtime API log and Tempo trace verified.
- `GET /models` — matching Runtime API log and Tempo trace verified.

Both navigation directions were demonstrated in Grafana:

1. **Tempo → Loki:** use **Logs for this span** from a trace/span to open related log entries.
2. **Loki → Tempo:** expand a log entry and use **TraceID → View trace** to open its corresponding trace.

The final checks passed: 90 runtime tests passed, 3 were skipped, 36 evaluation tests passed, all three Compose configurations validated, Alloy/Loki/Tempo configuration validation passed, and `git diff --check` returned no errors.

## 2. Architecture

```text
Runtime API (FastAPI container)
  ├─ OpenTelemetry request spans ------------------------------┐
  │                                                            v
  │                                                   Grafana Alloy
  │                                                   OTLP receiver :4318
  │                                                            |
  │                                                            v
  │                                                          Tempo
  │                                                     trace storage
  │                                                            |
  │                                                            v
  │                                                          Grafana
  │
  └─ stdout/stderr → Docker log source in Alloy → Loki → Grafana Explore
                                        trace_id / span_id enable correlation
```

### Component responsibilities

| Component | Responsibility | Local endpoint / network target |
|---|---|---|
| Runtime API | Produces request traces and application request-completion logs | Host port `8001` → container port `8000` |
| Grafana Alloy | Receives OTLP traces; discovers Docker containers and collects Runtime API stdout/stderr logs | Host OTLP HTTP port `127.0.0.1:4318`; container target `tempo:4317` / `loki:3100` |
| Tempo | Stores distributed traces | Host `127.0.0.1:3200`; container target `tempo:3200` |
| Loki | Stores and queries logs | Host `127.0.0.1:3100`; container target `loki:3100` |
| Grafana | Queries Tempo, Loki and Prometheus; provides trace/log navigation | Host `127.0.0.1:3000` |
| Prometheus | Existing metrics backend; retained unchanged by this phase | Host `127.0.0.1:9090` |

All observability containers join the existing external Docker network `enterprise-ai-net`. Persistent volumes used by this local setup are `enterprise-tempo-data`, `enterprise-loki-data`, `enterprise-alloy-data`, `enterprise-grafana-data`, and `enterprise-prometheus-data`.

## 3. Files created or updated

### Added for centralized logging / correlation

- `deployment/observability/tracing/loki/loki.yaml`
- `deployment/observability/grafana/provisioning/datasources/loki.yml`
- `deployment/observability/grafana/provisioning/datasources/tempo.yml` (provisioned correlation configuration)

### Updated or used by the combined observability stack

- `deployment/observability/tracing/alloy/config.alloy`
- `deployment/observability/tracing/docker-compose.yml`
- `deployment/runtime-api/docker-compose.yml`
- `deployment/observability/grafana/docker-compose.yml`
- `services/runtime-api/app/main.py`
- `services/runtime-api/requirements.txt`
- `services/runtime-api/requirements-docker.txt`
- `services/runtime-api/app/observability/tracing.py`
- `services/runtime-api/app/observability/__init__.py`
- `tests/test_tracing.py`

Phase 16.1 supplied the OpenTelemetry instrumentation and the trace-aware log format. Phase 16.2 added Loki, Docker log collection, the request-completion log, Grafana data-source configuration and correlation.

> **Working-tree caution:** `docs/troubleshooting/TROUBLESHOOTING-002-Dynamic-Model-Registry-Integration.md` was already modified before this phase and must be preserved. Review changes before staging; do not use `git add .`.

## 4. Loki configuration

File: `deployment/observability/tracing/loki/loki.yaml`

Key settings:

- HTTP API port: `3100`.
- Filesystem-backed storage under `/loki`.
- TSDB index with schema `v13`.
- Log-retention target: `72h`.
- Compactor enabled to support retention cleanup.
- `auth_enabled: false`, appropriate only for this isolated local lab; the host-published Loki endpoint is bound to `127.0.0.1`.

The `loki` service uses image `grafana/loki:3.7.9`, mounts the YAML read-only and stores data in persistent volume `enterprise-loki-data`.

## 5. Grafana Alloy configuration

File: `deployment/observability/tracing/alloy/config.alloy`

### Trace pipeline retained

1. `otelcol.receiver.otlp "default"` accepts OTLP over gRPC on `4317` and HTTP on `4318`.
2. `otelcol.processor.batch "default"` batches spans.
3. `otelcol.exporter.otlp "tempo"` forwards traces to `tempo:4317` over the Docker network.

### Log pipeline added

1. `discovery.docker "containers"` discovers Docker containers using `unix:///var/run/docker.sock`.
2. `discovery.relabel "runtime_api_only"` keeps only the `enterprise-runtime-api` container.
3. `loki.source.docker "runtime_api"` reads that container's stdout/stderr logs.
4. `loki.write "local"` forwards logs to `http://loki:3100/loki/api/v1/push`.
5. Log labels include `job="runtime-api"` and `service="enterprise-runtime-api"`. Loki also detected `service_name="enterprise-runtime-api"` in the observed stream.

The Docker socket is mounted into Alloy for container discovery and log collection. **Security note:** even mounted read-only, Docker socket access is highly privileged because API operations can control the daemon. Keep this design confined to the local lab unless a restricted production design is implemented.

A backup named `config.alloy.phase16.1.bak` was created during the configuration update. Review it before staging; it is a backup, not an active configuration file.

## 6. Runtime API configuration

File: `deployment/runtime-api/docker-compose.yml`

The Compose service builds from `../../services/runtime-api` using `Dockerfile`, tags the image `enterprise-runtime-api:3.19`, and maps port `8001` to container port `8000`. Environment variables include:

```yaml
OTEL_SERVICE_NAME: enterprise-runtime-api
OTEL_EXPORTER_OTLP_ENDPOINT: "http://enterprise-alloy:4318"
PYTHONUNBUFFERED: "1"
```

The Dockerfile installs `requirements-docker.txt` and copies the application source. The image was rebuilt after adding request-completion logging; the container's `/health` endpoint returned HTTP 200.

### Request-completion log

A FastAPI HTTP middleware in `services/runtime-api/app/main.py` logs completed requests, excluding frequent `/metrics` scrapes. The existing OpenTelemetry logging instrumentation injects trace context into Python log records.

Observed format (illustrative):

```text
2026-10-29 ... INFO app.main trace_id=<32-hex-character-id> span_id=<16-hex-character-id> service=enterprise-runtime-api http_request_completed method=GET path=/models status_code=200
```

The exact trace/span IDs vary per request. Do not use a placeholder as an actual ID.

## 7. Grafana data-source configuration

### Loki data source

File: `deployment/observability/grafana/provisioning/datasources/loki.yml`

- Name / UID: `Loki` / `loki`.
- URL: `http://loki:3100` (container-to-container address).
- Derived field `TraceID` extracts the 32-character lowercase hex value from `trace_id=...`.
- The derived field points to Tempo (`datasourceUid: tempo`) and displays the link label **View trace**.

### Tempo data source

File: `deployment/observability/grafana/provisioning/datasources/tempo.yml`

- Name / UID: `Tempo` / `tempo`.
- URL: `http://tempo:3200`.
- `tracesToLogsV2.datasourceUid` points to Loki (`loki`).
- Start/end time shifts are `-1m` / `+1m`.
- `service.name` is mapped to the Loki `service` label.
- Native trace-ID filtering is enabled (`filterByTraceID: true`); span-ID filtering is disabled.
- Custom query mode is disabled (`customQuery: false`).

The YAML declared provisioning version `5` in the last file review. Grafana's data-source API reported an effective version of `6` and showed the expected `tracesToLogsV2` block. Grafana reports the data source as read-only because it is provisioned.

## 8. Implementation procedure

The following summarizes the sequence performed in the local environment.

### 8.1 Validate and start Loki

Create `deployment/observability/tracing/loki/loki.yaml`, then validate it with:

```powershell
$configPath = (Resolve-Path .\deployment\observability\tracing\loki\loki.yaml).Path

docker run --rm `
  --mount "type=bind,source=$configPath,target=/etc/loki/loki.yaml,readonly" `
  grafana/loki:3.7.9 `
  --config.file=/etc/loki/loki.yaml `
  --verify-config=true
```

Successful validation output observed:

```text
msg="config is valid"
```

Add the `loki` service and `loki-data` volume to `deployment/observability/tracing/docker-compose.yml`, then start only Loki:

```powershell
docker compose -f .\deployment\observability\tracing\docker-compose.yml up -d loki
Invoke-WebRequest -Uri "http://127.0.0.1:3100/ready" -TimeoutSec 10 -UseBasicParsing
```

Loki readiness returned HTTP 200 and `ready` after startup.

### 8.2 Extend Alloy for Docker logs

Add Docker discovery, the relabel rule that filters for `enterprise-runtime-api`, `loki.source.docker`, and `loki.write`. Mount `/var/run/docker.sock:/var/run/docker.sock:ro` in the Alloy service and set `depends_on` for `tempo` and `loki`.

Validate before restarting:

```powershell
docker compose -f .\deployment\observability\tracing\docker-compose.yml config

docker compose -f .\deployment\observability\tracing\docker-compose.yml run --rm --no-deps --entrypoint /bin/alloy alloy validate /etc/alloy/config.alloy
```

Then recreate only Alloy:

```powershell
docker compose -f .\deployment\observability\tracing\docker-compose.yml up -d --force-recreate alloy
```

Alloy health returned HTTP 200 (`All Alloy components are healthy.`), and logs showed initialization of `discovery.docker.containers`, `loki.source.docker.runtime_api`, and `loki.write.local`.

### 8.3 Build and run the Runtime API image

Update the Runtime API Compose definition to include the build context and OTLP environment variables, then run:

```powershell
docker compose -f .\deployment\runtime-api\docker-compose.yml config
docker compose -f .\deployment\runtime-api\docker-compose.yml up -d --build runtime-api
Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -TimeoutSec 15 -UseBasicParsing
```

The build completed successfully and `/health` returned HTTP 200.

### 8.4 Provision Grafana data sources

Create `loki.yml`, update `tempo.yml` with `tracesToLogsV2`, validate both Compose files, and restart Grafana to load the provisioned settings:

```powershell
docker compose -f .\deployment\observability\grafana\docker-compose.yml config --quiet
docker compose -f .\deployment\observability\grafana\docker-compose.yml restart grafana
Invoke-WebRequest -Uri "http://127.0.0.1:3000/api/health" -TimeoutSec 15 -UseBasicParsing
```

Grafana returned HTTP 200. The data-source API confirmed that the Loki derived field and Tempo `tracesToLogsV2` settings were present.

## 9. Grafana queries used for validation

### Runtime request logs

In **Explore → Loki → Code**:

```logql
{job="runtime-api"} |= "http_request_completed"
```

### Filter to `/models`

```logql
{job="runtime-api"} |= "http_request_completed" |= "/models"
```

### Find logs containing a specific trace ID

Replace the example ID with the desired trace ID:

```logql
{job="runtime-api"} |= "17f3e49651a09d98812249941e5098e2"
```

### Runtime API traces

In **Explore → Tempo → TraceQL**:

```traceql
{ resource.service.name = "enterprise-runtime-api" }
```

To reopen an older, known trace when it is outside the Explore time range, switch the query type to **Trace ID** and enter its full ID.

## 10. End-to-end test evidence

### `GET /health`

Observed trace ID:

`fa3fb1fd9fffdfb9b181077335022d0f`

Observed span ID in the request-completion log:

`7b1ccd98345535f5`

Observed log message:

```text
http_request_completed method=GET path=/health status_code=200
```

The trace was returned by Tempo, the matching request log was found in Loki, and **Logs for this span** displayed the log in Grafana Explore.

### `GET /models`

Observed trace ID:

`17f3e49651a09d98812249941e5098e2`

Observed span ID in the request-completion log:

`9ace45be797c3b9d`

Observed log message:

```text
http_request_completed method=GET path=/models status_code=200
```

Grafana displayed the corresponding `GET /models` trace and its matching Loki log. Expanding the log showed **Links → TraceID → View trace**; clicking the link opened the associated trace. This validated the reverse Loki → Tempo navigation as well.

## 11. Troubleshooting notes

| Symptom | Cause / evidence | Resolution performed |
|---|---|---|
| Loki validation returned `flag provided but not defined: -config` | The single-hyphen flag was parsed incorrectly by the invocation. | Used the double-hyphen form: `--config.file=/etc/loki/loki.yaml --verify-config=true`; Loki reported `config is valid`. |
| Loki `/ready` initially returned HTTP 503 | Request occurred during startup; logs later showed `Loki started`. | Rechecked readiness; it returned HTTP 200 and `ready`. |
| Alloy validation reported `missing ',' in field list` in the labels map | Alloy map syntax requires commas between fields. | Replaced the multiline map entries with `labels = {"job" = "runtime-api", "service" = "enterprise-runtime-api"}` and reran validation successfully. |
| Grafana API connection closed right after restart | Request ran while Grafana was restarting. The previous PowerShell `$tempo` variable still held stale data because the assignment failed. | Checked `/api/health` first, then queried the data-source API again after Grafana returned HTTP 200. |
| Tempo Explore returned `0 series returned` | The selected default time range did not include an older trace. | Used the Trace ID query type to retrieve the known trace directly. |
| Tempo data source lacked `tracesToLogsV2` in the API response | The provisioned data-source definition was not yet reflected in the effective settings. | Updated `tempo.yml` provisioning version, restarted Grafana, and verified the API contained `tracesToLogsV2` with Loki UID `loki`. |
| PowerShell displayed `else` as an unknown command | The `else` clause had been entered as a separate command after its `if` block. | Harmless to configuration; subsequent validation commands were run independently. |
| `docker logs` produced a PowerShell `NativeCommandError` despite a running API container | Docker emitted log output to stderr, which PowerShell displayed as an error record. | Confirmed container status and successful HTTP 200 health response; log lines were present. |

## 12. Final validation results

Final checks recorded on October 29, 2026:

| Check | Result |
|---|---|
| Runtime API test suite | **90 passed, 3 skipped** |
| Evaluation test suite | **36 passed** |
| Runtime test warnings | 3 deprecation warnings; no test failures |
| Tracing Compose | `docker compose ... config --quiet` passed |
| Grafana Compose | `docker compose ... config --quiet` passed |
| Runtime API Compose | `docker compose ... config --quiet` passed |
| Alloy configuration | `alloy validate` passed |
| Loki configuration | `--verify-config=true` reported `config is valid` |
| Tempo configuration | `--config.verify=true` passed |
| Git whitespace check | `git diff --check` returned no output/errors |
| Tempo → Loki correlation | Verified for `/health` and `/models` |
| Loki → Tempo correlation | Verified for `/models` using the `View trace` link |

The three test warnings were deprecations: `httpx` used with `starlette.testclient`, and `HTTP_422_UNPROCESSABLE_ENTITY`. They did not fail the runtime tests.

## 13. Security and operational considerations

- Loki has `auth_enabled: false`; do not expose this lab deployment to untrusted networks. Its host port is bound to loopback.
- Grafana's Compose configuration binds its host port to `127.0.0.1:3000`.
- The Runtime API Compose mapping is currently `8001:8000`, which Docker normally publishes on all host interfaces. For a strictly local-only workstation lab, consider changing it to `127.0.0.1:8001:8000` after reviewing any other clients that depend on access.
- Alloy has Docker socket access. Even a read-only socket mount should be treated as highly privileged; reassess it before any production use.
- Local filesystem storage and 72-hour retention are lab choices, not a production durability design. Long-term storage, access control, retention policy, redaction and cloud cost controls must be reviewed before a cloud deployment.
- Prometheus configuration and scrape targets were intentionally not changed in this phase.

## 14. Git and handoff status

The changes remain **uncommitted**. The latest observed working-tree status included:

```text
 M deployment/observability/grafana/docker-compose.yml
 M deployment/runtime-api/docker-compose.yml
 M docs/troubleshooting/TROUBLESHOOTING-002-Dynamic-Model-Registry-Integration.md
 M services/runtime-api/app/main.py
 M services/runtime-api/requirements-docker.txt
 M services/runtime-api/requirements.txt
?? deployment/observability/grafana/provisioning/datasources/loki.yml
?? deployment/observability/grafana/provisioning/datasources/tempo.yml
?? deployment/observability/tracing/
?? services/runtime-api/app/observability/
?? tests/test_tracing.py
```

The troubleshooting document listed above was a pre-existing modification and must not be accidentally reverted, staged, or included in this phase unless reviewed explicitly. Before committing, inspect untracked files under `deployment/observability/tracing/`, especially `config.alloy.phase16.1.bak`, and stage only the intended implementation and documentation files.

## 15. Completion statement and next phase

**Phase 16.2 is functionally validated for the Runtime API endpoints tested.** Alloy collects container logs into Loki, Grafana queries logs and traces, and bidirectional trace/log navigation works for the tested `/health` and `/models` requests. Regression tests and configuration validation passed.

The next work should begin only after reviewing this documentation and the staged file list. Planned later observability work includes reviewing dashboards, useful log queries and alerts, and eventual S3-backed log storage and retention/cost optimization. Do not change the current Prometheus scrape configuration as part of this completed phase.
