from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Knowledge API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Environment Logic
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # This will be crucial for Phase 2 (LLMs)
    # Marking it as optional for now so the app starts without it
    OPENAI_API_KEY: str | None = None

    # Tell Pydantic to read from a .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


# Instantiate as a singleton to be used across the app
settings = Settings()
