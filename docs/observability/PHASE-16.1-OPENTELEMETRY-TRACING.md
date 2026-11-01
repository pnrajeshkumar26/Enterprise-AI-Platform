# Phase 16.1 — OpenTelemetry Tracing Implementation

**Project:** Enterprise AI Platform
**Phase:** 16.1 — OpenTelemetry tracing foundation
**Status:** Implemented and locally validated
**Scope:** Instrument the FastAPI Runtime API for inbound request tracing and outbound HTTP spans, forward traces through Grafana Alloy to Grafana Tempo, and inspect traces in Grafana.

> This document records the implementation and validation performed in the local development environment. It is not a production deployment runbook. Endpoints, image tags, package versions, filenames, and commands below reflect the state at the time of implementation.

## 1. Objective

Establish the first end-to-end distributed-tracing path for the Enterprise AI Platform without replacing the existing metrics collection path or introducing a second telemetry collector.

The implementation was intended to:

- Instrument incoming FastAPI requests.
- Instrument outgoing HTTP calls made with Python `requests` (including calls to the model-serving endpoint when that client is used).
- Export traces using OTLP over HTTP.
- Use Grafana Alloy as the telemetry collection/forwarding layer and Grafana Tempo as the trace backend.
- Inject trace and span identifiers into application log records so logs can be correlated with traces in a later phase.
- Exclude `/metrics` from FastAPI request tracing and avoid tracing the telemetry export request itself.
- Preserve the current Prometheus metrics configuration and existing application/test behavior.

## 2. Agreed telemetry architecture

```text
FastAPI Runtime API
  ├── Incoming HTTP request spans (OpenTelemetry FastAPI instrumentation)
  ├── Outgoing requests spans (OpenTelemetry Requests instrumentation)
  └── Python log records with trace_id / span_id injected
                 |
                 | OTLP HTTP traces (localhost:4318/v1/traces)
                 v
        Grafana Alloy (OTLP receiver)
                 |
                 | OTLP gRPC (tempo:4317)
                 v
           Grafana Tempo
                 |
                 | Tempo query API (tempo:3200)
                 v
        Grafana Explore / Tempo data source
```

Related components running in the local Docker network `enterprise-ai-net`:

- **Grafana Alloy:** receives OTLP and forwards spans to Tempo.
- **Tempo:** stores traces locally in the named Docker volume `enterprise-tempo-data`.
- **Grafana:** provides Explore and the Tempo data source.
- **Prometheus:** remains the metrics backend; its scrape configuration was not changed as part of Phase 16.1.

### Key design decisions

1. **One collection/forwarding layer:** Alloy is the agreed collector/forwarder. No standalone OpenTelemetry Collector was added.
2. **Metrics path remains as-is:** the existing Prometheus configuration is retained until collection consolidation is separately planned and proven.
3. **No OTLP log-export handler:** application logs remain on stdout. `LoggingInstrumentor` injects trace context into Python log records; central log collection is the next phase.
4. **Local persistence:** Tempo uses local storage backed by a named Docker volume for this development setup. Cloud object storage and retention/cost tuning are later work.
5. **Local-only access:** Grafana, Tempo, Alloy UI, Prometheus, and the OTLP HTTP host port should remain bound to loopback for local development unless there is an explicit network-access requirement.

## 3. Files added or changed

| File | Purpose |
|---|---|
| `services/runtime-api/requirements.txt` | Adds pinned OpenTelemetry dependencies to the runtime dependency set. |
| `services/runtime-api/requirements-docker.txt` | Adds the same OpenTelemetry dependencies to the Docker runtime dependency set. |
| `services/runtime-api/app/observability/__init__.py` | Makes `observability` a Python package. |
| `services/runtime-api/app/observability/tracing.py` | Configures the tracer provider, OTLP exporter, FastAPI/Requests instrumentation, and log context injection. |
| `services/runtime-api/app/main.py` | Initializes tracing, adds trace fields to the log format, and instruments the FastAPI app. |
| `tests/test_tracing.py` | Tests endpoint selection, exporter endpoint construction, HTTP request span creation, and log trace-context injection. |
| `deployment/observability/tracing/tempo/tempo.yaml` | Tempo local configuration, including OTLP receivers and local trace storage/retention settings. |
| `deployment/observability/tracing/alloy/config.alloy` | Alloy OTLP receiver, batch processor, and Tempo exporter. |
| `deployment/observability/tracing/docker-compose.yml` | Local Tempo and Alloy services, ports, shared network, and persistent volumes. |
| `deployment/observability/grafana/provisioning/datasources/tempo.yml` | Provisions Tempo as a Grafana data source. |
| `deployment/observability/grafana/docker-compose.yml` | Host binding changed to loopback (`127.0.0.1:3000:3000`) for local-only Grafana access. |

