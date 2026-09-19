"""vLLM-backed LLM-as-a-Judge client."""

import json
import os
import urllib.error
import urllib.request

from evaluation.judges.base_judge import BaseJudge
from evaluation.judges.llm_judge import (
    build_judge_prompt,
    calculate_overall_score,
    calculate_pass_status,
    parse_judge_response,
)


class VLLMJudge(BaseJudge):
    """Call an OpenAI-compatible vLLM endpoint as an evaluation judge."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ):
        self.base_url = (
            base_url
            or os.getenv("EVAL_JUDGE_URL", "http://localhost:8003/v1")
        ).rstrip("/")
        self.model = model or os.getenv(
            "EVAL_JUDGE_MODEL",
            "Qwen/Qwen2.5-1.5B-Instruct",
        )
        self.timeout = timeout

    def evaluate(
        self,
        prompt: str,
        response: str,
        reference_answer: str | None = None,
    ) -> dict:
        """Evaluate a candidate response using the configured vLLM judge."""
        judge_prompt = build_judge_prompt(
            prompt=prompt,
            response=response,
            reference_answer=reference_answer,
        )

        request_body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an LLM evaluation judge. "
                        "Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": judge_prompt,
                },
            ],
            "temperature": 0,
            "max_tokens": 300,
        }

        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as http_response:
                response_body = json.loads(
                    http_response.read().decode("utf-8")
                )
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Judge endpoint returned HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Unable to reach judge endpoint: {exc.reason}"
            ) from exc

        try:
            raw_content = response_body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                "Judge endpoint returned an unexpected response format"
            ) from exc

        judge_result = parse_judge_response(raw_content)

        overall_score = calculate_overall_score(judge_result)
        passed = calculate_pass_status(overall_score)

        usage = response_body.get("usage", {})

        return {
            **judge_result,
            "overall_score": overall_score,
            "passed": passed,
            "judge_model": self.model,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
