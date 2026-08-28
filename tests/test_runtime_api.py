from app.models.model_registry import list_models
from app.services.health_service import health_service


def test_health_service():
    result = health_service.get_health()

    assert result["status"] == "healthy"
    assert result["service"] == "runtime-api"
    assert result["version"] == "1.0.0"
    assert result["environment"] == "development"
    assert result["inference_engine"] == "orchestrator"
    assert result["models_configured"] == len(list_models())
    assert result["gpu_available"] is None


def test_model_registry():
    models = list_models()

    assert len(models) >= 1
    assert any(model.name == "TinyLlama" for model in models)
    assert any(model.name == "Phi-3 Mini" for model in models)
