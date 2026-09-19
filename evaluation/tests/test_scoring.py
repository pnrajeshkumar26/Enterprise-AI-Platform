"""Tests for deterministic scoring."""

from evaluation.metrics.scoring import (
    DeterministicMetrics,
    calculate_deterministic_score,
)


def test_score_with_all_quality_signals():
    metrics = DeterministicMetrics(
        exact_match=1.0,
        reference_contains=1.0,
        format_compliant=True,
    )

    assert calculate_deterministic_score(metrics) == 1.0


def test_score_with_mixed_signals():
    metrics = DeterministicMetrics(
        exact_match=1.0,
        reference_contains=0.0,
        format_compliant=True,
    )

    assert calculate_deterministic_score(metrics) == 2 / 3


def test_score_with_no_quality_signals():
    metrics = DeterministicMetrics(
        latency_seconds=1.5,
        input_tokens=20,
        output_tokens=30,
        estimated_cost_usd=0.001,
    )

    assert calculate_deterministic_score(metrics) == 0.0


def test_operational_metrics_do_not_change_quality_score():
    fast = DeterministicMetrics(
        exact_match=1.0,
        latency_seconds=0.5,
        input_tokens=10,
        output_tokens=10,
        estimated_cost_usd=0.001,
    )

    slow = DeterministicMetrics(
        exact_match=1.0,
        latency_seconds=5.0,
        input_tokens=1000,
        output_tokens=1000,
        estimated_cost_usd=0.1,
    )

    assert calculate_deterministic_score(fast) == 1.0
    assert calculate_deterministic_score(slow) == 1.0