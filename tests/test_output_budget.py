import pytest

from app.routing.output_budget import OutputBudgetPolicy


def test_tinyllama_default_output_budget():
    policy = OutputBudgetPolicy(
        default_by_model={
            "tinyllama": 512,
            "phi3": 1024,
        }
    )

    assert policy.resolve("tinyllama", None) == 512


def test_phi3_default_output_budget():
    policy = OutputBudgetPolicy(
        default_by_model={
            "tinyllama": 512,
            "phi3": 1024,
        }
    )

    assert policy.resolve("phi3", None) == 1024


def test_explicit_output_budget_overrides_default():
    policy = OutputBudgetPolicy(
        default_by_model={
            "tinyllama": 512,
            "phi3": 1024,
        }
    )

    assert policy.resolve("phi3", 768) == 768


def test_zero_output_budget_rejected():
    policy = OutputBudgetPolicy(
        default_by_model={
            "tinyllama": 512,
            "phi3": 1024,
        }
    )

    with pytest.raises(ValueError):
        policy.resolve("phi3", 0)


def test_unknown_model_rejected():
    policy = OutputBudgetPolicy(
        default_by_model={
            "tinyllama": 512,
            "phi3": 1024,
        }
    )

    with pytest.raises(ValueError):
        policy.resolve("unknown", None)
