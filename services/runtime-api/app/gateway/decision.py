from dataclasses import dataclass

from app.routing.token_capacity import TokenCapacityState


@dataclass(frozen=True)
class GatewayDecision:
    request_id: str
    requested_model: str
    selected_model: str
    routing_score: int
    routing_reason: str
    routing_reasons: tuple[str, ...]

    # Resolved output-token budget for the selected model.
    output_token_budget: int = 0

    # Token capacity signals observed before routing.
    tinyllama_token_capacity: TokenCapacityState | None = None
    phi3_token_capacity: TokenCapacityState | None = None

    # Multi-signal routing scores.
    tinyllama_multi_signal_score: float | None = None
    phi3_multi_signal_score: float | None = None

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
