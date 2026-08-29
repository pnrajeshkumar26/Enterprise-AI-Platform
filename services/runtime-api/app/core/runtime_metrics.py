from prometheus_client import Counter, Gauge, Histogram


# -------------------------------------------------------------------
# Request metrics
# -------------------------------------------------------------------

LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM generation requests.",
    [
        "requested_model",
        "selected_model",
        "status",
    ],
)


LLM_GENERATION_DURATION_SECONDS = Histogram(
    "llm_request_duration_seconds",
    "LLM generation request latency in seconds.",
    [
        "selected_model",
    ],
)


LLM_GENERATION_FAILURES_TOTAL = Counter(
    "llm_generation_failures_total",
    "Total number of failed LLM generation requests.",
    [
        "selected_model",
    ],
)


# -------------------------------------------------------------------
# Routing metrics
# -------------------------------------------------------------------

LLM_ROUTING_DECISIONS_TOTAL = Counter(
    "llm_routing_decisions_total",
    "Total number of automatic model routing decisions.",
    [
        "requested_model",
        "selected_model",
    ],
)


# -------------------------------------------------------------------
# Backend health
# -------------------------------------------------------------------

LLM_BACKEND_UP = Gauge(
    "llm_backend_up",
    "Backend availability. 1 = available, 0 = unavailable.",
    [
        "backend",
    ],
)


# -------------------------------------------------------------------
# Model registry
# -------------------------------------------------------------------

LLM_MODELS_CONFIGURED = Gauge(
    "llm_models_configured",
    "Number of models configured in the runtime model registry.",
)


# -------------------------------------------------------------------
# Runtime state
# -------------------------------------------------------------------

LLM_RUNTIME_UP = Gauge(
    "llm_runtime_up",
    "Runtime API availability. Always 1 while the process is healthy.",
)

LLM_RUNTIME_UP.set(1)
