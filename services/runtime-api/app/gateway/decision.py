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
