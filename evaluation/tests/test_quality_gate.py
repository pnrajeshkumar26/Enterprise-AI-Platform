import json

from evaluation.quality_gate import evaluate_gate


def write_report(tmp_path, model, score):
    report = {
        "dataset_version": "v1.0",
        "summary": {
            model: {
                "cases": 10,
                "average_overall_score": score,
                "pass_rate": 0.8,
            }
        },
    }

    path = tmp_path / "report.json"
    path.write_text(
        json.dumps(report),
        encoding="utf-8",
    )
    return path


def test_quality_gate_passes(tmp_path):
    report = write_report(tmp_path, "phi3", 4.2)

    result = evaluate_gate(
        report_path=report,
        model="phi3",
        min_score=3.5,
    )

    assert result == 0


def test_quality_gate_fails_below_threshold(tmp_path):
    report = write_report(tmp_path, "tinyllama", 3.4)

    result = evaluate_gate(
        report_path=report,
        model="tinyllama",
        min_score=3.5,
    )

    assert result == 1
