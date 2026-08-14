from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise Runtime API"
    app_version: str = "1.0.0"
    app_env: str = "development"

    vllm_url: str = "http://127.0.0.1:8000"

    vllm_model_id: str = (
        "/home/ubuntu/.cache/huggingface/hub/models--microsoft--"
        "Phi-3-mini-4k-instruct/snapshots/"
        "f39ac1d28e925b323eae81227eaba4464caced4e"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
