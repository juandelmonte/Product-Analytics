"""Application settings loaded from environment variables / a local .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://saas:saas@localhost:5432/saas"
    seed: int = 42


settings = Settings()
