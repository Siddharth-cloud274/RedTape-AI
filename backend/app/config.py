from typing import List
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    HOST: str = os.getenv("HOST")
    PORT: int = os.getenv("PORT")
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://[::1]:5173"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL")

    # Checks both the current directory and backend/ directory for .env
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
