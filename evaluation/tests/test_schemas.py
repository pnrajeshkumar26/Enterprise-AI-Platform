"""Tests for Phase 15 evaluation schemas."""

from evaluation.schemas.evaluation_case import EvaluationCase
from evaluation.schemas.evaluation_result import EvaluationResult


def test_evaluation_case_defaults():
    case = EvaluationCase(
        id="fact-001",
        category="factual",
        difficulty="easy",
        prompt="What is the capital of France?",
        reference_answer="Paris",
    )

    assert case.id == "fact-001"
    assert case.category == "factual"
    assert case.reference_answer == "Paris"
    assert case.evaluation_criteria == [
        "correctness",
        "relevance",
        "completeness",
    ]


def test_evaluation_result():
    result = EvaluationResult(
        evaluation_id="eval-0001",
        dataset_version="v1.0",
        case_id="fact-001",
        model="phi3",
        judge_model="qwen",
        correctness=5,
        relevance=5,
        completeness=4,
        instruction_following=5,
        overall_score=4.75,
        passed=True,
        evidence="The answer is correct and directly addresses the question.",
        latency_seconds=1.82,
        input_tokens=24,
        output_tokens=31,
        estimated_cost_usd=0.0008,
    )

    assert result.overall_score == 4.75
    assert result.passed is True
    assert result.model == "phi3"
    assert result.judge_model == "qwen"


def test_evaluation_result_rejects_invalid_score():
    try:
        EvaluationResult(
            evaluation_id="eval-invalid",
            dataset_version="v1.0",
            case_id="fact-001",
            model="phi3",
            judge_model="qwen",
            correctness=6,
            relevance=5,
            completeness=4,
            instruction_following=5,
            overall_score=4.75,
            passed=True,
            evidence="Invalid score test.",
            latency_seconds=1.0,
            input_tokens=10,
            output_tokens=10,
            estimated_cost_usd=0.001,
        )
    except Exception:
        return

    raise AssertionError("Expected invalid score to be rejected")