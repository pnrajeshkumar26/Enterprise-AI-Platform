from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "Enterprise Runtime API"
    app_version: str = "1.0.0"
    app_env: str = "development"

    # Kubernetes Service name for vLLM
    vllm_url: str = "http://vllm:8000"

    # Must match the model ID exposed by vLLM
    vllm_model_id: str = "microsoft/Phi-3-mini-4k-instruct"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
