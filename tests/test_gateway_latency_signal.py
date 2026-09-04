from app.gateway.gateway import LLMGateway
from app.gateway.latency import LatencyTracker
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


def test_gateway_reads_historical_latency(monkeypatch):
    tracker = LatencyTracker(window_size=3)

    tracker.record("tinyllama", 0.5)
    tracker.record("tinyllama", 0.7)

    tracker.record("phi3", 1.0)
    tracker.record("phi3", 1.2)

    monkeypatch.setattr(
        "app.gateway.gateway.latency_tracker",
        tracker,
    )

    monkeypatch.setattr(
        "app.gateway.gateway.gpu_resource_collector.collect",
        lambda: _test_gpu_state(),
    )

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="What is LLMOps?",
    )

    decision = gateway.decide(context)

    assert decision.tinyllama_avg_latency == 0.6
    assert decision.phi3_avg_latency == 1.1


def test_gateway_has_no_latency_history_initially(monkeypatch):
    tracker = LatencyTracker(window_size=3)

    monkeypatch.setattr(
        "app.gateway.gateway.latency_tracker",
        tracker,
    )

    monkeypatch.setattr(
        "app.gateway.gateway.gpu_resource_collector.collect",
        lambda: _test_gpu_state(),
    )

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="Hello",
    )

    decision = gateway.decide(context)

    assert decision.tinyllama_avg_latency is None
    assert decision.phi3_avg_latency is None


def test_explicit_model_also_receives_latency_signal(monkeypatch):
    tracker = LatencyTracker(window_size=3)

    tracker.record("tinyllama", 0.5)
    tracker.record("phi3", 1.5)

    monkeypatch.setattr(
        "app.gateway.gateway.latency_tracker",
        tracker,
    )

    monkeypatch.setattr(
        "app.gateway.gateway.gpu_resource_collector.collect",
        lambda: _test_gpu_state(),
    )

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="tinyllama",
        prompt="Hello",
    )

    decision = gateway.decide(context)

    assert decision.selected_model == "tinyllama"
    assert decision.tinyllama_avg_latency == 0.5
    assert decision.phi3_avg_latency == 1.5
