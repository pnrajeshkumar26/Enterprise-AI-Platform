"""Fast model benchmark for Phase 15 evaluation."""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

from evaluation.judges.vllm_judge import VLLMJudge


DATASET = (
    Path(__file__).resolve().parent
    / "datasets"
    / "v1.0"
    / "evaluation_dataset.jsonl"
)

RUNTIME_URL = os.getenv(
    "EVAL_RUNTIME_URL",
    "http://127.0.0.1:8001",
)

JUDGE_URL = os.getenv(
    "EVAL_JUDGE_URL",
    "http://127.0.0.1:8003/v1",
)

JUDGE_MODEL = os.getenv(
    "EVAL_JUDGE_MODEL",
    "Qwen/Qwen2.5-1.5B-Instruct",
)

RESPONSES_FILE = Path(
    "evaluation/reports/candidate_responses.jsonl"
)

BENCHMARK_FILE = Path(
    "evaluation/reports/model_benchmark.json"
)


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = []

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if line:
                cases.append(json.loads(line))

    if not cases:
        raise ValueError(f"No cases found in {path}")

    return cases


def select_cases(
    cases: list[dict[str, Any]],
    limit: int | None,
) -> list[dict[str, Any]]:
    """Select a balanced subset across categories."""

    if limit is None or limit >= len(cases):
        return cases

    grouped = defaultdict(list)

    for case in cases:
        grouped[case["category"]].append(case)

    categories = list(grouped)
    selected = []
    index = 0

    while len(selected) < limit:
        category = categories[index % len(categories)]

        if grouped[category]:
            selected.append(grouped[category].pop(0))

        index += 1

        if (
            index >= len(categories)
            and not any(grouped.values())
        ):
            break

    return selected


def generate(
    session: requests.Session,
    model: str,
    prompt: str,
    max_output_tokens: int,
    timeout: float,
) -> dict[str, Any]:

    started = time.perf_counter()

    response = session.post(
        f"{RUNTIME_URL.rstrip('/')}/generate",
        json={
            "model": model,
            "prompt": prompt,
            "max_output_tokens": max_output_tokens,
        },
        timeout=timeout,
    )

    response.raise_for_status()

    data = response.json()

    data["_client_latency_seconds"] = (
        time.perf_counter() - started
    )

    return data


def generate_candidates(
    cases: list[dict[str, Any]],
    model: str,
    max_output_tokens: int,
    timeout: float,
    output: Path,
) -> None:
    """Generate candidate responses without loading the judge."""

    session = requests.Session()

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Replace existing entries for this model while
    # preserving responses from the other candidate.
    existing = []

    if output.exists():
        with output.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()

                if line:
                    row = json.loads(line)

                    if row.get("model") != model:
                        existing.append(row)

    generated_rows = []

    for index, case in enumerate(cases, start=1):

        print(
            f"[{index}/{len(cases)}] "
            f"[{model}] {case['id']}",
            flush=True,
        )

        generated = generate(
            session=session,
            model=model,
            prompt=case["prompt"],
            max_output_tokens=max_output_tokens,
            timeout=timeout,
        )

        response_text = (
            generated.get("response", "")
            .strip()
        )

        if not response_text:
            raise ValueError(
                f"Empty response: {model}/{case['id']}"
            )

        usage = generated.get("usage") or {}

        generated_rows.append(
            {
                "evaluation_id": str(uuid.uuid4()),
                "case_id": case["id"],
                "category": case["category"],
                "difficulty": case.get("difficulty"),
                "prompt": case["prompt"],
                "reference_answer": case.get(
                    "reference_answer"
                ),
                "evaluation_criteria": case.get(
                    "evaluation_criteria",
                    [],
                ),
                "model": model,
                "response": response_text,
                "generation_latency_seconds":
                    generated.get(
                        "performance",
                        {},
                    ).get(
                        "latency_seconds",
                        generated[
                            "_client_latency_seconds"
                        ],
                    ),
                "generation_input_tokens":
                    usage.get(
                        "input_tokens",
                        0,
                    ),
                "generation_output_tokens":
                    usage.get(
                        "output_tokens",
                        0,
                    ),
                "generation_total_tokens":
                    usage.get(
                        "total_tokens",
                        0,
                    ),
                "generation_estimated_cost_usd":
                    generated.get(
                        "cost",
                        {},
                    ).get(
                        "estimated_usd",
                        0.0,
                    ),
            }
        )

    with output.open(
        "w",
        encoding="utf-8",
    ) as handle:

        for row in existing + generated_rows:
            handle.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(
        f"\nSaved {len(generated_rows)} "
        f"{model} responses to {output}"
    )


def load_candidate_responses(
    path: Path,
) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Candidate response file not found: {path}"
        )

    rows = []

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if line:
                rows.append(json.loads(line))

    if not rows:
        raise ValueError(
            f"No candidate responses found in {path}"
        )

    return rows


