from app.gateway.gateway import LLMGateway
from app.gateway.latency import LatencyTracker


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

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="tinyllama",
        prompt="Hello",
    )

    decision = gateway.decide(context)

    assert decision.selected_model == "tinyllama"
    assert decision.tinyllama_avg_latency == 0.5
    assert decision.phi3_avg_latency == 1.5
