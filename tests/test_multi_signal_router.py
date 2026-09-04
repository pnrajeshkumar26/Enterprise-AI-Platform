from app.routing.multi_signal_router import MultiSignalRouter
from app.routing.token_capacity import TokenCapacityState


def _state(
    model: str,
    capacity: int,
    total_tokens: int,
    status: str,
) -> TokenCapacityState:
    return TokenCapacityState(
        model=model,
        max_context_tokens=capacity,
        estimated_input_tokens=max(0, total_tokens - 256),
        output_token_budget=256,
        estimated_total_tokens=total_tokens,
        remaining_tokens=capacity - total_tokens,
        utilization_percent=(
            total_tokens / capacity * 100
        ),
        status=status,
    )


def test_base_preference_and_capacity_keep_tinyllama():
    router = MultiSignalRouter()

    result = router.decide(
        base_selected_model="tinyllama",
        tinyllama_capacity=_state(
            "tinyllama",
            2048,
            1000,
            "NORMAL",
        ),
        phi3_capacity=_state(
            "phi3",
            4096,
            1500,
            "NORMAL",
        ),
        tinyllama_avg_latency=0.5,
        phi3_avg_latency=1.2,
        gpu_utilization_percent=20,
        gpu_memory_utilization_percent=20,
        gpu_memory_free_mib=5000,
    )

    assert result.selected_model == "tinyllama"
    assert result.tinyllama_score > result.phi3_score


def test_capacity_can_overcome_base_preference():
    router = MultiSignalRouter()

    result = router.decide(
        base_selected_model="tinyllama",
        tinyllama_capacity=_state(
            "tinyllama",
            2048,
            1900,
            "HIGH",
        ),
        phi3_capacity=_state(
            "phi3",
            4096,
            1900,
            "NORMAL",
        ),
        tinyllama_avg_latency=0.5,
        phi3_avg_latency=1.2,
        gpu_utilization_percent=20,
        gpu_memory_utilization_percent=20,
        gpu_memory_free_mib=5000,
    )

    assert result.selected_model == "phi3"


def test_exceeded_model_is_not_selected():
    router = MultiSignalRouter()

    result = router.decide(
        base_selected_model="tinyllama",
        tinyllama_capacity=_state(
            "tinyllama",
            2048,
            2200,
            "EXCEEDED",
        ),
        phi3_capacity=_state(
            "phi3",
            4096,
            2200,
            "NORMAL",
        ),
        tinyllama_avg_latency=0.5,
        phi3_avg_latency=1.2,
        gpu_utilization_percent=20,
        gpu_memory_utilization_percent=20,
        gpu_memory_free_mib=5000,
    )

    assert result.selected_model == "phi3"


def test_gpu_pressure_favors_tinyllama():
    router = MultiSignalRouter()

    result = router.decide(
        base_selected_model="phi3",
        tinyllama_capacity=_state(
            "tinyllama",
            2048,
            1000,
            "NORMAL",
        ),
        phi3_capacity=_state(
            "phi3",
            4096,
            1000,
            "NORMAL",
        ),
        tinyllama_avg_latency=0.5,
        phi3_avg_latency=0.6,
        gpu_utilization_percent=90,
        gpu_memory_utilization_percent=90,
        gpu_memory_free_mib=1500,
    )

    assert result.selected_model == "tinyllama"


def test_faster_model_gets_latency_advantage():
    router = MultiSignalRouter()

    result = router.decide(
        base_selected_model="phi3",
        tinyllama_capacity=_state(
            "tinyllama",
            2048,
            1000,
            "NORMAL",
        ),
        phi3_capacity=_state(
            "phi3",
            4096,
            1000,
            "NORMAL",
        ),
        tinyllama_avg_latency=0.3,
        phi3_avg_latency=1.5,
        gpu_utilization_percent=20,
        gpu_memory_utilization_percent=20,
        gpu_memory_free_mib=5000,
    )

    assert result.tinyllama_score > result.phi3_score