**Working-tree caution:** `docs/troubleshooting/TROUBLESHOOTING-002-Dynamic-Model-Registry-Integration.md` was already modified before this phase and is unrelated to tracing. Do not stage or commit it as part of Phase 16.1 unless it has been reviewed separately. No commit had been made at the documented checkpoint.

## 4. Python dependencies and local environment

The Python environment used for this work was Python **3.11.9**. A project-local virtual environment was created at `.venv`; it is covered by `.gitignore`, so packages were not installed into the global Python environment.

The following pinned packages were added to both runtime requirement files:

```text
opentelemetry-api==1.45.1
opentelemetry-sdk==1.45.1
opentelemetry-exporter-otlp-proto-http==1.45.1
opentelemetry-instrumentation-fastapi==0.66b1
opentelemetry-instrumentation-requests==0.66b1
opentelemetry-instrumentation-logging==0.66b1
```

The local test environment also used:

```text
pytest==9.1.1
httpx==0.28.1
```

> Keep the versions synchronized between `requirements.txt` and `requirements-docker.txt`. The versions above are the versions used for this implementation; review compatibility before upgrading them.

### Create/use the virtual environment (PowerShell)

Run from the repository root:

```powershell
Set-Location C:\RAJESH\LEARNINGPATH\Python\Enterprise-AI-Platform

# Create only if .venv does not already exist
py -3.11 -m venv .venv

# Install the runtime Docker dependency set
.\.venv\Scripts\python.exe -m pip install -r .\services\runtime-api\requirements-docker.txt

# Install the test tools used in this local environment
.\.venv\Scripts\python.exe -m pip install pytest==9.1.1 httpx==0.28.1

# Verify dependency consistency
.\.venv\Scripts\python.exe -m pip check
```

Expected dependency check result: `No broken requirements found.` If `.venv` already exists, do not recreate it unnecessarily.

## 5. Application tracing implementation

### 5.1 `services/runtime-api/app/observability/tracing.py`

The module implements these behaviors:

- Reads `OTEL_SERVICE_NAME`; defaults to `enterprise-runtime-api` if unset.
- Prefers `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` when set.
- Otherwise derives the traces endpoint from `OTEL_EXPORTER_OTLP_ENDPOINT` by appending `/v1/traces`.
- If neither endpoint is configured, creates the tracing provider/instrumentation but does not add an OTLP exporter. This permits local trace creation without export.
- Creates a `TracerProvider` with a `service.name` resource attribute.
- Uses `OTLPSpanExporter` and `BatchSpanProcessor` when an endpoint is configured.
- Adds the exact exporter URL to `OTEL_PYTHON_REQUESTS_EXCLUDED_URLS` to prevent instrumented `requests` calls used for telemetry export from generating recursive spans. It does not exclude every request to the same host.
- Uses `LoggingInstrumentor` to inject trace context into Python logging records without setting a new logging format and without installing an OTLP log exporter.
- Uses `RequestsInstrumentor` to trace outbound HTTP requests.
- Uses `FastAPIInstrumentor` to trace inbound requests, with `/metrics` excluded by default.
- Uses a module-level provider reference to avoid initializing the provider more than once in the process.

The effective implementation is the source in `services/runtime-api/app/observability/tracing.py`; refer to that file for the full function bodies and exact regular expressions.

### 5.2 `services/runtime-api/app/main.py`

The app imports and initializes tracing:

```python
from app.observability.tracing import (
    initialize_tracing,
    instrument_fastapi_app,
)

tracer_provider = initialize_tracing()
```

The existing log format was extended with OpenTelemetry context fields:

```python
"%(asctime)s %(levelname)s %(name)s "
"trace_id=%(otelTraceID)s "
"span_id=%(otelSpanID)s "
"service=%(otelServiceName)s %(message)s"
```

After the FastAPI app and routes are defined, the app is instrumented:

```python
instrument_fastapi_app(app, tracer_provider)
```

This implementation adds context to logs; it does **not** send logs directly to Tempo or configure log shipping. The planned path for logs is stdout → Alloy → Loki in Phase 16.2.

