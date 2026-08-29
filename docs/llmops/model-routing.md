# Model Routing

## Current routing model

The `ModelRouter` is deterministic and score-based.

High-level signals include:

- prompt length
- multiple questions
- multi-step wording
- complexity indicators
- technical/code indicators
- code blocks

Current decision boundary:

```text
score < 3  -> TinyLlama
score >= 3 -> Phi-3
```

## Example behavior

| Request type | Expected route |
|---|---|
| Casual joke | TinyLlama |
| Technical/factual question | Phi-3 |
| Complex LLMOps architecture analysis | Phi-3 |

## Why deterministic routing?

For a learning/reference platform, deterministic routing makes it possible to explain why a request was selected and to write stable unit tests.

A future production router could use a richer policy involving model availability, latency, GPU pressure, token budget and cost.

## Interview explanation

> I started with deterministic routing because I wanted routing decisions to be reproducible and testable. Once the platform has reliable telemetry, those metrics can become inputs to more adaptive routing policies.
