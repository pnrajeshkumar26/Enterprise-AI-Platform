"""Tests for deterministic evaluation metrics."""

from evaluation.metrics.deterministic import (
    contains_reference_score,
    exact_match_score,
    normalize_text,
    within_word_limit,
    word_count,
)


def test_normalize_text():
    assert normalize_text("  Paris   IS  Beautiful ") == "paris is beautiful"


def test_exact_match():
    assert exact_match_score("Paris", "Paris") == 1.0
    assert exact_match_score("Paris", "London") == 0.0


def test_exact_match_ignores_case_and_whitespace():
    assert exact_match_score("  PARIS  ", "paris") == 1.0


def test_contains_reference():
    response = "The capital of France is Paris."
    assert contains_reference_score(response, "Paris") == 1.0


def test_contains_reference_negative():
    assert contains_reference_score("The capital is London.", "Paris") == 0.0


def test_word_count():
    assert word_count("one two three") == 3


def test_word_limit():
    assert within_word_limit("one two three", 3)
    assert not within_word_limit("one two three four", 3)