def aggregate(
    results: list[dict[str, Any]],
) -> dict[str, Any]:

    by_model = defaultdict(list)

    for result in results:
        by_model[result["model"]].append(result)

    summary = {}

    for model, rows in by_model.items():

        count = len(rows)

        summary[model] = {
            "cases": count,

            "average_overall_score": round(
                sum(r["overall_score"] for r in rows)
                / count,
                3,
            ),

            "pass_rate": round(
                sum(bool(r["passed"]) for r in rows)
                / count,
                3,
            ),

            "average_correctness": round(
                sum(r["correctness"] for r in rows)
                / count,
                3,
            ),

            "average_relevance": round(
                sum(r["relevance"] for r in rows)
                / count,
                3,
            ),

            "average_completeness": round(
                sum(r["completeness"] for r in rows)
                / count,
                3,
            ),

            "average_instruction_following": round(
                sum(
                    r["instruction_following"]
                    for r in rows
                )
                / count,
                3,
            ),

            "average_generation_latency_seconds": round(
                sum(
                    r["generation_latency_seconds"]
                    for r in rows
                )
                / count,
                3,
            ),

            "total_generation_tokens": sum(
                r["generation_total_tokens"]
                for r in rows
            ),

            "total_judge_tokens": sum(
                r.get("judge_input_tokens", 0)
                + r.get("judge_output_tokens", 0)
                for r in rows
            ),
        }

    return summary


def judge_candidates(
    responses: list[dict[str, Any]],
    timeout: float,
    output: Path,
) -> None:
    """Judge saved candidate responses using Qwen."""

    judge = VLLMJudge(
        base_url=JUDGE_URL,
        model=JUDGE_MODEL,
        timeout=timeout,
    )

    results = []

    print(
        f"Judging {len(responses)} saved candidate responses "
        f"with {JUDGE_MODEL}",
        flush=True,
    )

    for index, candidate in enumerate(
        responses,
        start=1,
    ):

        print(
            f"[{index}/{len(responses)}] "
            f"[{candidate['model']}] "
            f"{candidate['case_id']}",
            flush=True,
        )

        judged = judge.evaluate(
            prompt=candidate["prompt"],
            response=candidate["response"],
            reference_answer=candidate.get(
                "reference_answer"
            ),
        )

        results.append(
            {
                "evaluation_id":
                    candidate["evaluation_id"],

                "case_id":
                    candidate["case_id"],

                "category":
                    candidate["category"],

                "difficulty":
                    candidate.get("difficulty"),

                "model":
                    candidate["model"],

                "judge_model":
                    JUDGE_MODEL,

                "correctness":
                    judged["correctness"],

                "relevance":
                    judged["relevance"],

                "completeness":
                    judged["completeness"],

                "instruction_following":
                    judged["instruction_following"],

                "overall_score":
                    judged["overall_score"],

                "passed":
                    judged["passed"],

                "evidence":
                    judged["evidence"],

                "generation_latency_seconds":
                    candidate[
                        "generation_latency_seconds"
                    ],

                "generation_input_tokens":
                    candidate[
                        "generation_input_tokens"
                    ],

                "generation_output_tokens":
                    candidate[
                        "generation_output_tokens"
                    ],

                "generation_total_tokens":
                    candidate[
                        "generation_total_tokens"
                    ],

                "generation_estimated_cost_usd":
                    candidate[
                        "generation_estimated_cost_usd"
                    ],

                "judge_input_tokens":
                    judged.get(
                        "judge_input_tokens",
                        0,
                    ),

                "judge_output_tokens":
                    judged.get(
                        "judge_output_tokens",
                        0,
                    ),
            }
        )

    models = sorted(
        {
            row["model"]
            for row in results
        }
    )

    report = {
        "benchmark_id":
            str(uuid.uuid4()),

        "dataset_version":
            "v1.0",

        "cases":
            len(results),

        "candidate_models":
            models,

        "judge_model":
            JUDGE_MODEL,

        "summary":
            aggregate(results),

        "results":
            results,
    }

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"\nBenchmark report written to {output}"
    )

    print("\n=== Benchmark Summary ===")

    for model, summary in report[
        "summary"
    ].items():

        print(
            f"{model}: "
            f"score={summary['average_overall_score']:.3f}, "
            f"pass_rate={summary['pass_rate']:.3f}, "
            f"correctness={summary['average_correctness']:.3f}, "
            f"relevance={summary['average_relevance']:.3f}, "
            f"completeness={summary['average_completeness']:.3f}, "
            f"instruction_following="
            f"{summary['average_instruction_following']:.3f}, "
            f"latency="
            f"{summary['average_generation_latency_seconds']:.3f}s"
        )


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--phase",
        choices=[
            "generate",
            "judge",
        ],
        default="generate",
        help=(
            "generate candidate responses or "
            "judge saved responses"
        ),
    )

    parser.add_argument(
        "--model",
        choices=[
            "tinyllama",
            "phi3",
        ],
        help=(
            "Candidate model for generation phase"
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=128,
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
    )

    parser.add_argument(
        "--responses",
        type=Path,
        default=RESPONSES_FILE,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=BENCHMARK_FILE,
    )

    args = parser.parse_args()

    if args.phase == "generate":

        if not args.model:
            parser.error(
                "--model is required when "
                "--phase generate is used"
            )

        cases = load_cases(DATASET)

        cases = select_cases(
            cases,
            args.limit,
        )

        print(
            f"Generating {len(cases)} cases "
            f"with {args.model}"
        )

        generate_candidates(
            cases=cases,
            model=args.model,
            max_output_tokens=args.max_output_tokens,
            timeout=args.timeout,
            output=args.responses,
        )

    else:

        responses = load_candidate_responses(
            args.responses
        )

        judge_candidates(
            responses=responses,
            timeout=args.timeout,
            output=args.output,
        )


if __name__ == "__main__":
    main()
