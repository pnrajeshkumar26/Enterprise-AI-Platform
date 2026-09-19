import json
from unittest.mock import patch

from evaluation.judges.vllm_judge import VLLMJudge


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_vllm_judge_evaluate():
    judge_response = {
        "choices": [
            {
                "message": {
                    "content": """```json
{
  "correctness": 5,
  "relevance": 5,
  "completeness": 4,
  "instruction_following": 5,
  "evidence": "The answer is correct and directly addresses the question."
}
```"""
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }

    with patch(
        "urllib.request.urlopen",
        return_value=FakeHTTPResponse(judge_response),
    ) as mock_urlopen:
        judge = VLLMJudge(
            base_url="http://localhost:8003/v1",
            model="Qwen/Qwen2.5-1.5B-Instruct",
        )

        result = judge.evaluate(
            prompt="What is the capital of France?",
            response="Paris.",
            reference_answer="Paris",
        )

    mock_urlopen.assert_called_once()

    assert result["correctness"] == 5
    assert result["relevance"] == 5
    assert result["completeness"] == 4
    assert result["instruction_following"] == 5

    assert result["overall_score"] == 4.8
    assert result["passed"] is True

    assert result["judge_model"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert result["input_tokens"] == 100
    assert result["output_tokens"] == 50
    assert result["total_tokens"] == 150


def test_vllm_judge_uses_environment_configuration():
    with patch.dict(
        "os.environ",
        {
            "EVAL_JUDGE_URL": "http://example:9000/v1",
            "EVAL_JUDGE_MODEL": "test-model",
        },
    ):
        judge = VLLMJudge()

    assert judge.base_url == "http://example:9000/v1"
    assert judge.model == "test-model"
