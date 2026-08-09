# Sprint 8.3 --- vLLM CPU Runtime Deployment & Troubleshooting

## Objective

Deploy a vLLM inference server using Docker, validate the runtime with a
small model, understand the startup lifecycle, and document the failure
encountered during CPU KV-cache initialization.

## Environment

-   Host: Windows 10
-   WSL: 2.3.26.0
-   WSL kernel: 5.15.167.4
-   Docker Desktop: 27.4.0
-   Docker Linux context: `desktop-linux`
-   CPU: 8 logical CPUs
-   Docker memory during final test: approximately 3.83 GiB
-   GPU: NVIDIA GPU was not available in the local environment
-   vLLM image: `vllm/vllm-openai-cpu:latest-x86_64`
-   vLLM version: `0.26.0`
-   Model: `Qwen/Qwen3-0.6B`

------------------------------------------------------------------------

## 1. Initial Environment Validation

### Python

``` powershell
python --version
pip --version
```

Observed:

``` text
Python 3.11.9
pip 26.2
```

These are the project virtual-environment versions and are separate from
the Python runtime packaged inside the vLLM container.

### Docker resources

``` powershell
docker info | findstr /I "CPUs Memory"
```

Final test:

``` text
CPUs: 6
Total Memory: 3.829GiB
```

### WSL resources

``` powershell
wsl -d docker-desktop -- free -h
wsl -d docker-desktop -- nproc
wsl -d docker-desktop -- uname -a
```

The WSL/Docker environment was intentionally configured during
troubleshooting with a limited memory allocation. The final Docker
memory available to the daemon was approximately 3.83 GiB.

------------------------------------------------------------------------

## 2. GPU Validation

### Check NVIDIA GPU

``` powershell
nvidia-smi
```

Result:

``` text
nvidia-smi : The term 'nvidia-smi' is not recognized...
```

A CUDA container test was also attempted. Docker reported:

``` text
WSL environment detected but no adapters were found
```

### Conclusion

The local machine could not provide a usable NVIDIA GPU to Docker.

Therefore, the exercise was moved to the vLLM CPU image rather than
spending the sprint troubleshooting unavailable GPU hardware.

------------------------------------------------------------------------

## 3. Pull the vLLM CPU Image

``` powershell
docker pull vllm/vllm-openai-cpu:latest-x86_64
```

Validation:

``` powershell
docker images | findstr /I "vllm"
```

Observed:

``` text
vllm/vllm-openai-cpu    latest-x86_64
```

The image occupied several GB of local disk space.

------------------------------------------------------------------------

## 4. Verify vLLM Version

The initial attempts using:

``` powershell
vllm --version
```

and:

``` powershell
docker run --rm vllm/vllm-openai-cpu:latest-x86_64 vllm --version
```

were not valid for this image/CLI combination.

The reliable check was:

``` powershell
docker run --rm --entrypoint python `
  vllm/vllm-openai-cpu:latest-x86_64 `
  -c "import vllm; print(vllm.__version__)"
```

Result:

``` text
0.26.0
```

------------------------------------------------------------------------

# 5. Start the vLLM CPU Runtime

The final test used:

``` powershell
docker run --rm `
  --name vllm-cpu `
  --security-opt seccomp=unconfined `
  --cap-add SYS_NICE `
  --shm-size=1g `
  -p 8001:8000 `
  -e VLLM_CPU_KVCACHE_SPACE=0 `
  vllm/vllm-openai-cpu:latest-x86_64 `
  Qwen/Qwen3-0.6B `
  --dtype=bfloat16
