from prometheus_client import REGISTRY

from app.core.runtime_metrics import (
    LLM_GENERATION_FAILURES_TOTAL,
    LLM_REQUESTS_TOTAL,
    LLM_ROUTING_CAPACITY_OVERRIDES_TOTAL,
    LLM_ROUTING_CAPACITY_REJECTIONS_TOTAL,
    LLM_ROUTING_DECISIONS_TOTAL,
    LLM_ROUTING_OUTCOMES_TOTAL,
    LLM_ROUTING_SCORE,
    LLM_ROUTING_SCORE_MARGIN,
    LLM_ROUTING_SELECTED_MODELS_TOTAL,
)
from app.gateway.decision import GatewayDecision
from app.routing.capacity_router import CapacityRoutingError
from app.services.generate_service import GenerateService


def _value(metric, labels=None):
    labels = labels or {}
    return metric.labels(**labels)._value.get()


def test_routing_metrics_helper_records_selected_model_and_outcome():
    service = GenerateService()

    decision = GatewayDecision(
        request_id="test-request",
        requested_model="auto",
        selected_model="phi3",
        routing_score=0,
        routing_reason="multi-signal",
        routing_reasons=("multi-signal",),
        routing_outcome="multi_signal",
    )

    before_selected = _value(
        LLM_ROUTING_SELECTED_MODELS_TOTAL,
        {"selected_model": "phi3"},
    )
    before_outcome = _value(
        LLM_ROUTING_OUTCOMES_TOTAL,
        {"outcome": "multi_signal"},
    )

    service._record_routing_metrics(
        requested_model="auto",
        selected_model="phi3",
        decision=decision,
    )

    assert _value(
        LLM_ROUTING_SELECTED_MODELS_TOTAL,
        {"selected_model": "phi3"},
    ) == before_selected + 1

    assert _value(
        LLM_ROUTING_OUTCOMES_TOTAL,
        {"outcome": "multi_signal"},
    ) == before_outcome + 1


def test_routing_metrics_helper_records_auto_routing_decision():
    service = GenerateService()

    decision = GatewayDecision(
        request_id="test-request",
        requested_model="auto",
        selected_model="phi3",
        routing_score=0,
        routing_reason="multi-signal",
        routing_reasons=("multi-signal",),
        routing_outcome="multi_signal",
    )

    before = _value(
        LLM_ROUTING_DECISIONS_TOTAL,
        {
            "requested_model": "auto",
            "selected_model": "phi3",
        },
    )

    service._record_routing_metrics(
        requested_model="auto",
        selected_model="phi3",
        decision=decision,
    )

    assert _value(
        LLM_ROUTING_DECISIONS_TOTAL,
        {
            "requested_model": "auto",
            "selected_model": "phi3",
        },
    ) == before + 1


def test_routing_metrics_helper_records_multi_signal_scores():
    service = GenerateService()

    decision = GatewayDecision(
        request_id="test-request",
        requested_model="auto",
        selected_model="phi3",
        routing_score=0,
        routing_reason="multi-signal",
        routing_reasons=("multi-signal",),
        routing_outcome="multi_signal",
        tinyllama_multi_signal_score=5.0,
        phi3_multi_signal_score=9.0,
    )

    service._record_routing_metrics(
        requested_model="auto",
        selected_model="phi3",
        decision=decision,
    )

    assert (
        LLM_ROUTING_SCORE.labels(
            model="tinyllama"
        )._value.get()
        == 5.0
    )

    assert (
        LLM_ROUTING_SCORE.labels(
            model="phi3"
        )._value.get()
        == 9.0
    )

    assert LLM_ROUTING_SCORE_MARGIN._value.get() == 4.0


def test_routing_metrics_helper_records_capacity_override():
    service = GenerateService()

    decision = GatewayDecision(
        request_id="test-request",
        requested_model="auto",
        selected_model="phi3",
        routing_score=0,
        routing_reason="capacity override",
        routing_reasons=("capacity override",),
        routing_outcome="capacity_override",
        capacity_from_model="tinyllama",
        capacity_to_model="phi3",
    )

    before = _value(
        LLM_ROUTING_CAPACITY_OVERRIDES_TOTAL,
        {
            "from_model": "tinyllama",
            "to_model": "phi3",
        },
    )

    service._record_routing_metrics(
        requested_model="auto",
        selected_model="phi3",
        decision=decision,
    )

    assert _value(
        LLM_ROUTING_CAPACITY_OVERRIDES_TOTAL,
        {
            "from_model": "tinyllama",
            "to_model": "phi3",
        },
    ) == before + 1


def test_capacity_rejection_metric_exists():
    metric_names = {
        metric.name
        for metric in REGISTRY.collect()
    }

    assert (
        "llm_routing_capacity_rejections"
        in metric_names
    )


def test_routing_metrics_helper_sanitizes_non_finite_scores():
    service = GenerateService()

    decision = GatewayDecision(
        request_id="test-request",
        requested_model="auto",
        selected_model="phi3",
        routing_score=0,
        routing_reason="capacity override",
        routing_reasons=("capacity override",),
        routing_outcome="capacity_override",
        capacity_from_model="tinyllama",
        capacity_to_model="phi3",
        tinyllama_multi_signal_score=float("-inf"),
        phi3_multi_signal_score=9.0,
    )

    service._record_routing_metrics(
        requested_model="auto",
        selected_model="phi3",
        decision=decision,
    )

    assert (
        LLM_ROUTING_SCORE.labels(
            model="tinyllama"
        )._value.get()
        == 0.0
    )

    assert (
        LLM_ROUTING_SCORE.labels(
            model="phi3"
        )._value.get()
        == 9.0
    )

    assert LLM_ROUTING_SCORE_MARGIN._value.get() == 0.0


def test_capacity_rejection_records_request_failure_not_generation_failure(
    monkeypatch,
):
    service = GenerateService()

    def reject_capacity(_context):
        raise CapacityRoutingError(
            "Request exceeds available token capacity"
        )

    monkeypatch.setattr(
        "app.services.generate_service.llm_gateway.decide",
        reject_capacity,
    )

    before_rejections = _value(
        LLM_ROUTING_CAPACITY_REJECTIONS_TOTAL,
        {"requested_model": "auto"},
    )

    before_outcomes = _value(
        LLM_ROUTING_OUTCOMES_TOTAL,
        {"outcome": "capacity_rejected"},
    )

    before_requests = _value(
        LLM_REQUESTS_TOTAL,
        {
            "requested_model": "auto",
            "selected_model": "auto",
            "status": "failure",
        },
    )

    before_generation_failures = _value(
        LLM_GENERATION_FAILURES_TOTAL,
        {"selected_model": "auto"},
    )

    try:
        service.generate(
            model_name="auto",
            prompt="Hello",
            max_output_tokens=5000,
        )
    except CapacityRoutingError:
        pass
    else:
        raise AssertionError(
            "Expected CapacityRoutingError"
        )

    assert _value(
        LLM_ROUTING_CAPACITY_REJECTIONS_TOTAL,
        {"requested_model": "auto"},
    ) == before_rejections + 1

    assert _value(
        LLM_ROUTING_OUTCOMES_TOTAL,
        {"outcome": "capacity_rejected"},
    ) == before_outcomes + 1

    assert _value(
        LLM_REQUESTS_TOTAL,
        {
            "requested_model": "auto",
            "selected_model": "auto",
            "status": "failure",
        },
    ) == before_requests + 1

    assert _value(
        LLM_GENERATION_FAILURES_TOTAL,
        {"selected_model": "auto"},
    ) == before_generation_failures
