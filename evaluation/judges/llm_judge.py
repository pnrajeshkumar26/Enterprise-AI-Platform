"""LLM-as-a-Judge parsing and scoring utilities."""

import json

from evaluation.config import evaluation_config


REQUIRED_FIELDS = {
    "correctness",
    "relevance",
    "completeness",
    "instruction_following",
    "evidence",
}


def build_judge_prompt(
    prompt: str,
    response: str,
    reference_answer: str | None = None,
) -> str:
    """Build a structured rubric prompt for an evaluation judge."""

    reference_section = ""

    if reference_answer:
        reference_section = (
            "\nReference answer:\n"
            f"{reference_answer}\n"
        )

    return f"""
You are an evaluation judge.

Evaluate the model response against the user prompt.

User prompt:
{prompt}

Model response:
{response}
{reference_section}

Score each criterion from 1 to 5:

1. correctness
2. relevance
3. completeness
4. instruction_following

Return ONLY valid JSON with exactly these fields:

{{
  "correctness": 1,
  "relevance": 1,
  "completeness": 1,
  "instruction_following": 1,
  "evidence": "brief evidence supporting the scores"
}}

Do not provide chain-of-thought or hidden reasoning.
Provide only concise evidence.
""".strip()


def parse_judge_response(raw_response: str) -> dict:
    """Parse and validate structured judge JSON."""

    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError("Judge response is not valid JSON") from exc

    missing = REQUIRED_FIELDS - payload.keys()

    if missing:
        raise ValueError(
            f"Judge response is missing required fields: {sorted(missing)}"
        )

    score_fields = [
        "correctness",
        "relevance",
        "completeness",
        "instruction_following",
    ]

    for field in score_fields:
        value = payload[field]

        if not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be numeric")

        if not 1 <= value <= 5:
            raise ValueError(f"{field} must be between 1 and 5")

    if not isinstance(payload["evidence"], str):
        raise ValueError("evidence must be a string")

    return payload


def calculate_overall_score(judge_result: dict) -> float:
    """Calculate the weighted evaluation score from judge dimensions."""

    weights = evaluation_config.rubric_weights

    score = (
        judge_result["correctness"] * weights["correctness"]
        + judge_result["relevance"] * weights["relevance"]
        + judge_result["completeness"] * weights["completeness"]
        + judge_result["instruction_following"]
        * weights["instruction_following"]
    )

    return round(score, 2)


def calculate_pass_status(overall_score: float) -> bool:
    """Determine whether the evaluation meets the configured threshold."""

    return overall_score >= evaluation_config.pass_threshold