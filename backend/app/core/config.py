from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def default_release_path() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    upgraded = repo_root.parent.parent / "20260714 谱构效数据建设" / "releases" / "IR-Spectroscopy-KG-Data-v0.1.1-alpha.20260715"
    return upgraded if upgraded.exists() else repo_root / "raw_data" / "IR-Spectroscopy-KG-Data-v0.1.1-alpha.20260715"


class Settings(BaseSettings):
    app_name: str = "Spectrum-Structure-Effect Knowledge API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./spectroscopy.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    release_path: Path = default_release_path()
    catalog_database_path: Path = Path(__file__).resolve().parents[2] / ".runtime" / "spectrum_structure_effect_catalog.sqlite"
    docs_summary_path: Path = Path(__file__).resolve().parents[3] / "raw_data" / "docs" / "ir_ie_v07_core_data_model_v20260622.summary.json"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
