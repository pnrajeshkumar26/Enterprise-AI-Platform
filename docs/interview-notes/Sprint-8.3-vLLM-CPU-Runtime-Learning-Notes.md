# Sprint 8.3 --- vLLM CPU Runtime: LLM Ops Learning Notes

## What This Sprint Teaches

Sprint 8.3 demonstrates how an LLM Ops engineer should approach an
inference-runtime deployment rather than treating vLLM as only a Python
package.

The exercise covered:

-   Dockerized inference
-   CPU backend
-   model loading
-   runtime initialization
-   compilation/warm-up
-   KV cache
-   memory troubleshooting
-   GPU availability validation
-   operational stop/escalation decisions

------------------------------------------------------------------------

## 1. vLLM Runtime Mental Model

``` text
Application / Client
        |
        v
OpenAI-compatible API
        |
        v
vLLM API Server
        |
        +--> Scheduler
        |
        +--> Model
        |
        +--> KV Cache
        |
        +--> CPU/GPU backend
        |
        v
Generated tokens
```

The API server can only become healthy after the underlying model engine
has completed initialization.

------------------------------------------------------------------------

## 2. Model Memory vs Serving Memory

A common beginner mistake is:

> "The model is only 1.4 GB, so a 4 GB container should be enough."

That is not a safe inference.

Serving requires:

``` text
Model weights
+ runtime
+ framework
+ compilation
+ temporary buffers
+ KV cache
+ request state
+ concurrency
```

Therefore capacity planning must be based on the complete serving
workload.

------------------------------------------------------------------------

## 3. What Is KV Cache?

During autoregressive generation, the transformer repeatedly uses
attention information from previous tokens.

The KV cache keeps this information available so the server does not
have to recompute it for every generated token.

Conceptually:

``` text
Prompt
  ↓
Token 1 ──> K/V stored
Token 2 ──> K/V stored
Token 3 ──> K/V stored
Token 4 ──> K/V stored
...
```

As context and concurrent requests increase, KV-cache requirements
increase.

This is why an inference engine can load a model but still fail before
serving requests.

------------------------------------------------------------------------

## 4. Why vLLM Is Important for LLM Ops

vLLM is an inference/serving engine rather than a model-training
framework.

The LLM Ops focus is:

``` text
Model
  ↓
Serving runtime
  ↓
API
  ↓
Container
  ↓
Kubernetes
  ↓
Monitoring
  ↓
CI/CD
```

The Sprint 8.3 exercise covers the serving-runtime layer.

------------------------------------------------------------------------

## 5. Operational Troubleshooting Pattern

When an inference container fails:

### First ask

``` text
Did the container start?
```

### Then

``` text
Did the runtime start?
```

### Then

``` text
Was the model resolved?
```

### Then

``` text
Was the model downloaded?
```

### Then

``` text
Were weights loaded?
```

### Then

``` text
Did compilation/warm-up complete?
```

### Then

``` text
Was KV cache initialized?
```

### Finally

``` text
Is the API ready?
```

This sequence prevents guessing.

------------------------------------------------------------------------

## 6. Key Interview Questions

### Q1. What is vLLM?

vLLM is an inference and serving engine designed to efficiently serve
large language models, including through an OpenAI-compatible API.

### Q2. Why is KV cache important?

It stores attention key/value state from previous tokens and avoids
repeated computation during autoregressive generation.

### Q3. Can a model fit in memory but still fail to serve?

Yes. The inference runtime needs additional memory for KV cache,
framework/runtime state, temporary buffers, compilation, and concurrent
requests.

### Q4. What would you check when vLLM fails during startup?

Check:

1.  container logs
2.  CPU/GPU availability
3.  host/container memory
4.  model compatibility
5.  model download
6.  dtype
7.  KV-cache allocation
8.  shared memory
9.  runtime configuration

### Q5. What was the root cause in this sprint?

Insufficient available Docker/WSL memory during KV-cache initialization.

### Q6. Why didn't you continue changing parameters?

Because the evidence indicated a fundamental resource constraint.
Further parameter experimentation on the same constrained environment
would have low value.

### Q7. Why is GPU vLLM preferred for production LLM serving?

Modern LLM inference generally benefits heavily from GPU parallelism and
GPU memory bandwidth. CPU serving can be useful for specific workloads,
but production sizing depends on model, latency, throughput, and
concurrency requirements.

------------------------------------------------------------------------

## 7. Production Mindset

The key lesson is:

> An LLM Ops engineer must understand the relationship between model
> size, runtime memory, KV cache, concurrency, hardware, and serving
> performance.

The troubleshooting result is not simply:

``` text
vLLM failed
```

It is:

``` text
vLLM initialized successfully through model loading and warm-up,
then failed at KV-cache allocation because the runtime environment
did not have sufficient available memory.
```

That is the level of diagnosis expected in an LLM Ops environment.

------------------------------------------------------------------------

## 8. Next Learning Target

Move the vLLM exercise to a GPU-capable environment and implement:

``` text
vLLM
  ↓
OpenAI-compatible API
  ↓
Docker
  ↓
Kubernetes
  ↓
Health checks
  ↓
Prometheus
  ↓
Grafana
  ↓
CI/CD
```

This will connect Sprint 8.3 directly with the later Kubernetes,
observability, production-runtime, benchmarking, and CI/CD work in the
LLM Ops roadmap.

------------------------------------------------------------------------

## Sprint 8.3 Status

**COMPLETE**

The objective was achieved as a deployment and troubleshooting exercise.
The remaining GPU-serving work is intentionally deferred to a suitable
GPU environment.
