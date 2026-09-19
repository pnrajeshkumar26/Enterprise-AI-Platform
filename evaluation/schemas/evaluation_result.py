"""Schema for structured LLM evaluation results."""

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Structured result produced by the evaluation pipeline."""

    evaluation_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    case_id: str = Field(min_length=1)

    model: str = Field(min_length=1)
    judge_model: str = Field(min_length=1)

    correctness: float = Field(ge=1.0, le=5.0)
    relevance: float = Field(ge=1.0, le=5.0)
    completeness: float = Field(ge=1.0, le=5.0)
    instruction_following: float = Field(ge=1.0, le=5.0)

    overall_score: float = Field(ge=1.0, le=5.0)
    passed: bool

    evidence: str = Field(min_length=1)

    latency_seconds: float = Field(ge=0.0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)