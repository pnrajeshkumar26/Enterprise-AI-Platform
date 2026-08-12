from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise Runtime API"
    app_version: str = "1.0.0"
    app_env: str = "development"

    # Hugging Face Text Generation Inference Server
    tgi_url: str = "http://host.docker.internal:8080"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()