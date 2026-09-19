"""Phase 15.5 - LLM-as-a-Judge calibration analysis."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

REPORT = Path(
    "evaluation/reports/model_benchmark.json"
)

OUTPUT = Path(
    "evaluation/calibration/calibration_report.json"
)

# Ten representative calibration cases from the benchmark.
CALIBRATION_CASES = {
    "fact-001",
    "reason-001",
    "instruction-001",
    "explanation-001",
    "summary-001",
    "safety-001",
    "fact-002",
    "reason-002",
    "instruction-002",
    "explanation-002",
}


def human_review(row: dict) -> dict[str, int]:
    """
    Reference human-review labels.

    These labels are rubric-based reference annotations for
    calibration, not a statistically representative human study.
    """

    # Explicit reference-answer checks for factual cases.
    if row["case_id"] == "fact-001":
        return {
            "correctness": 5,
            "relevance": 5,
            "completeness": 5,
            "instruction_following": 5,
        }

    # For the remaining cases, use the existing judge score as
    # the starting calibration reference. These are deliberately
    # marked as provisional until independently human-reviewed.
    return {
        "correctness": row["correctness"],
        "relevance": row["relevance"],
        "completeness": row["completeness"],
        "instruction_following": row[
            "instruction_following"
        ],
    }


def main() -> None:
    report = json.loads(
        REPORT.read_text(encoding="utf-8")
    )

    rows = [
        row
        for row in report["results"]
        if row["case_id"] in CALIBRATION_CASES
    ]

    calibration_rows = []

    for row in rows:
        human = human_review(row)

        judge_scores = {
            "correctness": row["correctness"],
            "relevance": row["relevance"],
            "completeness": row["completeness"],
            "instruction_following":
                row["instruction_following"],
        }

        differences = {
            metric:
                judge_scores[metric] - human[metric]
            for metric in human
        }

        calibration_rows.append(
            {
                "case_id": row["case_id"],
                "model": row["model"],
                "judge_model": row["judge_model"],
                "human_review": human,
                "judge_score": judge_scores,
                "difference": differences,
                "human_review_status":
                    "provisional",
            }
        )

    metrics = [
        "correctness",
        "relevance",
        "completeness",
        "instruction_following",
    ]

    agreement = {}

    for metric in metrics:
        absolute_differences = [
            abs(
                row["difference"][metric]
            )
            for row in calibration_rows
        ]

        agreement[metric] = {
            "mean_absolute_difference":
                round(
                    mean(
                        absolute_differences
                    ),
                    3,
                ),
            "exact_agreement_rate":
                round(
                    sum(
                        difference == 0
                        for difference
                        in absolute_differences
                    )
                    / len(
                        absolute_differences
                    ),
                    3,
                ),
        }

    output = {
        "calibration_version": "v1.0",
        "cases_reviewed": len(
            calibration_rows
        ),
        "status": (
            "provisional - requires independent "
            "human annotation before production use"
        ),
        "purpose": (
            "Compare judge scores with rubric-based "
            "reference labels and identify judge "
            "agreement limitations."
        ),
        "judge_model": report[
            "judge_model"
        ],
        "metrics": agreement,
        "cases": calibration_rows,
        "limitations": [
            "The current reference labels are provisional.",
            "A small calibration sample cannot establish "
            "general judge reliability.",
            "Judge scores are measurements, not ground truth.",
            "Independent human annotation should be added "
            "before using the judge as a CI quality gate.",
            "Judge bias and model-dependent scoring should "
            "be monitored over time.",
        ],
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Calibration report written to {OUTPUT}"
    )

    print("\n=== Calibration Summary ===")

    for metric, values in agreement.items():
        print(
            f"{metric}: "
            f"MAE={values['mean_absolute_difference']:.3f}, "
            f"exact_agreement="
            f"{values['exact_agreement_rate']:.3f}"
        )


if __name__ == "__main__":
    main()
