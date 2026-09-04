from app.gateway.gateway import LLMGateway
from app.resources.gpu_state import GPUResourceState


def _test_gpu_state():
    return GPUResourceState(
        gpu_name="Tesla T4",
        gpu_utilization_percent=0.0,
        memory_utilization_percent=0.0,
        memory_total_mib=15360.0,
        memory_used_mib=13418.0,
        memory_free_mib=1493.0,
        temperature_celsius=37.0,
    )


def _patch_gpu(monkeypatch):
    monkeypatch.setattr(
        "app.gateway.gateway.gpu_resource_collector.collect",
        lambda: _test_gpu_state(),
    )


def test_auto_routing_moves_to_phi3_when_tinyllama_capacity_exceeded(
    monkeypatch,
):
    _patch_gpu(monkeypatch)

    monkeypatch.setattr(
        "app.gateway.gateway.model_router.route",
        lambda prompt: type(
            "Routing",
            (),
            {
                "selected_model": "tinyllama",
                "score": 0,
                "reason": "test base routing",
            },
        )(),
    )

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="a" * 6600,
    )

    decision = gateway.decide(context)

    assert (
        decision.tinyllama_token_capacity.status
        == "EXCEEDED"
    )

    assert (
        decision.phi3_token_capacity.has_capacity
        is True
    )

    assert decision.selected_model == "phi3"

    assert "capacity override" in decision.routing_reason


def test_auto_routing_keeps_tinyllama_when_capacity_is_safe(
    monkeypatch,
):
    _patch_gpu(monkeypatch)

    monkeypatch.setattr(
        "app.gateway.gateway.model_router.route",
        lambda prompt: type(
            "Routing",
            (),
            {
                "selected_model": "tinyllama",
                "score": 0,
                "reason": "test base routing",
            },
        )(),
    )

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="hello",
    )

    decision = gateway.decide(context)

    assert decision.selected_model == "tinyllama"
    assert "capacity override" not in decision.routing_reason


def test_explicit_tinyllama_rejects_insufficient_capacity(
    monkeypatch,
):
    _patch_gpu(monkeypatch)

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="tinyllama",
        prompt="a" * 6600,
    )

    try:
        gateway.decide(context)
    except ValueError as exc:
        assert "cannot accommodate" in str(exc)
    else:
        raise AssertionError(
            "Expected explicit TinyLlama capacity rejection"
        )
