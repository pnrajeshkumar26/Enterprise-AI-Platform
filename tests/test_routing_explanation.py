from app.gateway.decision import GatewayDecision
from app.routing.multi_signal_router import ModelScoreBreakdown
from app.schemas.generate import (
    RoutingExplanation,
    RoutingScoreBreakdown,
)


def _build_decision() -> GatewayDecision:
    tinyllama = ModelScoreBreakdown(
        model="tinyllama",
        base_preference_score=2.0,
        capacity_score=1.0,
        latency_score=2.0,
        gpu_pressure_score=0.0,
        total_score=5.0,
    )

    phi3 = ModelScoreBreakdown(
        model="phi3",
        base_preference_score=2.0,
        capacity_score=8.0,
        latency_score=-1.0,
        gpu_pressure_score=0.0,
        total_score=9.0,
    )

    return GatewayDecision(
        request_id="test-request",
        requested_model="auto",
        selected_model="phi3",
        routing_score=0,
        routing_reason=(
            "multi-signal scores: "
            "tinyllama=5.0, phi3=9.0; "
            "selected=phi3"
        ),
        routing_reasons=("multi-signal routing",),
        tinyllama_multi_signal_score=5.0,
        phi3_multi_signal_score=9.0,
        tinyllama_score_breakdown=tinyllama,
        phi3_score_breakdown=phi3,
    )


def _build_explanation(
    decision: GatewayDecision,
) -> RoutingExplanation:
    breakdowns = {}

    for name, breakdown in (
        ("tinyllama", decision.tinyllama_score_breakdown),
        ("phi3", decision.phi3_score_breakdown),
    ):
        if breakdown is None:
            continue

        breakdowns[name] = RoutingScoreBreakdown(
            base_preference=breakdown.base_preference_score,
            capacity=breakdown.capacity_score,
            latency=breakdown.latency_score,
            gpu_pressure=breakdown.gpu_pressure_score,
            total=breakdown.total_score,
        )

    return RoutingExplanation(
        selected_model=decision.selected_model,
        reason=decision.routing_reason,
        scores={
            "tinyllama": decision.tinyllama_multi_signal_score,
            "phi3": decision.phi3_multi_signal_score,
        },
        breakdown=breakdowns,
    )


def test_routing_explanation_exposes_selected_model_and_scores():
    decision = _build_decision()
    explanation = _build_explanation(decision)

    assert explanation.selected_model == "phi3"
    assert explanation.scores["tinyllama"] == 5.0
    assert explanation.scores["phi3"] == 9.0


def test_routing_explanation_exposes_signal_contributions():
    decision = _build_decision()
    explanation = _build_explanation(decision)

    tinyllama = explanation.breakdown["tinyllama"]
    phi3 = explanation.breakdown["phi3"]

    assert tinyllama.base_preference == 2.0
    assert tinyllama.capacity == 1.0
    assert tinyllama.latency == 2.0
    assert tinyllama.gpu_pressure == 0.0
    assert tinyllama.total == 5.0

    assert phi3.base_preference == 2.0
    assert phi3.capacity == 8.0
    assert phi3.latency == -1.0
    assert phi3.gpu_pressure == 0.0
    assert phi3.total == 9.0


def test_routing_explanation_score_totals_match_breakdowns():
    decision = _build_decision()
    explanation = _build_explanation(decision)

    for model, breakdown in explanation.breakdown.items():
        contribution_sum = (
            breakdown.base_preference
            + breakdown.capacity
            + breakdown.latency
            + breakdown.gpu_pressure
        )

        assert contribution_sum == breakdown.total
        assert explanation.scores[model] == breakdown.total


def test_explicit_routing_explanation_can_have_no_score_breakdown():
    explanation = RoutingExplanation(
        selected_model="phi3",
        reason="Explicit model requested",
    )

    assert explanation.selected_model == "phi3"
    assert explanation.scores == {}
    assert explanation.breakdown == {}
