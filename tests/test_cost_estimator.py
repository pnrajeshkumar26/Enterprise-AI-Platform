import pytest

from app.cost.estimator import CostEstimator


def test_cost_estimation():
    estimator = CostEstimator(
        instance_type="g4dn.xlarge",
        hourly_cost_usd=0.579,
    )

    result = estimator.estimate(4.0)

    expected = 0.579 * 4.0 / 3600.0

    assert result.instance_type == "g4dn.xlarge"
    assert result.hourly_cost_usd == 0.579
    assert result.runtime_seconds == 4.0
    assert abs(result.estimated_cost_usd - expected) < 1e-12


def test_zero_runtime_has_zero_cost():
    estimator = CostEstimator(
        instance_type="g4dn.xlarge",
        hourly_cost_usd=0.579,
    )

    result = estimator.estimate(0.0)

    assert result.estimated_cost_usd == 0.0


def test_negative_runtime_is_rejected():
    estimator = CostEstimator(
        instance_type="g4dn.xlarge",
        hourly_cost_usd=0.579,
    )

    with pytest.raises(ValueError):
        estimator.estimate(-1.0)


def test_negative_hourly_cost_is_rejected():
    with pytest.raises(ValueError):
        CostEstimator(
            instance_type="g4dn.xlarge",
            hourly_cost_usd=-0.01,
        )


def test_empty_instance_type_is_rejected():
    with pytest.raises(ValueError):
        CostEstimator(
            instance_type="",
            hourly_cost_usd=0.579,
        )