```

## Important options

  -------------------------------------------------------------------------
  Option                                Purpose
  ------------------------------------- -----------------------------------
  `--name vllm-cpu`                     Predictable container name

  `--security-opt seccomp=unconfined`   Relaxed seccomp profile for the CPU
                                        runtime

  `--cap-add SYS_NICE`                  Allows required process/thread
                                        scheduling behavior

  `--shm-size=1g`                       Shared memory for multiprocessing

  `-p 8001:8000`                        Host port 8001 → container port
                                        8000

  `VLLM_CPU_KVCACHE_SPACE=0`            Avoids explicitly reserving a fixed
                                        CPU KV-cache space

  `Qwen/Qwen3-0.6B`                     Model selected for the test

  `--dtype=bfloat16`                    Requested model data type
  -------------------------------------------------------------------------

------------------------------------------------------------------------

# 6. What Worked

The startup logs confirmed that vLLM successfully:

### 6.1 Started

``` text
version 0.26.0
```

### 6.2 Selected the model

``` text
model Qwen/Qwen3-0.6B
```

### 6.3 Selected the CPU backend

``` text
device_config=cpu
```

### 6.4 Resolved the model architecture

``` text
Resolved architecture: Qwen3ForCausalLM
```

### 6.5 Downloaded the model

The Qwen3-0.6B model was downloaded successfully.

### 6.6 Loaded the weights

The logs showed successful checkpoint/weight loading.

### 6.7 Performed compilation and warm-up

The runtime reached:

``` text
Warming up model for the compilation...
```

and later:

``` text
Warming up done.
```

This is important: the failure did **not** happen during initial
container startup or model download.

------------------------------------------------------------------------

# 7. Warning Observed: oneDNN Fallback

The runtime reported:

``` text
Failed to create oneDNN linear, fallback to torch linear.
```

### Interpretation

This indicates that a oneDNN optimized path was not used and the runtime
fell back to the PyTorch linear implementation.

It was **not the final root cause**, because vLLM continued to:

-   load the model,
-   compile,
-   warm up,
-   and proceed toward KV-cache initialization.

------------------------------------------------------------------------

# 8. Warning Observed: Shared Memory Broadcast

During compilation/warm-up, the logs included messages similar to:

``` text
No available shared memory broadcast block found in 60 seconds.
```

The runtime nevertheless progressed and eventually completed warm-up.

Therefore this was treated as a performance/startup warning rather than
the final failure.

------------------------------------------------------------------------

# 9. Critical Evidence: Memory Pressure

The most important evidence appeared around model loading.

The runtime reported approximately:

``` text
Checkpoint size: 1.40 GiB
Available RAM: 0.67 GiB
```

and:

``` text
Model loading took 0.67 GiB
```

This showed that very little memory remained for subsequent
inference-engine initialization.

------------------------------------------------------------------------

# 10. Final Failure: KV Cache Initialization

The final failure occurred while vLLM was initializing the KV cache.

The important messages were:

``` text
Explicitly set (0.0/3.83) GiB for KV cache on node 0.
```

followed by:

``` text
ValueError: No available memory for the cache blocks.
```

The traceback showed the failure during KV-cache
initialization/checking.

## Root Cause

**Insufficient available memory in the Docker/WSL environment for
KV-cache allocation after the model and runtime had consumed the
available memory.**

### Memory flow

``` text
Docker/WSL memory
       |
       +-- OS / container overhead
       |
       +-- Python + vLLM runtime
       |
       +-- model weights
       |
       +-- PyTorch / compilation
       |
       +-- warm-up / temporary allocations
       |
       +-- KV cache
       |
       X  insufficient memory
```

------------------------------------------------------------------------

# 11. Why the Model Could Load but the Server Could Not Start

This is an important LLM Ops concept.

A model being small enough to load does **not** mean that the inference
server has enough memory to serve requests.

The runtime needs memory for:

1.  Model weights
2.  Framework/runtime objects
3.  Compilation
4.  Temporary buffers
5.  KV cache
6.  Request processing
7.  Concurrent sequences
8.  Shared-memory/multiprocessing operations

Therefore:

``` text
Model fits in memory
        ≠
Inference server can serve the model
```

------------------------------------------------------------------------

# 12. Troubleshooting Performed

## Step 1 --- Validate Docker

``` powershell
docker info | findstr /I "CPUs Memory"
```

Confirmed the memory limit.

## Step 2 --- Validate WSL

``` powershell
wsl -d docker-desktop -- free -h
```

Confirmed the WSL memory allocation.

## Step 3 --- Validate GPU

``` powershell
nvidia-smi
```

Confirmed no usable NVIDIA GPU was available.

## Step 4 --- Pull CPU vLLM image

``` powershell
docker pull vllm/vllm-openai-cpu:latest-x86_64
```

Successful.

## Step 5 --- Verify vLLM

``` powershell
docker run --rm --entrypoint python `
  vllm/vllm-openai-cpu:latest-x86_64 `
  -c "import vllm; print(vllm.__version__)"
