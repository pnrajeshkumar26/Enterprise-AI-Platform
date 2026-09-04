from dataclasses import dataclass


@dataclass(frozen=True)
class TokenCapacityState:
    """Token capacity assessment for one model."""

    model: str
    max_context_tokens: int
    estimated_input_tokens: int
    output_token_budget: int
    estimated_total_tokens: int
    remaining_tokens: int
    utilization_percent: float
    status: str

    @property
    def has_capacity(self) -> bool:
        return self.estimated_total_tokens <= self.max_context_tokens

    @property
    def is_warning(self) -> bool:
        return self.status == "WARNING"

    @property
    def is_high(self) -> bool:
        return self.status == "HIGH"

    @property
    def is_exceeded(self) -> bool:
        return self.status == "EXCEEDED"


class TokenCapacityEvaluator:
    """Evaluate request token headroom against model context capacity."""

    STATUS_NORMAL = "NORMAL"
    STATUS_WARNING = "WARNING"
    STATUS_HIGH = "HIGH"
    STATUS_EXCEEDED = "EXCEEDED"

    def __init__(
        self,
        capacity_by_model: dict[str, int] | None = None,
        warning_threshold: float = 0.80,
        high_threshold: float = 0.90,
    ):
        self.capacity_by_model = capacity_by_model or {
            "tinyllama": 2048,
            "phi3": 4096,
        }

        if warning_threshold <= 0:
            raise ValueError("warning_threshold must be > 0")

        if high_threshold <= warning_threshold:
            raise ValueError(
                "high_threshold must be greater than warning_threshold"
            )

        if high_threshold > 1:
            raise ValueError("high_threshold must be <= 1")

        self.warning_threshold = warning_threshold
        self.high_threshold = high_threshold

    def estimate_input_tokens(self, prompt: str) -> int:
        """
        Estimate input tokens deterministically.

        This is intentionally a lightweight routing estimate.
        Actual backend token usage remains the authoritative telemetry.
        """
        if not prompt:
            return 0

        # Conservative approximation:
        # roughly four characters per token.
        return max(1, (len(prompt) + 3) // 4)

    def evaluate(
        self,
        model: str,
        prompt: str,
        output_token_budget: int = 256,
    ) -> TokenCapacityState:
        normalized_model = (model or "").strip().lower()

        if normalized_model not in self.capacity_by_model:
            raise ValueError(
                f"Unknown model: {normalized_model}"
            )

        if output_token_budget < 0:
            raise ValueError(
                "output_token_budget must be >= 0"
            )

        max_context_tokens = self.capacity_by_model[
            normalized_model
        ]

        estimated_input_tokens = self.estimate_input_tokens(
            prompt
        )

        estimated_total_tokens = (
            estimated_input_tokens
            + output_token_budget
        )

        remaining_tokens = (
            max_context_tokens
            - estimated_total_tokens
        )

        utilization_percent = (
            estimated_total_tokens
            / max_context_tokens
            * 100
        )

        utilization_ratio = (
            estimated_total_tokens
            / max_context_tokens
        )

        if utilization_ratio > 1:
            status = self.STATUS_EXCEEDED
        elif utilization_ratio >= self.high_threshold:
            status = self.STATUS_HIGH
        elif utilization_ratio >= self.warning_threshold:
            status = self.STATUS_WARNING
        else:
            status = self.STATUS_NORMAL

        return TokenCapacityState(
            model=normalized_model,
            max_context_tokens=max_context_tokens,
            estimated_input_tokens=estimated_input_tokens,
            output_token_budget=output_token_budget,
            estimated_total_tokens=estimated_total_tokens,
            remaining_tokens=remaining_tokens,
            utilization_percent=utilization_percent,
            status=status,
        )


token_capacity_evaluator = TokenCapacityEvaluator()
