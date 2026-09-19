"""Prometheus metrics for offline LLM evaluation."""

from prometheus_client import Counter, Gauge, Histogram


EVALUATION_REQUESTS_TOTAL = Counter(
    "evaluation_requests_total",
    "Total number of LLM evaluation requests.",
    ["model", "judge_model", "category"],
)

EVALUATION_PASS_TOTAL = Counter(
    "evaluation_pass_total",
    "Total number of evaluation results that passed.",
    ["model", "judge_model", "category"],
)

EVALUATION_SCORE = Gauge(
    "evaluation_score",
    "Latest LLM-as-a-Judge overall score.",
    ["model", "judge_model", "category"],
)

EVALUATION_LATENCY_SECONDS = Histogram(
    "evaluation_latency_seconds",
    "LLM-as-a-Judge evaluation latency.",
    ["model", "judge_model"],
)

EVALUATION_INPUT_TOKENS_TOTAL = Counter(
    "evaluation_input_tokens_total",
    "Total judge input tokens.",
    ["judge_model"],
)

EVALUATION_OUTPUT_TOKENS_TOTAL = Counter(
    "evaluation_output_tokens_total",
    "Total judge output tokens.",
    ["judge_model"],
)


def record_evaluation_metrics(
    *,
    model: str,
    judge_model: str,
    category: str,
    score: float,
    passed: bool,
    latency_seconds: float,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Record one completed evaluation."""

    EVALUATION_REQUESTS_TOTAL.labels(
        model=model,
        judge_model=judge_model,
        category=category,
    ).inc()

    if passed:
        EVALUATION_PASS_TOTAL.labels(
            model=model,
            judge_model=judge_model,
            category=category,
        ).inc()

    EVALUATION_SCORE.labels(
        model=model,
        judge_model=judge_model,
        category=category,
    ).set(score)

    EVALUATION_LATENCY_SECONDS.labels(
        model=model,
        judge_model=judge_model,
    ).observe(latency_seconds)

    EVALUATION_INPUT_TOKENS_TOTAL.labels(
        judge_model=judge_model,
    ).inc(input_tokens)

    EVALUATION_OUTPUT_TOKENS_TOTAL.labels(
        judge_model=judge_model,
    ).inc(output_tokens)