### 5.3 Application configuration

For local host-based testing, the Runtime API was started with:

```powershell
Set-Location C:\RAJESH\LEARNINGPATH\Python\Enterprise-AI-Platform
$env:PYTHONPATH = "services/runtime-api"
$env:OTEL_SERVICE_NAME = "enterprise-runtime-api-local"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
Remove-Item Env:OTEL_EXPORTER_OTLP_TRACES_ENDPOINT -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Because `OTEL_EXPORTER_OTLP_ENDPOINT` is the base endpoint, the code derives the effective traces endpoint as:

```text
http://localhost:4318/v1/traces
```

The explicit `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` variable takes precedence when set. For a service running in a Docker container, `localhost` refers to that container itself; use the correct Alloy service/network address for a containerized Runtime API, rather than blindly reusing the host-based value.

## 6. Local Alloy and Tempo deployment

### 6.1 Docker prerequisites

Docker Desktop must be running. The services use the external Docker network `enterprise-ai-net` so they can communicate with the other locally deployed platform services.

The tracing Compose file creates/uses these named volumes:

- `enterprise-tempo-data`
- `enterprise-alloy-data`

The environment also created the following network and retained the existing local observability volumes:

- Docker network: `enterprise-ai-net`
- Prometheus volume: `enterprise-prometheus-data`
- Grafana volume: `enterprise-grafana-data`

The existing `hf_cache` volume and stopped legacy containers were left untouched.

### 6.2 Tempo configuration

File: `deployment/observability/tracing/tempo/tempo.yaml`

Key settings:

- HTTP query/API port: `3200`
- gRPC server port: `9095`
- OTLP gRPC receiver: `0.0.0.0:4317`
- OTLP HTTP receiver: `0.0.0.0:4318`
- Local trace storage and WAL under `/var/tempo`
- Local-development block retention configured to 24 hours, with compaction-related settings as captured in the file

The config was validated with Tempo 3.1.1 using:

```powershell
docker compose -f .\deployment\observability\tracing\docker-compose.yml run --rm --no-deps --entrypoint /tempo tempo --config.file=/etc/tempo/tempo.yaml --config.verify=true
```

Expected result: command exits with code `0`.

### 6.3 Alloy configuration

File: `deployment/observability/tracing/alloy/config.alloy`

The pipeline is:

1. `otelcol.receiver.otlp "default"` listens on ports `4317` (gRPC) and `4318` (HTTP).
2. `otelcol.processor.batch "default"` batches trace data.
3. `otelcol.exporter.otlp "tempo"` forwards traces to `tempo:4317` with TLS disabled for the internal local Docker network.

The config was validated with:

```powershell
docker compose -f .\deployment\observability\tracing\docker-compose.yml run --rm --no-deps --entrypoint /bin/alloy alloy validate /etc/alloy/config.alloy
```

Expected result: Alloy validation succeeds with exit code `0`.

### 6.4 Compose deployment and service health

The tracing Compose file uses:

- `grafana/tempo:3.1.1`
- `grafana/alloy:v1.21.2`
- The external Docker network `enterprise-ai-net`
- Loopback-bound host ports for Tempo query API (`127.0.0.1:3200`) and Alloy UI/health (`127.0.0.1:12345`) and OTLP HTTP (`127.0.0.1:4318`)

Validate and start services:

```powershell
docker compose -f .\deployment\observability\tracing\docker-compose.yml config
docker compose -f .\deployment\observability\tracing\docker-compose.yml up -d
```

Health checks confirmed:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:3200/ready
Invoke-WebRequest -UseBasicParsing http://localhost:12345/-/healthy
```

Observed successful responses were HTTP 200; Tempo returned `ready`, and Alloy reported that all components were healthy.

## 7. Grafana Tempo data source

File: `deployment/observability/grafana/provisioning/datasources/tempo.yml`

The provisioned data source has:

- Name: `Tempo`
- UID: `tempo`
- Type: `tempo`
- URL: `http://tempo:3200`
- `editable: false`

The URL is the Tempo container/service name because Grafana and Tempo are attached to `enterprise-ai-net`; it should not be changed to `localhost:3200` inside Grafana's container.

Grafana was deployed through the existing Compose file:

```powershell
docker compose -f .\deployment\observability\grafana\docker-compose.yml up -d
```

Grafana's host binding was changed to:

```yaml
ports:
  - "127.0.0.1:3000:3000"
```

