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


def test_gateway_exposes_token_capacity_for_both_models(monkeypatch):
    _patch_gpu(monkeypatch)

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="Hello",
    )

    decision = gateway.decide(context)

    assert decision.tinyllama_token_capacity is not None
    assert decision.phi3_token_capacity is not None

    assert (
        decision.tinyllama_token_capacity.max_context_tokens
        == 2048
    )

    assert (
        decision.phi3_token_capacity.max_context_tokens
        == 4096
    )


def test_gateway_uses_model_specific_output_defaults(monkeypatch):
    _patch_gpu(monkeypatch)

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="Hello",
    )

    decision = gateway.decide(context)

    assert decision.tinyllama_token_capacity.output_token_budget == 512
    assert decision.phi3_token_capacity.output_token_budget == 1024


def test_gateway_uses_explicit_output_budget_for_both_models(monkeypatch):
    _patch_gpu(monkeypatch)

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="Explain Kubernetes architecture.",
        requested_output_tokens=768,
    )

    decision = gateway.decide(context)

    assert decision.output_token_budget == 768
    assert decision.tinyllama_token_capacity.output_token_budget == 768
    assert decision.phi3_token_capacity.output_token_budget == 768


def test_gateway_reports_capacity_status(monkeypatch):
    _patch_gpu(monkeypatch)

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="a" * 5800,
    )

    decision = gateway.decide(context)

    assert decision.tinyllama_token_capacity.status == "HIGH"
    assert (
        decision.tinyllama_token_capacity.has_capacity
        is True
    )

    assert decision.phi3_token_capacity.status == "NORMAL"
    assert (
        decision.phi3_token_capacity.has_capacity
        is True
    )
