# Sprint 8.2 — TGI GPU Troubleshooting & LLM Ops Learning

## Objective

Validate the Hugging Face Text Generation Inference (TGI) integration for the Enterprise AI Runtime API and document the troubleshooting performed when the TGI container failed to start.

This sprint provides practical LLM Ops learning around:

- Dockerized inference servers
- TGI
- GPU/CPU requirements
- Docker Desktop + WSL2
- NVIDIA container runtime
- GPU passthrough
- Triton/CUDA initialization
- Runtime API → inference server integration
- Infrastructure vs application troubleshooting

---

## 1. Current Architecture

```text
Client
  |
  v
Runtime API (FastAPI)
  |
  v
TGI Client
  |
  v
Hugging Face TGI
  |
  v
Model Runtime
  |
  +--> Triton / CUDA
  |
  +--> GPU
```

Runtime API:

```text
localhost:8000
```

TGI was configured separately on:

```text
localhost:8080
```

---

## 2. Sprint 8.1 — TGI Client

A dedicated `TGIClient` was introduced so the Runtime API does not directly depend on TGI implementation details.

Responsibilities include:

- Store the TGI base URL.
- Send generation requests.
- Pass generation parameters.
- Handle HTTP responses.
- Return generated text.

Example interface:

```python
class TGIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.7,
    ) -> str:
        ...
```

Validation performed:

```powershell
findstr requests requirements-docker.txt
```

Expected dependency:

```text
requests==2.32.5
```

Python syntax validation:

```powershell
python -m py_compile app/clients/tgi_client.py
```

Import validation:

```powershell
python -c "from app.clients.tgi_client import TGIClient; print('TGIClient import OK')"
```

Successful result:

```text
TGIClient import OK
```

### Learning

The client abstraction allows the Runtime API to support multiple inference engines later:

```text
TGIClient
VLLMClient
OllamaClient
OpenAIClient
```

---

# 3. TGI Container

The TGI image used was:

```text
ghcr.io/huggingface/text-generation-inference:latest
```

Container:

```text
tgi-smollm
```

The container eventually entered:

```text
Exited (1)
```

Inspection:

```powershell
docker ps -a
```

---

# 4. TGI Startup Failure

The critical TGI error was:

```text
RuntimeError: 0 active drivers ([]). There should only be one. rank=0
```

followed by:

```text
ERROR text_generation_launcher: Shard 0 failed to start
```

and:

```text
Error: ShardCannotStart
```

The traceback entered the Triton/Mamba execution path.

### Interpretation

TGI attempted to initialize the model execution backend, but no active accelerator driver was available.

Therefore the TGI shard could not start.

### Important lesson

> A healthy Docker daemon does not mean that a GPU is available to a container.

---

# 5. Host GPU Validation

Command:

```powershell
nvidia-smi
```

Result:

```text
nvidia-smi : The term 'nvidia-smi' is not recognized...
```

This means `nvidia-smi` was not available on the Windows host.

A Docker-level GPU test was performed next.

---

# 6. Docker GPU Passthrough Test

Command:

```powershell
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

The CUDA image downloaded successfully, but container initialization failed with:

```text
nvidia-container-cli: initialization error:
WSL environment detected but no adapters were found
```

### Conclusion

Docker has an NVIDIA runtime configured, but no NVIDIA adapter is exposed to the WSL/Docker environment.

This distinction is important:

```text
NVIDIA runtime installed
        !=
NVIDIA GPU available
```

---

# 7. WSL2 Validation

Command:

```powershell
wsl --status
```

Observed:

```text
Default Distribution: docker-desktop
Default Version: 2
```

Version:

```powershell
wsl --version
```

Observed:

```text
WSL version: 2.3.26.0
Kernel version: 5.15.167.4-1
WSLg version: 1.0.65
MSRDC version: 1.2.5620
Direct3D version: 1.611.1-81528511
DXCore version: 10.0.26100.1-240331-1435.ge-release
Windows version: 10.0.26200.8875
```

### Learning

WSL2 is enabled and functioning.

Therefore the issue is not simply a WSL1/WSL2 configuration problem.

---

# 8. Docker Engine Validation

Command:

```powershell
docker info
```

Important observed values:

```text
Server Version: 27.4.0
Operating System: Docker Desktop
OSType: linux
Architecture: x86_64
Kernel Version: 5.15.167.4-microsoft-standard-WSL2
CPUs: 8
Total Memory: 2.819GiB
```

Runtime information:

```text
Runtimes: runc io.containerd.runc.v2 nvidia
Default Runtime: runc
```

### Important observation

Docker reports an `nvidia` runtime.

However, the CUDA test reports:

```text
no adapters were found
```

Therefore an NVIDIA runtime being present does not prove that an NVIDIA GPU is available.

---

# 9. Final Root Cause

The troubleshooting chain is:

```text
TGI starts
   |
   v