This limits host access to the local machine. The Grafana health endpoint returned HTTP 200 after startup. The Tempo data source was available in Grafana, and Explore was used to query the traces.

**Security note:** The local Compose configuration used the development credentials `admin` / `enterpriseai`. Do not reuse these credentials in a shared or production environment. Change them before any wider exposure.

## 8. Validation procedure and results

### 8.1 Syntax/import validation

The tracing module and app imports were checked successfully, and the FastAPI app reported 11 routes at the checkpoint.

### 8.2 Unit tests for tracing

File: `tests/test_tracing.py`

Four focused tests were added and passed. They cover:

1. An explicit traces endpoint takes precedence over the base OTLP endpoint.
2. A base OTLP endpoint is converted to a `/v1/traces` endpoint.
3. A request to the health endpoint produces a server span using an in-memory exporter in the test.
4. Python log records receive trace/span context fields.

### 8.3 Full runtime test suite

Run from the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "services/runtime-api"
.\.venv\Scripts\python.exe -m pytest -q .\tests
```

Recorded result:

```text
90 passed, 3 skipped, 3 warnings in 2.16s
```

The warnings were existing/deprecation-related warnings involving Starlette's `TestClient`/`httpx` recommendation and uses of `HTTP_422_UNPROCESSABLE_ENTITY`. They were not tracing test failures.

### 8.4 Evaluation test suite

```powershell
$env:PYTHONPATH = "."
.\.venv\Scripts\python.exe -m pytest -q .\evaluation\tests
```

Recorded result:

```text
36 passed in 0.55s
```

### 8.5 Git whitespace validation

```powershell
git diff --check
```

Recorded result: no output, meaning no whitespace errors were reported.

### 8.6 End-to-end trace check

With Tempo and Alloy running, the Runtime API was started on the host and the following endpoints were requested successfully:

- `http://127.0.0.1:8000/health` — HTTP 200
- `http://127.0.0.1:8000/models` — HTTP 200

Tempo's search API was queried for the recent five minutes:

```powershell
$end = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$start = $end - 300
$result = Invoke-RestMethod -Uri "http://localhost:3200/api/search?start=$start&end=$end&limit=20"
$result | ConvertTo-Json -Depth 8
```

Tempo returned traces for both endpoints, with service name `enterprise-runtime-api-local`. The observed trace IDs included:

- `/health`: `bbfe688661e426b1262bb4911fc0ff25`
- `/models`: `3f2a597f68089a68fb2c543a8b48238d`

These IDs are examples from the validation session; new requests will generate different IDs.

Grafana Explore was also verified with the TraceQL query:

```traceql
{ resource.service.name = "enterprise-runtime-api-local" }
```

The `/health` and `/models` traces were visible in Grafana. This verifies the end-to-end path from the instrumented API through Alloy into Tempo and the Grafana query UI.

### 8.7 Prometheus and Grafana checks

Prometheus was started using the existing Compose deployment. Its readiness endpoint returned HTTP 200 and the `up` query returned `1` for the Prometheus self-scrape. Some existing targets (`enterprise-runtime-api:8000`, `enterprise-evaluation-metrics:9108`, and `enterprise-dcgm-exporter:9400`) showed `up=0` in the local environment because those target containers were not running under those target names at the time of the test; the Runtime API was running directly on the Windows host.

This was recorded as a local test-environment condition, not fixed by changing the Prometheus scrape configuration. The Prometheus configuration was intentionally left unchanged in Phase 16.1.

## 9. Troubleshooting log

### Issue 1 — Python environment did not have OpenTelemetry packages

**Symptom:** No OpenTelemetry packages were installed in the global Python interpreter, and a project virtual environment did not exist.

**Resolution:** Created the repository-local `.venv`, installed the Docker runtime requirements and test tools, and checked package consistency with `pip check`.

**Lesson:** Use the repository virtual environment for tracing work rather than modifying global Python packages.

### Issue 2 — Tempo rejected an initial configuration field

**Symptom:** Tempo config verification initially failed because a `compactor` field in the draft config was not accepted by the selected Tempo 3.1.1 configuration schema.

**Resolution:** Updated the configuration to use the supported Tempo 3 scheduler/worker compaction-retention configuration, then re-ran `--config.verify=true` successfully.

**Lesson:** Validate the configuration against the exact pinned container version; do not assume fields from another Tempo release are compatible.

