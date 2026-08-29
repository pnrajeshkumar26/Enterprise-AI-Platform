from dataclasses import dataclass


@dataclass(frozen=True)
class GuardResult:
    valid: bool
    reason: str | None = None


class ResponseGuard:
    """
    Lightweight deterministic guard for platform-critical terminology.

    This is intentionally narrow. It does not attempt to judge general
    factual correctness or rewrite model output. It only detects known
    contradictory definitions that are unacceptable for this platform.
    """

    # Known incorrect expansions/definitions observed during validation.
    CONTRADICTIONS = (
        "vectorized large language model",
        "vectorized large language models",
        "vectorized llvm",
        "low-level machine operations",
        "low-level machine learning operations",
        "vllm is a type of large language model",
    )

    def validate(self, response: str) -> GuardResult:
        text = response.strip().lower()

        if not text:
            return GuardResult(
                valid=False,
                reason="empty response",
            )

        for contradiction in self.CONTRADICTIONS:
            if contradiction in text:
                return GuardResult(
                    valid=False,
                    reason=f"known terminology contradiction: {contradiction}",
                )

        return GuardResult(valid=True)


response_guard = ResponseGuard()
