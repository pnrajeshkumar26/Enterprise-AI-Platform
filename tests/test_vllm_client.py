from app.clients.vllm_client import VLLMClient


def test_vllm_client_uses_enterprise_grounding(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "test response",
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 7,
                    "total_tokens": 12,
                },
            }

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        "app.clients.vllm_client.requests.post",
        fake_post,
    )

    client = VLLMClient(
        "http://enterprise-vllm:8000",
        "microsoft/Phi-3-mini-4k-instruct",
    )

    result = client.generate("What is vLLM?")

    # Stage 2: GenerationResult + token telemetry
    assert result.text == "test response"
    assert result.input_tokens == 5
    assert result.output_tokens == 7
    assert result.total_tokens == 12

    assert captured["url"] == (
        "http://enterprise-vllm:8000/v1/chat/completions"
    )
    assert captured["timeout"] == 60

    payload = captured["json"]

    assert payload["model"] == "microsoft/Phi-3-mini-4k-instruct"

    assert payload["messages"][0]["role"] == "system"

    assert (
        "LLMOps means Large Language Model Operations"
        in payload["messages"][0]["content"]
    )

    assert (
        "vLLM is an LLM inference and serving framework"
        in payload["messages"][0]["content"]
    )

    assert payload["messages"][1] == {
        "role": "user",
        "content": "What is vLLM?",
    }


def test_vllm_client_raises_for_invalid_completion(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": []
            }

    monkeypatch.setattr(
        "app.clients.vllm_client.requests.post",
        lambda url, json, timeout: FakeResponse(),
    )

    client = VLLMClient(
        "http://enterprise-vllm:8000",
        "microsoft/Phi-3-mini-4k-instruct",
    )

    try:
        client.generate("What is vLLM?")
    except ValueError as exc:
        assert "valid completion" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for invalid vLLM response"
    )
