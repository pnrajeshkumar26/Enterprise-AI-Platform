from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "Enterprise Runtime API"
    app_version: str = "1.0.0"
    app_env: str = "development"

    # Self-hosted GPU compute cost baseline
    compute_instance_type: str = "g4dn.xlarge"
    compute_hourly_cost_usd: float = 0.579

    # Kubernetes Service name for vLLM
    vllm_url: str = "http://enterprise-vllm:8000"

    # Must match the model ID exposed by vLLM
    vllm_model_id: str = "microsoft/Phi-3-mini-4k-instruct"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
