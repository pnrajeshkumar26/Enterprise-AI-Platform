from app.models.model_registry import (
    list_models,
    get_model,
)


class ModelService:

    def list_models(self):
        return list_models()

    def get_model(self, model_name: str):
        return get_model(model_name)


model_service = ModelService()