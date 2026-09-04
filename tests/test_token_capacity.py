import pytest

from app.routing.token_capacity import TokenCapacityEvaluator


def test_tinyllama_capacity_is_2048():
    evaluator = TokenCapacityEvaluator()

    state = evaluator.evaluate(
        model="tinyllama",
        prompt="hello",
        output_token_budget=256,
    )

    assert state.max_context_tokens == 2048
    assert state.has_capacity is True


def test_phi3_capacity_is_4096():
    evaluator = TokenCapacityEvaluator()

    state = evaluator.evaluate(
        model="phi3",
        prompt="hello",
        output_token_budget=256,
    )

    assert state.max_context_tokens == 4096
    assert state.has_capacity is True


def test_warning_state():
    evaluator = TokenCapacityEvaluator()

    prompt = "a" * 6000

    state = evaluator.evaluate(
        model="tinyllama",
        prompt=prompt,
        output_token_budget=256,
    )

    assert state.status == "WARNING"
    assert state.utilization_percent >= 80


def test_high_state():
    evaluator = TokenCapacityEvaluator()

    prompt = "a" * 7000

    state = evaluator.evaluate(
        model="tinyllama",
        prompt=prompt,
        output_token_budget=256,
    )

    assert state.status == "HIGH"
    assert state.is_high is True


def test_exceeded_state():
    evaluator = TokenCapacityEvaluator()

    prompt = "a" * 9000

    state = evaluator.evaluate(
        model="tinyllama",
        prompt=prompt,
        output_token_budget=256,
    )

    assert state.status == "EXCEEDED"
    assert state.has_capacity is False
    assert state.remaining_tokens < 0


def test_unknown_model_rejected():
    evaluator = TokenCapacityEvaluator()

    with pytest.raises(ValueError):
        evaluator.evaluate(
            model="unknown",
            prompt="hello",
        )


def test_negative_output_budget_rejected():
    evaluator = TokenCapacityEvaluator()

    with pytest.raises(ValueError):
        evaluator.evaluate(
            model="tinyllama",
            prompt="hello",
            output_token_budget=-1,
        )
