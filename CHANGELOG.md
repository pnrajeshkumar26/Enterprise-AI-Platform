# Changelog

## [Sprint 14 — Stage 2] — Token Telemetry

### Added

- Added normalized `GenerationResult` for backend generation metadata.
- Added exact token usage extraction from vLLM responses.
- Extended TinyLlama responses with prompt, completion, and total token usage.
- Updated Runtime API generation flow to normalize token telemetry across backends.
- Added Prometheus counters:
  - `llm_input_tokens_total`
  - `llm_output_tokens_total`
  - `llm_tokens_total`
- Updated vLLM client tests for the new `GenerationResult` contract.

### Validation

- Runtime API image: `enterprise-runtime-api:3.12`
- TinyLlama image: `enterprise-tinyllama:1.3`
- Automated tests: `14 passed`
- Live TinyLlama, Phi-3, and automatic routing requests validated.
- Prometheus token counters validated for both models.

---

All notable changes to this project will be documented in this file.

## [v0.1.0] - Foundation

### Added
```markdown
# Changelog

All notable changes to this project are documented here.

## [Sprint 13] — LLMOps Observability

### Added

- Intelligent model routing
- TinyLlama / llama.cpp inference
- Phi-3 / vLLM inference
- Runtime API instrumentation
- Prometheus metrics
- NVIDIA DCGM GPU telemetry
- Grafana dashboards
- Grafana alerting
- Containerized Streamlit frontend
- Restart and recovery validation
- Response-quality guardrails
- Additional automated tests
- GitHub Actions CI/CD improvements
- Public LLMOps documentation

### Observability

- Runtime API health monitoring
- DCGM exporter health monitoring
- LLM request metrics
- LLM generation failure metrics
- LLM latency metrics
- GPU framebuffer memory monitoring
- Operational alert rules

### Release

- Commit: `7ad8840`
- Tag: `sprint-13-llmops-observability`

---

## [v0.1.0] — Foundation

### Added

- Initial repository
- Project structure
- Documentation structure
- Enterprise architecture planning
