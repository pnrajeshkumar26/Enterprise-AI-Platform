import pytest

from app.routing.capacity_router import CapacityAwareRouter
from app.routing.token_capacity import TokenCapacityState


def _state(
    model: str,
    capacity: int,
    estimated_total: int,
    status: str,
) -> TokenCapacityState:
    return TokenCapacityState(
        model=model,
        max_context_tokens=capacity,
        estimated_input_tokens=estimated_total - 256,
        output_token_budget=256,
        estimated_total_tokens=estimated_total,
        remaining_tokens=capacity - estimated_total,
        utilization_percent=(
            estimated_total / capacity * 100
        ),
        status=status,
    )


def test_keeps_base_model_when_capacity_is_available():
    router = CapacityAwareRouter()

    result = router.select(
        requested_model="auto",
        base_selected_model="tinyllama",
        tinyllama_capacity=_state(
            "tinyllama",
            2048,
            1200,
            "NORMAL",
        ),
        phi3_capacity=_state(
            "phi3",
            4096,
            1800,
            "NORMAL",
        ),
    )

    assert result.selected_model == "tinyllama"
    assert result.overridden is False


def test_falls_back_to_phi3_when_tinyllama_exceeds_capacity():
    router = CapacityAwareRouter()

    result = router.select(
        requested_model="auto",
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
    )

    assert result.selected_model == "phi3"
    assert result.overridden is True
    assert "capacity override" in result.reason


def test_explicit_model_is_not_silently_changed():
    router = CapacityAwareRouter()

    with pytest.raises(ValueError):
        router.select(
            requested_model="tinyllama",
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
        )


def test_both_models_exceeded():
    router = CapacityAwareRouter()

    with pytest.raises(ValueError):
        router.select(
            requested_model="auto",
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
                4500,
                "EXCEEDED",
            ),
        )


def test_phi3_can_remain_selected_when_capacity_is_available():
    router = CapacityAwareRouter()

    result = router.select(
        requested_model="auto",
        base_selected_model="phi3",
        tinyllama_capacity=_state(
            "tinyllama",
            2048,
            1200,
            "NORMAL",
        ),
        phi3_capacity=_state(
            "phi3",
            4096,
            2500,
            "NORMAL",
        ),
    )

    assert result.selected_model == "phi3"
    assert result.overridden is False
