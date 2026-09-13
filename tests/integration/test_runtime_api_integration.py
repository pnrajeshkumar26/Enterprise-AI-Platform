import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.integration
def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["service"] == "runtime-api"


@pytest.mark.integration
def test_models_endpoint(client):
    response = client.get("/models")

    assert response.status_code == 200

    payload = response.json()

    assert payload


@pytest.mark.integration
def test_generate_validation_rejects_zero_output_budget(client):
    response = client.post(
        "/generate",
        json={
            "model": "auto",
            "prompt": "test",
            "max_output_tokens": 0,
        },
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_generate_validation_rejects_missing_prompt(client):
    response = client.post(
        "/generate",
        json={
            "model": "auto",
            "max_output_tokens": 10,
        },
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_metrics_endpoint(client):
    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.text

    assert "llm_requests_total" in body
    assert "llm_routing_selected_models_total" in body