### Issue 3 — Alloy configuration needed independent validation

**Action:** Ran Alloy's built-in `validate` command inside the Compose service, with dependencies disabled for the one-off validation container.

**Result:** The configuration validated successfully with exit code `0`.

**Lesson:** Validate configuration files before relying on container startup logs alone.

### Issue 4 — Grafana logged Tempo/Prometheus DNS errors during startup

**Symptom:** Grafana logged connection/DNS errors while dependent observability services had not yet been started or were still starting.

**Resolution:** Started Tempo, Alloy, and Prometheus on the shared `enterprise-ai-net` network and rechecked service health. Later Grafana log inspection did not show new matching errors in the most recent 30-second window, and the Tempo data source/Explore queries worked.

**Lesson:** When investigating startup errors, correlate the log timestamps with container startup order and verify current health before treating historical startup messages as ongoing failures.

### Issue 5 — Local Prometheus targets showed `up=0`

**Symptom:** The Prometheus query showed `up=0` for Runtime API, evaluation metrics, and DCGM exporter targets, while Prometheus itself was `up=1`.

**Cause at the checkpoint:** Those target containers were not running locally using the configured Docker service names. The Runtime API was started on the Windows host at `127.0.0.1:8000`, which is not the same network address as `enterprise-runtime-api:8000` from inside the Prometheus container.

**Resolution/status:** No scrape configuration change was made as part of Phase 16.1. Track this as a local deployment topology/target availability issue if those metrics need to be validated in the current local stack.

**Lesson:** `localhost` inside a container refers to the container itself, and service-name DNS works only for reachable services on the relevant Docker network.

### Issue 6 — Grafana port should not be exposed to every host interface

**Action:** Changed Grafana's Compose port mapping to `127.0.0.1:3000:3000` and redeployed it.

**Validation:** The container showed the loopback-bound mapping, Grafana health later returned HTTP 200, and Explore was accessible locally.

**Lesson:** Default to loopback-only access for local developer dashboards and telemetry endpoints unless remote access has been explicitly designed and secured.

### Issue 7 — Regression/deprecation warnings remained

**Symptom:** The runtime test suite passed but emitted three warnings related to Starlette/httpx and deprecated HTTP 422 status naming.

**Resolution/status:** They were not changed as part of tracing implementation, because they were not test failures and changing unrelated test/application APIs would broaden this phase's scope.

**Lesson:** Record pre-existing/deprecation warnings separately from feature regressions; handle them in a dedicated cleanup when appropriate.

## 10. Current local services and ports

| Component | Local address / port | Purpose |
|---|---|---|
| Runtime API (host process) | `http://127.0.0.1:8000` | Test the instrumented API. |
| Grafana | `http://127.0.0.1:3000` | Dashboards and Explore; local-only binding. |
| Prometheus | `http://127.0.0.1:9090` | Existing metrics backend. |
| Tempo | `http://127.0.0.1:3200` | Trace query/readiness API. |
| Alloy UI/health | `http://127.0.0.1:12345` | Alloy UI and component health. |
| Alloy OTLP HTTP | `http://127.0.0.1:4318` | Local Runtime API trace export endpoint base; exporter sends to `/v1/traces`. |
| Alloy OTLP gRPC | container port `4317` | OTLP receiver; forwarded internally to Tempo. |
| Tempo OTLP gRPC | container port `4317` | Internal Alloy-to-Tempo trace ingestion. |

### Check service status

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Stop the local observability stack without deleting data

From the repository root, stop each Compose project separately:

```powershell
docker compose -f .\deployment\observability\tracing\docker-compose.yml down
docker compose -f .\deployment\observability\prometheus\docker-compose.yml down
docker compose -f .\deployment\observability\grafana\docker-compose.yml down
```

These commands do not use `-v`, so named volumes should be preserved. They do not stop the host-run FastAPI `uvicorn` process; stop that separately with `Ctrl+C` in its terminal. Do not use `down -v` unless deletion of local telemetry data is intended.

To start the stack again, bring up the existing network/Prometheus and tracing dependencies first, then Grafana:

```powershell
docker compose -f .\deployment\observability\prometheus\docker-compose.yml up -d
docker compose -f .\deployment\observability\tracing\docker-compose.yml up -d
docker compose -f .\deployment\observability\grafana\docker-compose.yml up -d
```

If a compose project depends on an external `enterprise-ai-net` network and Docker says it does not exist, recreate the network only if it is truly absent:

