import argparse
import json
import sys
from pathlib import Path

from evaluation.config import evaluation_config


def evaluate_gate(
    report_path: Path,
    model: str,
    min_score: float,
) -> int:
    if not report_path.exists():
        print(f"QUALITY GATE: FAIL")
        print(f"Report not found: {report_path}")
        return 1

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("QUALITY GATE: FAIL")
        print(f"Unable to read evaluation report: {exc}")
        return 1

    dataset_version = report.get("dataset_version")
    expected_dataset_version = evaluation_config.dataset_version

    if dataset_version != expected_dataset_version:
        print("QUALITY GATE: FAIL")
        print(
            f"Dataset version mismatch: "
            f"report={dataset_version}, "
            f"expected={expected_dataset_version}"
        )
        return 1

    summary = report.get("summary", {})
    model_result = summary.get(model)

    if not isinstance(model_result, dict):
        print("QUALITY GATE: FAIL")
        print(f"No benchmark summary found for model: {model}")
        return 1

    cases = int(model_result.get("cases", 0))
    score = float(model_result.get("average_overall_score", 0.0))
    pass_rate = float(model_result.get("pass_rate", 0.0))

    if cases <= 0:
        print("QUALITY GATE: FAIL")
        print(f"Model {model} has no evaluated cases.")
        return 1

    print("=== Evaluation Quality Gate ===")
    print(f"Model:             {model}")
    print(f"Dataset version:   {dataset_version}")
    print(f"Cases:             {cases}")
    print(f"Average score:     {score:.3f}")
    print(f"Pass rate:         {pass_rate:.3f}")
    print(f"Minimum score:     {min_score:.3f}")

    if score < min_score:
        print()
        print("QUALITY GATE: FAIL")
        print(
            f"Average score {score:.3f} is below "
            f"required threshold {min_score:.3f}."
        )
        return 1

    print()
    print("QUALITY GATE: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the LLM evaluation quality gate."
    )
    parser.add_argument(
        "--report",
        default="evaluation/reports/model_benchmark.json",
        help="Path to the evaluation benchmark report.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Candidate model to gate.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=evaluation_config.pass_threshold,
        help="Minimum acceptable average evaluation score.",
    )

    args = parser.parse_args()

    return evaluate_gate(
        report_path=Path(args.report),
        model=args.model,
        min_score=args.min_score,
    )


if __name__ == "__main__":
    sys.exit(main())
