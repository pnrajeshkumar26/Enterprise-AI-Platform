from app.schemas.generate import (
    CostTelemetry,
    GenerateResponse,
    PerformanceTelemetry,
    RoutingExplanation,
    RoutingScoreBreakdown,
    UsageTelemetry,
)


def test_generate_response_accepts_request_telemetry():
    response = GenerateResponse(
        model="Phi-3 Mini",
        response="Kubernetes is a container orchestration platform.",
        status="success",
        usage=UsageTelemetry(
            input_tokens=233,
            output_tokens=70,
            total_tokens=303,
        ),
        performance=PerformanceTelemetry(
            latency_seconds=2.418361772,
        ),
        cost=CostTelemetry(
            estimated_usd=0.000388953185,
        ),
        routing=RoutingExplanation(
            selected_model="phi3",
            reason="multi-signal scores: tinyllama=9.0, phi3=9.0; selected=phi3",
            scores={
                "tinyllama": 9.0,
                "phi3": 9.0,
            },
            breakdown={
                "tinyllama": RoutingScoreBreakdown(
                    base_preference=0.0,
                    capacity=8.0,
                    latency=0.0,
                    gpu_pressure=1.0,
                    total=9.0,
                ),
                "phi3": RoutingScoreBreakdown(
                    base_preference=2.0,
                    capacity=8.0,
                    latency=0.0,
                    gpu_pressure=-1.0,
                    total=9.0,
                ),
            },
        ),
    )

    assert response.model == "Phi-3 Mini"
    assert response.status == "success"

    assert response.usage is not None
    assert response.usage.input_tokens == 233
    assert response.usage.output_tokens == 70
    assert response.usage.total_tokens == 303

    assert response.performance is not None
    assert response.performance.latency_seconds == 2.418361772

    assert response.cost is not None
    assert response.cost.estimated_usd == 0.000388953185

    assert response.routing is not None
    assert response.routing.selected_model == "phi3"
    assert response.routing.scores["phi3"] == 9.0
    assert response.routing.breakdown["tinyllama"].capacity == 8.0


def test_generate_response_keeps_telemetry_optional():
    response = GenerateResponse(
        model="TinyLlama",
        response="Hello",
        status="success",
    )

    assert response.usage is None
    assert response.performance is None
    assert response.cost is None
    assert response.routing is None
