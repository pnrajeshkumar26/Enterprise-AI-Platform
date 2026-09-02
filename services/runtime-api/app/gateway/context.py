from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayRequestContext:
    """
    Normalized request context used by the LLM Gateway.

    Stage 1 intentionally contains only request-level information.
    Token, cost, latency and GPU signals will be added incrementally.
    """

    request_id: str
    requested_model: str
    prompt: str
    prompt_length: int

    @classmethod
    def from_request(
        cls,
        request_id: str,
        requested_model: str,
        prompt: str,
    ) -> "GatewayRequestContext":
        normalized_model = (requested_model or "auto").lower().strip()
        normalized_prompt = prompt or ""

        return cls(
            request_id=request_id,
            requested_model=normalized_model,
            prompt=normalized_prompt,
            prompt_length=len(normalized_prompt),
        )