Model initialization
   |
   v
Triton / CUDA backend
   |
   v
Needs accelerator driver
   |
   v
No active driver
   |
   v
0 active drivers
   |
   v
Shard 0 fails
   |
   v
TGI exits with code 1
```

The evidence indicates that:

- Docker daemon is healthy.
- Runtime API container is healthy.
- WSL2 is enabled.
- Docker has an NVIDIA runtime.
- No NVIDIA adapter is exposed to WSL/Docker.
- TGI cannot initialize the required accelerator backend.

---

# 10. What Was Not the Root Cause

### Not the Runtime API Docker build

The Runtime API image built successfully and the container ran successfully.

### Not the TGI client Python import

The client successfully passed:

```text
python -m py_compile app/clients/tgi_client.py
```

and:

```text
TGIClient import OK
```

### Not a Docker daemon outage

`docker info` successfully returned server information.

### Not WSL1

The environment is explicitly using:

```text
Default Version: 2
```

### Not simply a missing NVIDIA runtime

Docker reports:

```text
Runtimes: runc io.containerd.runc.v2 nvidia
```

The actual issue is that no NVIDIA adapter is available to the WSL/Docker environment.

---

# 11. Why Rebuilding TGI Will Not Fix This

The failure occurs during runtime initialization:

```text
0 active drivers
```

Therefore repeatedly changing the application image or rebuilding the TGI image is unlikely to solve the underlying issue.

The infrastructure requirement would be:

```text
NVIDIA GPU
    +
NVIDIA driver
    +
WSL GPU support
    +
Docker GPU passthrough
```

That requirement is not currently available on this development machine.

---

# 12. LLM Ops Learning — Separate Application and Inference Runtime

Our architecture intentionally separates:

```text
Application
    |
    v
Runtime API
    |
    v
Inference Client
    |
    v
Inference Server
```

This allows the same Runtime API to work with different inference engines:

```text
Runtime API
    |
    +---- TGI
    |
    +---- vLLM
    |
    +---- Ollama
    |
    +---- OpenAI-compatible endpoint
```

### Key design principle

> Separate inference orchestration from inference implementation.

This makes the platform easier to replace, test and operate.

---

# 13. Next Inference Engines

## TGI

Status:

```text
TGI client integration       DONE
TGI deployment attempt      DONE
GPU validation              DONE
Root-cause analysis         DONE
Troubleshooting document    DONE
GPU-backed TGI execution    NOT AVAILABLE ON CURRENT MACHINE
```

TGI remains documented as an inference-server integration, but GPU execution requires an appropriate accelerator environment.

---

## vLLM

Next major inference-engine learning target.

Topics:

- vLLM architecture
- Continuous batching
- KV cache
- GPU inference
- OpenAI-compatible API
- Model serving
- Concurrency
- Throughput vs latency
- Production inference

Target:

```text
Runtime API
     |
     v
VLLMClient
     |
     v
vLLM OpenAI-compatible endpoint
```

---

## Ollama

Ollama will be used for local inference where appropriate.

Topics:

- Local model serving
- Model lifecycle
- Pull/run models
- REST API
- OpenAI-compatible interaction
- CPU-friendly local development

Target:

```text
Runtime API
     |
     v
OllamaClient
     |
     v
Ollama
     |
     v
Local LLM
```

---

# 14. Recommended Runtime Abstraction

Long-term design:

```text
                  Runtime API
                      |
               Inference Layer
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
    TGIClient      VLLMClient     OllamaClient
       |              |              |
       v              v              v
      TGI            vLLM          Ollama
