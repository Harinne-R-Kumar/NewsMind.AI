import os
from typing import List
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Security
    JWT_SECRET: str = "default_local_dev_secret_key_please_change_for_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # Databases
    DATABASE_URL: str = "sqlite+aiosqlite:///./newsmind.db"
    CHROMA_DB_PATH: str = "./chromadb_data"

    # AI & LLM Settings
    OLLAMA_URL: str = "http://localhost:11434"
    DEFAULT_LLM_MODEL: str = "qwen2.5:7b"
    EMBEDDING_MODEL: str = "all-minilm:latest"

    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "dummy@gmail.com"
    SMTP_PASSWORD: str = "dummypassword"
    EMAIL_FROM: str = "newsmind-ai@dummy.com"

    # Services
    OPENWEATHER_API_KEY: str = ""
    NEWS_API_KEY: str = ""

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [x.strip() for x in v.split(",")]
        return v


# Instantiate the configuration
settings = Settings()
