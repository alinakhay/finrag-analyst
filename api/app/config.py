from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CatalystLens API"
    app_version: str = "0.3.0"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    top_k: int = 2
    model_provider: str = "extractive"
    base_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    adapter_path: str = "artifacts/catalyst-lora"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CATALYSTLENS_",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
