from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Spectroscopy Knowledge API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./spectroscopy.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    release_path: Path = Path(__file__).resolve().parents[3] / "raw_data" / "basic_groups_v07_20260619"
    docs_summary_path: Path = Path(__file__).resolve().parents[3] / "raw_data" / "docs" / "ir_ie_v07_core_data_model_v20260622.summary.json"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
