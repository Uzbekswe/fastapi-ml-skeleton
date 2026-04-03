from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.0.1"
APP_NAME = "House Price Prediction Example"
API_PREFIX = "/api"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    API_KEY: SecretStr
    IS_DEBUG: bool = False
    DEFAULT_MODEL_PATH: str

    @field_validator("DEFAULT_MODEL_PATH")
    @classmethod
    def validate_model_path(cls, v: str) -> str:
        if not Path(v).exists():
            raise ValueError(f"Model file not found: {v}")
        return v


settings = Settings()
