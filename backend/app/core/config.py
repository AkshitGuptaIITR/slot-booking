from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore",
    )


settings = Settings()
