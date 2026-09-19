import json
import os
import time
from pathlib import Path

from prometheus_client import Gauge, start_http_server


REPORT_PATH = Path(
    os.getenv(
        "EVALUATION_REPORT",
        "evaluation/reports/model_benchmark.json",
    )
)

PORT = int(os.getenv("EVALUATION_METRICS_PORT", "9108"))


EVALUATION_SCORE = Gauge(
    "evaluation_score",
    "Latest average evaluation score by model.",
    ["model"],
)

EVALUATION_PASS_RATE = Gauge(
    "evaluation_pass_rate",
    "Latest evaluation pass rate by model.",
    ["model"],
)

EVALUATION_LATENCY_SECONDS = Gauge(
    "evaluation_generation_latency_seconds",
    "Average candidate generation latency by model.",
    ["model"],
)

EVALUATION_CASES_TOTAL = Gauge(
    "evaluation_cases_total",
    "Number of evaluation cases by model.",
    ["model"],
)

EVALUATION_GENERATION_TOKENS_TOTAL = Gauge(
    "evaluation_generation_tokens_total",
    "Total candidate generation tokens in the latest benchmark.",
    ["model"],
)


def load_report() -> dict:
    with REPORT_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def update_metrics(report: dict) -> None:
    summary = report.get("summary", {})

    for model, data in summary.items():
        if not isinstance(data, dict):
            continue

        EVALUATION_SCORE.labels(model=model).set(
            float(data.get("average_overall_score", 0.0))
        )

        EVALUATION_PASS_RATE.labels(model=model).set(
            float(data.get("pass_rate", 0.0))
        )

        EVALUATION_LATENCY_SECONDS.labels(model=model).set(
            float(data.get("average_generation_latency_seconds", 0.0))
        )

        EVALUATION_CASES_TOTAL.labels(model=model).set(
            float(data.get("cases", 0))
        )

        EVALUATION_GENERATION_TOKENS_TOTAL.labels(model=model).set(
            float(data.get("total_generation_tokens", 0))
        )


def main() -> None:
    start_http_server(PORT)
    print(f"Evaluation metrics exporter listening on :{PORT}")

    while True:
        try:
            update_metrics(load_report())
        except Exception as exc:
            print(f"Failed to update evaluation metrics: {exc}")

        time.sleep(30)


if __name__ == "__main__":
    main()
