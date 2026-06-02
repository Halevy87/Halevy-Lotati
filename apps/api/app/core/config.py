from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Local-dev default matches docker-compose.yml. Override via env in CI / other envs.
    database_url: str = "postgresql+psycopg2://halevy:halevy@localhost:5544/halevy"

    # Permissive for local dev; tighten when the frontend origin is fixed.
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
