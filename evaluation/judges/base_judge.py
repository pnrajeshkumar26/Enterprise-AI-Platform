"""Base interface for LLM evaluation judges."""

from abc import ABC, abstractmethod


class BaseJudge(ABC):
    """Interface implemented by evaluation judge backends."""

    @abstractmethod
    def evaluate(
        self,
        prompt: str,
        response: str,
        reference_answer: str | None = None,
    ) -> dict:
        """Evaluate a model response and return structured judge data."""
        raise NotImplementedError