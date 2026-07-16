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
    legacy_reference_path: Path = Path(__file__).resolve().parents[3] / "raw_data" / "basic_groups_v07_20260619"
    docs_summary_path: Path = Path(__file__).resolve().parents[3] / "raw_data" / "docs" / "ir_ie_v07_core_data_model_v20260622.summary.json"
    terminology_catalog_path: Path = Path(__file__).resolve().parents[3].parent.parent / "0714谱构效数据" / "terminology" / "_terminology_catalog.json"
    textbook_inventory_path: Path = Path(__file__).resolve().parents[3].parent.parent / "0714谱构效数据" / "material_spectra_accepted"
    mineru_outputs_path: Path = Path(__file__).resolve().parents[3].parent.parent / "20260616 谱学教科书知识抽取加强版" / "outputs"
    nist_index_path: Path = Path("/share/lawbda/spectra_nist/nist_multimodal.sqlite")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
