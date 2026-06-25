"""Application settings, loaded from environment / .env.

Env var names match what FoundryChatClient reads natively
(FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL), so the client can also pick them
up on its own — we surface them here for explicit wiring and validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Foundry project endpoint, e.g. https://<project>.services.ai.azure.com
    foundry_project_endpoint: str = ""
    # Model deployment name, e.g. gpt-4.1-mini
    foundry_model: str = "gpt-4.1-mini"

    # CORS origin for the local Next.js frontend
    frontend_origin: str = "http://localhost:3000"


settings = Settings()
