import os

import pytest
import requests


pytestmark = pytest.mark.e2e


def e2e_enabled():
    return os.getenv("RUN_E2E", "").lower() in {
        "1",
        "true",
        "yes",
    }


@pytest.mark.skipif(
    not e2e_enabled(),
    reason="Set RUN_E2E=1 to run live E2E smoke tests",
)
def test_runtime_api_live_health():
    base_url = os.getenv(
        "RUNTIME_API_URL",
        "http://127.0.0.1:8001",
    )

    response = requests.get(
        f"{base_url}/health",
        timeout=10,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["service"] == "runtime-api"


@pytest.mark.skipif(
    not e2e_enabled(),
    reason="Set RUN_E2E=1 to run live E2E smoke tests",
)
def test_streamlit_live_health():
    response = requests.get(
        "http://127.0.0.1:8501/_stcore/health",
        timeout=10,
    )

    assert response.status_code == 200


@pytest.mark.skipif(
    not e2e_enabled(),
    reason="Set RUN_E2E=1 to run live E2E smoke tests",
)
def test_prometheus_live_health():
    response = requests.get(
        "http://127.0.0.1:9090/-/healthy",
        timeout=10,
    )

    assert response.status_code == 200
