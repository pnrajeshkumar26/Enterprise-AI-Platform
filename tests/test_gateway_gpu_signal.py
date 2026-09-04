from app.gateway.gateway import LLMGateway
from app.gateway.latency import LatencyTracker
from app.resources.gpu_collector import GPUResourceCollector
from app.resources.gpu_state import GPUResourceState


def test_gateway_reads_gpu_resource_state(monkeypatch):
    tracker = LatencyTracker(window_size=3)

    gpu_state = GPUResourceState(
        gpu_name="Tesla T4",
        gpu_utilization_percent=42.0,
        memory_utilization_percent=18.0,
        memory_total_mib=15360.0,
        memory_used_mib=12000.0,
        memory_free_mib=3360.0,
        temperature_celsius=40.0,
    )

    monkeypatch.setattr(
        "app.gateway.gateway.latency_tracker",
        tracker,
    )

    monkeypatch.setattr(
        "app.gateway.gateway.gpu_resource_collector",
        GPUResourceCollector(),
    )

    monkeypatch.setattr(
        "app.gateway.gateway.gpu_resource_collector.collect",
        lambda: gpu_state,
    )

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="Hello",
    )

    decision = gateway.decide(context)

    assert decision.gpu_name == "Tesla T4"
    assert decision.gpu_utilization_percent == 42.0
    assert decision.gpu_memory_utilization_percent == 18.0
    assert decision.gpu_memory_total_mib == 15360.0
    assert decision.gpu_memory_used_mib == 12000.0
    assert decision.gpu_memory_free_mib == 3360.0


def test_gateway_preserves_existing_model_selection(monkeypatch):
    gpu_state = GPUResourceState(
        gpu_name="Tesla T4",
        gpu_utilization_percent=95.0,
        memory_utilization_percent=95.0,
        memory_total_mib=15360.0,
        memory_used_mib=15000.0,
        memory_free_mib=360.0,
    )

    monkeypatch.setattr(
        "app.gateway.gateway.gpu_resource_collector.collect",
        lambda: gpu_state,
    )

    gateway = LLMGateway()

    context = gateway.create_context(
        requested_model="auto",
        prompt="What is Kubernetes?",
    )

    decision = gateway.decide(context)

    assert decision.selected_model == "phi3"
    assert decision.routing_score == 3
    assert decision.gpu_utilization_percent == 95.0
    assert decision.gpu_memory_free_mib == 360.0