```

The application should not contain engine-specific business logic.

This is an important LLM Ops engineering principle:

> The Runtime API should orchestrate inference without being tightly coupled to a particular serving engine.

---

# 15. Troubleshooting Checklist

When an inference server fails:

### Step 1 — Check container state

```powershell
docker ps -a
```

### Step 2 — Check logs

```powershell
docker logs <container-name>
```

### Step 3 — Check Docker daemon

```powershell
docker info
```

### Step 4 — Check WSL

```powershell
wsl --status
wsl --version
```

### Step 5 — Check host GPU

```powershell
nvidia-smi
```

### Step 6 — Check Docker GPU passthrough

```powershell
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### Step 7 — Classify the failure

Determine whether the failure is:

```text
Application
Model
Python dependency
Container
Inference runtime
GPU driver
GPU passthrough
Network
Configuration
```

### Step 8 — Fix the correct layer

Do not modify application code when the failure is demonstrably in the infrastructure layer.

---

# 16. Diagnostic Matrix

| Test | Result | Meaning |
|---|---|---|
| `docker ps` | Runtime API running | Application container healthy |
| `docker info` | Server information available | Docker daemon healthy |
| `wsl --status` | Version 2 | WSL2 enabled |
| `wsl --version` | 2.3.26.0 | WSL installed |
| `nvidia-smi` | Not recognized | No usable host NVIDIA CLI detected |
| Docker CUDA test | No adapters found | GPU not exposed to WSL/Docker |
| TGI logs | `0 active drivers` | Accelerator initialization failed |
| TGI status | Exit code 1 | TGI shard startup failed |

---

# 17. Sprint 8.2 Acceptance Criteria

- [x] TGI client created
- [x] HTTP request structure implemented
- [x] `requests` dependency verified
- [x] Python syntax/import validation completed
- [x] TGI container startup attempted
- [x] TGI failure captured
- [x] Docker GPU capability tested
- [x] WSL2 status validated
- [x] Docker runtime information collected
- [x] Root cause identified
- [x] Troubleshooting documented
- [ ] GPU-backed TGI execution — requires NVIDIA-capable environment

---

# 18. Sprint 8.2 Outcome

The Sprint 8.2 troubleshooting objective is complete for the current development environment.

The result:

```text
Runtime API       → HEALTHY
Docker            → HEALTHY
WSL2              → ENABLED
TGI Client        → HEALTHY
TGI startup       → FAILED
GPU passthrough   → UNAVAILABLE
Root cause        → IDENTIFIED
```

The key LLM Ops lesson is:

> Diagnose the layer that is actually failing instead of repeatedly changing application code.

---

# 19. Next Step

Proceed to:

```text
Sprint 8.3
vLLM + OpenAI-compatible inference
```

Then:

```text
Sprint 8.4
Ollama + local inference
```

Then:

```text
Kubernetes
      ↓
KServe
      ↓
Prometheus / Grafana
      ↓
CI/CD
      ↓
Production LLM Ops workflow
```

---

# 20. Interview Preparation — TGI Failure Scenario

### Question

> A TGI container starts but the model shard fails with `0 active drivers`. How would you troubleshoot it?

### Answer

1. Check the container status.
2. Inspect the TGI logs.
3. Identify whether the error is application, model, runtime or infrastructure related.
4. Check host GPU availability using `nvidia-smi`.
5. Check WSL2 status/version.
6. Test Docker GPU passthrough using a CUDA container.
7. Check NVIDIA runtime/driver configuration.
8. Compare the inference server's hardware requirements with the available environment.
9. Avoid modifying application code when the failure is in the infrastructure layer.
10. Move the workload to an appropriate GPU environment or use an inference engine suitable for the current hardware.

### Core takeaway

A successful Docker build or a healthy Docker daemon does not guarantee that GPU workloads can run.

---

## Sprint Tracking

**Sprint:** 8.2  
**Focus:** TGI inference-server validation and GPU troubleshooting  
**Status:** Troubleshooting/documentation complete  
**Next:** vLLM + OpenAI-compatible inference
