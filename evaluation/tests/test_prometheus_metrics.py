from evaluation.metrics.prometheus import (
    record_evaluation_metrics,
)


def test_record_evaluation_metrics():
    # Smoke-test the metric recording path.
    record_evaluation_metrics(
        model="tinyllama",
        judge_model="Qwen/Qwen2.5-1.5B-Instruct",
        category="factual",
        score=4.0,
        passed=True,
        latency_seconds=0.5,
        input_tokens=50,
        output_tokens=20,
    )
