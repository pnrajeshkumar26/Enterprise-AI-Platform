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
                ]
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

    assert result == "test response"

    payload = captured["json"]

    assert payload["model"] == "microsoft/Phi-3-mini-4k-instruct"
    assert payload["max_tokens"] == 256
    assert payload["temperature"] == 0.2
    assert payload["top_p"] == 0.9

    assert payload["messages"][0]["role"] == "system"

    system_prompt = payload["messages"][0]["content"]

    assert "LLMOps means Large Language Model Operations." in system_prompt
    assert "vLLM is an LLM inference and serving framework." in system_prompt
    assert "llama.cpp is a C/C++ library for running LLMs." in system_prompt
    assert "Prometheus is a metrics and time-series monitoring system." in system_prompt
    assert "Grafana is an observability and visualization platform." in system_prompt
    assert "Kubernetes is an open-source container orchestration platform." in system_prompt
    assert "NVIDIA Tesla T4 has 16 GB of GDDR6 GPU memory." in system_prompt
