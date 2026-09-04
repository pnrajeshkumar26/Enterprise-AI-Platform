from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayDecision:
    request_id: str
    requested_model: str
    selected_model: str
    routing_score: int
    routing_reason: str
    routing_reasons: tuple[str, ...]

    # Historical latency signal observed before routing.
    tinyllama_avg_latency: float | None = None
    phi3_avg_latency: float | None = None

    # Current GPU resource state observed before routing.
    gpu_name: str | None = None
    gpu_utilization_percent: float | None = None
    gpu_memory_utilization_percent: float | None = None
    gpu_memory_total_mib: float | None = None
    gpu_memory_used_mib: float | None = None
    gpu_memory_free_mib: float | None = None
