"""Configuration for the Phase 15 LLM evaluation framework."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationConfig:
    """Evaluation settings shared across the evaluation pipeline."""

    dataset_version: str = "v1.0"

    # Dedicated evaluation judge model.
    # This model is separate from the production/runtime routing candidates.
    judge_model: str = "Qwen/Qwen2.5-1.5B-Instruct"

    # Rubric weights.
    correctness_weight: float = 0.40
    relevance_weight: float = 0.25
    completeness_weight: float = 0.20
    instruction_following_weight: float = 0.15

    # Initial pass threshold on a 1-5 scale.
    pass_threshold: float = 3.5

    @property
    def rubric_weights(self) -> dict[str, float]:
        """Return rubric weights as a named mapping."""
        return {
            "correctness": self.correctness_weight,
            "relevance": self.relevance_weight,
            "completeness": self.completeness_weight,
            "instruction_following": self.instruction_following_weight,
        }


evaluation_config = EvaluationConfig()