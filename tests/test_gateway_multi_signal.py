from app.gateway.gateway import LLMGateway
from app.resources.gpu_state import GPUResourceState


def _test_gpu_state():
    return GPUResourceState(
        gpu_name="Tesla T4",
        gpu_utilization_percent=20.0,
        memory_utilization_percent=20.0,
        memory_total_mib=15360.0,
        memory_used_mib=10000.0,
        memory_free_mib=5360.0,
        temperature_celsius=37.0,
    )


def _patch_gpu(monkeypatch):
    monkeypatch.setattr(
        "app.gateway.gateway.gpu_resource_collector.collect",
        lambda: _test_gpu_state(),
    )


def test_gateway_exposes_multi_signal_scores(monkeypatch):
    _patch_gpu(monkeypatch)

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="Hello",
    )

    decision = gateway.decide(context)

    assert decision.tinyllama_multi_signal_score is not None
    assert decision.phi3_multi_signal_score is not None


def test_gateway_uses_multi_signal_decision(monkeypatch):
    _patch_gpu(monkeypatch)

    monkeypatch.setattr(
        "app.gateway.gateway.model_router.route",
        lambda prompt: type(
            "Routing",
            (),
            {
                "selected_model": "tinyllama",
                "score": 0,
                "reason": "base preference",
            },
        )(),
    )

    from app.routing.multi_signal_router import ModelScoreBreakdown

    monkeypatch.setattr(
        "app.gateway.gateway.multi_signal_router.decide",
        lambda **kwargs: type(
            "MultiSignal",
            (),
            {
                "selected_model": "phi3",
                "tinyllama_score": 5.0,
                "phi3_score": 9.0,
                "tinyllama_breakdown": ModelScoreBreakdown(
                    model="tinyllama",
                    base_preference_score=2.0,
                    capacity_score=1.0,
                    latency_score=2.0,
                    gpu_pressure_score=0.0,
                    total_score=5.0,
                ),
                "phi3_breakdown": ModelScoreBreakdown(
                    model="phi3",
                    base_preference_score=2.0,
                    capacity_score=8.0,
                    latency_score=-1.0,
                    gpu_pressure_score=0.0,
                    total_score=9.0,
                ),
                "reason": (
                    "multi-signal scores: "
                    "tinyllama=5.0, phi3=9.0; "
                    "selected=phi3"
                ),
            },
        )(),
    )

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="Hello",
    )

    decision = gateway.decide(context)

    assert decision.selected_model == "phi3"
    assert decision.tinyllama_multi_signal_score == 5.0
    assert decision.phi3_multi_signal_score == 9.0


def test_gateway_routing_reason_contains_multi_signal_explanation(
    monkeypatch,
):
    _patch_gpu(monkeypatch)

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="What is LLMOps?",
    )

    decision = gateway.decide(context)

    assert "multi-signal scores:" in decision.routing_reason
