from app.services.health_service import health_service
from app.models.model_registry import list_models


def test_health_service():
    result = health_service.get_health()

    assert result["status"] == "healthy"
    assert result["service"] == "runtime-api"
    assert result["version"] == "1.0.0"
    assert result["environment"] == "development"
    assert result["inference_engine"] == "llama.cpp"
    assert result["models_loaded"] == len(list_models())
    assert result["gpu_available"] is False


def test_model_registry():
    models = list_models()

    assert len(models) >= 1
    assert any(model.name == "TinyLlama" for model in models)