```

Successful:

``` text
0.26.0
```

## Step 6 --- Start Qwen3-0.6B

The runtime started and progressed through model loading and warm-up.

## Step 7 --- Investigate memory

The logs showed extremely limited memory remaining.

## Step 8 --- Investigate KV cache

The final error identified cache-block allocation as the failure point.

## Step 9 --- Stop further CPU tuning

Because the host remained resource-constrained, the troubleshooting was
intentionally stopped.

------------------------------------------------------------------------

# 13. Why We Stopped

Continuing to change small vLLM parameters would not address the
fundamental constraint:

``` text
Available runtime memory < memory required for model + inference infrastructure
```

The goal of the sprint was to learn:

-   containerized inference,
-   vLLM startup,
-   runtime lifecycle,
-   model loading,
-   KV cache,
-   resource troubleshooting,
-   and operational decision making.

Those objectives were achieved.

Therefore:

> Sprint 8.3 is closed as a successful troubleshooting/learning
> exercise, even though the final CPU serving endpoint was not brought
> to a healthy state.

------------------------------------------------------------------------

# 14. Useful Diagnostic Commands

### Containers

``` powershell
docker ps
docker ps -a
```

### vLLM image

``` powershell
docker images | findstr /I "vllm"
```

### Docker resources

``` powershell
docker info | findstr /I "CPUs Memory"
```

### WSL resources

``` powershell
wsl -d docker-desktop -- free -h
wsl -d docker-desktop -- nproc
```

### Stop test container

``` powershell
docker stop vllm-cpu
```

### Force-remove test container

``` powershell
docker rm -f vllm-cpu
```

------------------------------------------------------------------------

# 15. LLM Ops Lessons

## Lesson 1 --- Always inspect the complete startup lifecycle

``` text
Container
   ↓
Runtime
   ↓
Model resolution
   ↓
Model download
   ↓
Weight loading
   ↓
Compilation
   ↓
Warm-up
   ↓
KV cache
   ↓
API readiness
```

A failure at each stage has a different troubleshooting path.

## Lesson 2 --- Read logs chronologically

The first warning is not necessarily the root cause.

In this test:

``` text
oneDNN fallback
        ↓
shared-memory warning
        ↓
model loading
        ↓
warm-up
        ↓
KV-cache failure
```

The final KV-cache error was the decisive failure.

## Lesson 3 --- Capacity planning is part of LLM Ops

For production inference, evaluate:

-   RAM
-   VRAM
-   model size
-   dtype
-   context length
-   KV cache
-   concurrency
-   batching
-   CPU/GPU utilization

## Lesson 4 --- Know when to stop troubleshooting

Good operations engineering is not endless trial-and-error.

When evidence points to a hardware/resource limitation:

``` text
Collect evidence
      ↓
Identify bottleneck
      ↓
Document
      ↓
Escalate / move environment
```

------------------------------------------------------------------------

# 16. Next vLLM Exercise

The next vLLM exercise should be performed on a GPU-capable environment.

Target workflow:

``` text
Client
  |
  v
OpenAI-compatible API
  |
  v
vLLM
  |
  v
NVIDIA GPU
  |
  v
LLM
```

Then validate:

``` text
GET  /v1/models
POST /v1/chat/completions
POST /v1/completions
```

After that:

-   Prometheus metrics
-   latency
-   throughput
-   concurrency
-   Docker health checks
-   Kubernetes deployment
-   CI/CD deployment

------------------------------------------------------------------------

# 17. Sprint 8.3 Acceptance Criteria

-   [x] Pull vLLM CPU container
-   [x] Verify vLLM version
-   [x] Validate Docker/WSL resources
-   [x] Validate GPU availability
-   [x] Start vLLM with Qwen3-0.6B
-   [x] Observe model resolution
-   [x] Observe model download
-   [x] Observe model loading
-   [x] Observe compilation/warm-up
-   [x] Investigate oneDNN warning
-   [x] Investigate shared-memory warning
-   [x] Identify KV-cache failure
-   [x] Identify memory constraint
-   [x] Document troubleshooting
-   [x] Define next GPU-based vLLM exercise

**Status: COMPLETE --- Troubleshooting/Learning Objective Achieved**

------------------------------------------------------------------------

# 18. Final Technical Summary

The vLLM CPU deployment was technically successful through most of the
inference-engine startup lifecycle:

``` text
vLLM container       ✓
Model resolution     ✓
Model download       ✓
Model loading        ✓
Compilation           ✓
Warm-up               ✓
KV cache              ✗
API readiness         ✗
```

Final failure:

``` text
ValueError: No available memory for the cache blocks.
```

Root cause:

``` text
Insufficient Docker/WSL memory for KV-cache initialization.
```

Decision:

``` text
Stop CPU-runtime tuning.
Move GPU-based vLLM serving to a suitable environment.
```
