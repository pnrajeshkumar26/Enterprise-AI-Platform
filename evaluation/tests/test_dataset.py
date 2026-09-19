"""Tests for the versioned evaluation dataset."""

import json
from collections import Counter
from pathlib import Path

from evaluation.schemas.evaluation_case import EvaluationCase


DATASET_PATH = (
    Path(__file__).parents[1]
    / "datasets"
    / "v1.0"
    / "evaluation_dataset.jsonl"
)

EXPECTED_CATEGORY_COUNTS = {
    "factual": 10,
    "reasoning": 8,
    "instruction_following": 8,
    "explanation": 5,
    "summarization": 5,
    "safety": 4,
}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}

EXPECTED_CRITERIA = {
    "correctness",
    "relevance",
    "completeness",
    "instruction_following",
}


def load_dataset() -> list[EvaluationCase]:
    cases = []

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                payload = json.loads(line)
                cases.append(EvaluationCase.model_validate(payload))

    return cases


def test_dataset_exists():
    assert DATASET_PATH.exists()


def test_dataset_contains_40_cases():
    cases = load_dataset()

    assert len(cases) == 40


def test_dataset_case_ids_are_unique():
    cases = load_dataset()

    ids = [case.id for case in cases]

    assert len(ids) == len(set(ids))


def test_dataset_category_distribution():
    cases = load_dataset()

    category_counts = Counter(case.category for case in cases)

    assert dict(category_counts) == EXPECTED_CATEGORY_COUNTS


def test_dataset_has_valid_difficulties():
    cases = load_dataset()

    assert all(case.difficulty in VALID_DIFFICULTIES for case in cases)


def test_dataset_has_valid_evaluation_criteria():
    cases = load_dataset()

    for case in cases:
        assert set(case.evaluation_criteria) == EXPECTED_CRITERIA


def test_dataset_contains_reference_and_reference_free_cases():
    cases = load_dataset()

    assert any(case.reference_answer for case in cases)
    assert any(case.reference_answer is None for case in cases)


def test_dataset_prompts_are_non_empty():
    cases = load_dataset()

    assert all(case.prompt.strip() for case in cases)