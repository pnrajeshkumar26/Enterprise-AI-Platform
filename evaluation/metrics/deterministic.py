"""Deterministic evaluation metrics."""

import re


def normalize_text(text: str) -> str:
    """Normalize text for simple reference comparison."""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def exact_match_score(response: str, reference: str) -> float:
    """Return 1.0 for an exact normalized match, otherwise 0.0."""
    return float(normalize_text(response) == normalize_text(reference))


def contains_reference_score(response: str, reference: str) -> float:
    """Return 1.0 when the normalized reference appears in the response."""
    normalized_response = normalize_text(response)
    normalized_reference = normalize_text(reference)

    return float(normalized_reference in normalized_response)


def word_count(text: str) -> int:
    """Return the number of whitespace-separated words."""
    return len(text.split())


def within_word_limit(text: str, maximum_words: int) -> bool:
    """Check whether a response stays within a word limit."""
    return word_count(text) <= maximum_words