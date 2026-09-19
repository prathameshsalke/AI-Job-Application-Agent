import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./job_agent.db"
    secret_key: str = "change-this-in-development"
    access_token_expire_minutes: int = 1440
    frontend_url: str = "http://localhost:5500"
    upload_dir: str = "uploads"
    max_upload_mb: int = 10
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
