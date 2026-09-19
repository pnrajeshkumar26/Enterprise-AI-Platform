"""Schema for an individual LLM evaluation case."""

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    """A single test case used to evaluate an LLM response."""

    id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)

    prompt: str = Field(min_length=1)

    reference_answer: str | None = None

    evaluation_criteria: list[str] = Field(
        default_factory=lambda: [
            "correctness",
            "relevance",
            "completeness",
        ]
    )