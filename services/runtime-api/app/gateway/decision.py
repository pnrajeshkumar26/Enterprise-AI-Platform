from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GatewayDecision:
    """
    Explainable routing decision produced by the LLM Gateway.
    """

    request_id: str
    requested_model: str
    selected_model: str
    routing_score: int
    routing_reason: str
    routing_reasons: Tuple[str, ...]
