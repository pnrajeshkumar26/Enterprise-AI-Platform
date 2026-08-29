from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "runtime-api"))

from app.routing.model_router import model_router


def test_simple_factual_kubernetes_request_routes_to_phi3():
    decision = model_router.route("What is Kubernetes?")

    assert decision.selected_model == "phi3"


def test_simple_factual_docker_request_routes_to_phi3():
    decision = model_router.route("What is Docker?")

    assert decision.selected_model == "phi3"


def test_casual_request_routes_to_tinyllama():
    decision = model_router.route(
        "Tell me a short joke about software engineers."
    )

    assert decision.selected_model == "tinyllama"


def test_prometheus_question_routes_to_phi3():
    decision = model_router.route(
        "Explain why Prometheus is useful in LLMOps."
    )

    assert decision.selected_model == "phi3"


def test_complex_llmops_request_routes_to_phi3():
    prompt = (
        "Analyze an enterprise LLMOps architecture using llama.cpp "
        "and vLLM on a Tesla T4, discuss GPU memory management, "
        "automatic model routing, failure recovery, latency monitoring, "
        "and Prometheus/Grafana observability."
    )

    decision = model_router.route(prompt)

    assert decision.selected_model == "phi3"


def test_complex_routing_is_deterministic():
    prompt = (
        "Analyze an enterprise LLMOps architecture using llama.cpp "
        "and vLLM on a Tesla T4, discuss GPU memory management, "
        "automatic model routing, failure recovery, latency monitoring, "
        "and Prometheus/Grafana observability."
    )

    first = model_router.route(prompt)
    second = model_router.route(prompt)

    assert first.selected_model == second.selected_model
    assert first.score == second.score
    assert first.reason == second.reason
