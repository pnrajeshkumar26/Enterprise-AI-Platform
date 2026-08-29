# Inference Architecture

## Request lifecycle

```text
Client
  |
  v
POST /generate
  |
  v
Runtime API
  |
  +--> explicit model? -------> selected backend
  |
  +--> auto -------------------> ModelRouter
                                     |
                         +-----------+-----------+
                         |                       |
                    TinyLlama                 Phi-3
                    llama.cpp                  vLLM
```

## TinyLlama path

TinyLlama is exposed as a dedicated inference service using `llama.cpp` and the GGUF model format. This path is intended for lower-complexity requests where a lightweight model is sufficient.

## Phi-3 path

Phi-3 Mini is served through vLLM's OpenAI-compatible `/v1/chat/completions` API. The Runtime API's `VLLMClient` isolates the HTTP contract and sampling configuration from the rest of the platform.

## Why two backends?

The two-backend design demonstrates a core LLMOps problem: matching workload requirements to model capability and resource cost rather than routing everything to one model.

## Quality control

Phi-3 responses pass through a narrow deterministic response guard for known platform-critical terminology contradictions. The guard can trigger one corrective generation; it is not a universal factual verifier.

## Future evolution

Possible next routing signals:

- observed latency
- GPU memory pressure
- model availability
- prompt/token estimates
- workload class
- cost budget
- historical success/failure rate
