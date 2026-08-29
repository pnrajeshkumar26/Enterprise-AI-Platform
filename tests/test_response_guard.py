from app.quality.response_guard import ResponseGuard


def test_response_guard_accepts_valid_terminology():
    guard = ResponseGuard()

    result = guard.validate(
        "vLLM is an LLM inference and serving framework."
    )

    assert result.valid is True
    assert result.reason is None


def test_response_guard_rejects_vectorized_vllm():
    guard = ResponseGuard()

    result = guard.validate(
        "vLLM stands for Vectorized Large Language Model."
    )

    assert result.valid is False
    assert "vectorized large language model" in result.reason


def test_response_guard_rejects_low_level_llmops():
    guard = ResponseGuard()

    result = guard.validate(
        "LLMOps means Low-Level Machine Operations."
    )

    assert result.valid is False
    assert "low-level machine operations" in result.reason


def test_response_guard_rejects_empty_response():
    guard = ResponseGuard()

    result = guard.validate("")

    assert result.valid is False
    assert result.reason == "empty response"
