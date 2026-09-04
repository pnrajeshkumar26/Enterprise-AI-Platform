from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayRequestContext:
    """
    Normalized request context used by the LLM Gateway.
    """

    request_id: str
    requested_model: str
    prompt: str
    prompt_length: int
    requested_output_tokens: int | None = None

    @classmethod
    def from_request(
        cls,
        request_id: str,
        requested_model: str,
        prompt: str,
        requested_output_tokens: int | None = None,
    ) -> "GatewayRequestContext":
        normalized_model = (
            requested_model or "auto"
        ).lower().strip()

        normalized_prompt = prompt or ""

        if requested_output_tokens is not None:
            if requested_output_tokens < 1:
                raise ValueError(
                    "max_output_tokens must be >= 1"
                )

        return cls(
            request_id=request_id,
            requested_model=normalized_model,
            prompt=normalized_prompt,
            prompt_length=len(normalized_prompt),
            requested_output_tokens=requested_output_tokens,
        )
