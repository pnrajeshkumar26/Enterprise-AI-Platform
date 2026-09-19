"""Deterministic evaluation scoring utilities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeterministicMetrics:
    """Metrics collected without an LLM judge."""

    exact_match: float | None = None
    reference_contains: float | None = None
    format_compliant: bool | None = None
    latency_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


def calculate_deterministic_score(metrics: DeterministicMetrics) -> float:
    """
    Calculate a simple deterministic quality score.

    Only available quality signals are included.
    Operational metrics such as latency, tokens, and cost
    are reported separately and do not directly determine
    answer quality.
    """
    quality_signals: list[float] = []

    if metrics.exact_match is not None:
        quality_signals.append(metrics.exact_match)

    if metrics.reference_contains is not None:
        quality_signals.append(metrics.reference_contains)

    if metrics.format_compliant is not None:
        quality_signals.append(float(metrics.format_compliant))

    if not quality_signals:
        return 0.0

    return sum(quality_signals) / len(quality_signals)