```powershell
docker network create enterprise-ai-net
```

## 11. Working-tree hygiene and commit readiness

At the documented checkpoint, `git status --short` showed these tracing-related changes:

```text
 M deployment/observability/grafana/docker-compose.yml
 M services/runtime-api/app/main.py
 M services/runtime-api/requirements-docker.txt
 M services/runtime-api/requirements.txt
?? deployment/observability/grafana/provisioning/datasources/tempo.yml
?? deployment/observability/tracing/
?? services/runtime-api/app/observability/
?? tests/test_tracing.py
```

It also showed a pre-existing unrelated modification:

```text
 M docs/troubleshooting/TROUBLESHOOTING-002-Dynamic-Model-Registry-Integration.md
```

Before committing Phase 16.1, review the diffs and stage only the intended tracing files. Do not use `git add .`.

Suggested review commands:

```powershell
git status --short
git diff --check
git diff -- services/runtime-api/app/main.py services/runtime-api/requirements.txt services/runtime-api/requirements-docker.txt deployment/observability/grafana/docker-compose.yml
git diff --no-index NUL services/runtime-api/app/observability/tracing.py
```

For newly created files, open/review them directly or use `git diff --no-index` as appropriate. Do not stage the unrelated troubleshooting document without separate review.

## 12. Completion summary

Phase 16.1 is implemented and locally validated at the recorded checkpoint:

- OpenTelemetry dependencies were pinned in both runtime dependency files.
- FastAPI inbound tracing and outbound `requests` tracing were configured.
- Trace/span context was added to Python log records while keeping logs on stdout.
- `/metrics` and telemetry exporter requests were excluded from unnecessary tracing.
- Tempo and Alloy configuration passed their built-in validation commands.
- Alloy and Tempo started and returned healthy/readiness responses.
- Grafana Tempo data source and Explore trace query were verified.
- Real traces from `/health` and `/models` were found in Tempo and viewed in Grafana.
- Runtime tests: **90 passed, 3 skipped**; evaluation tests: **36 passed**.
- `git diff --check` completed without reported errors.
- Prometheus scrape configuration was not changed.
- No Git commit had been made at this checkpoint.

## 13. Follow-on work — Phase 16.2: Centralized logging with Loki

The planned next phase is to implement centralized logs using the agreed path:

```text
Runtime API stdout / container logs
            |
            v
      Grafana Alloy
            |
            v
           Loki
            |
            v
 Grafana Explore / log dashboards
```

Proposed focus for Phase 16.2:

1. Inspect the current log format, Docker runtime behavior, and existing Alloy configuration before making changes.
2. Add Loki with local persistent storage for the development environment.
3. Extend Alloy to collect/forward logs into Loki without duplicating collectors.
4. Preserve the trace/span IDs added in Phase 16.1 and validate that they appear in logs.
5. Provision Loki in Grafana and validate log queries and navigation/correlation with traces.
6. Add targeted config/tests or repeatable smoke checks, then rerun runtime and evaluation regression suites.
7. Keep S3-backed Loki storage, retention tuning, and cloud cost optimization for a separately validated step rather than mixing them into the local foundation.

## 14. Quick diagnostic checklist

If traces stop appearing, check these in order:

1. **Application configuration:** confirm `OTEL_SERVICE_NAME` and the effective OTLP endpoint. For the host-run API, ensure `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318` and that the explicit traces endpoint is either correctly set or unset as intended.
2. **Runtime API:** send a request to `/health`, then review the Uvicorn/application logs for initialization or export errors.
3. **Alloy health:** request `http://localhost:12345/-/healthy` and check `docker logs --tail 100 enterprise-alloy`.
4. **Tempo readiness:** request `http://localhost:3200/ready` and check `docker logs --tail 100 enterprise-tempo`.
5. **Container network:** verify Alloy and Tempo are both attached to `enterprise-ai-net`, and that Alloy exports to `tempo:4317` rather than an incorrect localhost address.
6. **Tempo search:** query recent traces using the Tempo API command in Section 8.6; verify the selected time window includes the request time.
7. **Grafana data source:** confirm the Tempo URL is `http://tempo:3200` from Grafana's container network and that the data source test succeeds.
8. **Tests/config validation:** rerun the four focused tracing tests, full runtime suite, evaluation suite, Tempo config verification, Alloy config validation, and `git diff --check`.

---

**End of Phase 16.1 implementation record.**
