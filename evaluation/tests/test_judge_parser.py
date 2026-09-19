"""Tests for LLM-as-a-Judge parsing and scoring."""

import json

import pytest

from evaluation.judges.llm_judge import (
    build_judge_prompt,
    calculate_overall_score,
    calculate_pass_status,
    parse_judge_response,
)


def valid_judge_response() -> str:
    return json.dumps(
        {
            "correctness": 5,
            "relevance": 4,
            "completeness": 4,
            "instruction_following": 5,
            "evidence": "The response is correct and directly addresses the prompt.",
        }
    )


def test_build_judge_prompt_contains_required_context():
    prompt = build_judge_prompt(
        "What is the capital of France?",
        "Paris",
        "Paris",
    )

    assert "What is the capital of France?" in prompt
    assert "Paris" in prompt
    assert "correctness" in prompt
    assert "instruction_following" in prompt


def test_parse_valid_judge_response():
    result = parse_judge_response(valid_judge_response())

    assert result["correctness"] == 5
    assert result["relevance"] == 4
    assert result["completeness"] == 4
    assert result["instruction_following"] == 5


def test_calculate_overall_score():
    result = parse_judge_response(valid_judge_response())

    assert calculate_overall_score(result) == 4.55


def test_pass_status():
    assert calculate_pass_status(4.55) is True
    assert calculate_pass_status(3.5) is True
    assert calculate_pass_status(3.49) is False


def test_invalid_json_is_rejected():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_judge_response("not json")


def test_missing_field_is_rejected():
    payload = {
        "correctness": 5,
        "relevance": 4,
        "completeness": 4,
        "instruction_following": 5,
    }

    with pytest.raises(ValueError, match="missing required fields"):
        parse_judge_response(json.dumps(payload))


def test_out_of_range_score_is_rejected():
    payload = {
        "correctness": 6,
        "relevance": 4,
        "completeness": 4,
        "instruction_following": 5,
        "evidence": "Invalid score.",
    }

    with pytest.raises(ValueError, match="between 1 and 5"):
        parse_judge_response(json.dumps(payload))


def test_parse_fenced_json_response():
    raw_response = """```json
{
  "correctness": 5,
  "relevance": 5,
  "completeness": 5,
  "instruction_following": 5,
  "evidence": "The response is correct."
}
```"""

    result = parse_judge_response(raw_response)

    assert result["correctness"] == 5
    assert result["relevance"] == 5
    assert result["completeness"] == 5
    assert result["instruction_following"] == 5


def test_parse_structured_evidence():
    payload = {
        "correctness": 5,
        "relevance": 5,
        "completeness": 5,
        "instruction_following": 5,
        "evidence": [
            {
                "question": "What is the capital of France?",
                "response": "Paris.",
                "reference_answer": "Paris.",
            }
        ],
    }

    result = parse_judge_response(json.dumps(payload))

    assert result["correctness"] == 5
    assert isinstance(result["evidence"], str)
    assert "Paris" in result["evidence"]
