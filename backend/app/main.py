from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.analysis import router as analysis_router
from app.api.routes.catalog import build_router
from app.api.routes.graph import compound_router, graph_router, router as groups_router
from app.api.routes.terms import router as terms_router
from app.api.routes.user import router as user_router
from app.api.routes.nist import router as nist_router
from app.core.config import get_settings
from app.core.security import CurrentUser, require_permission
from app.services.catalog_service import CatalogService

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(groups_router, prefix=settings.api_prefix)
app.include_router(graph_router, prefix=settings.api_prefix)
app.include_router(compound_router, prefix=settings.api_prefix)
app.include_router(analysis_router, prefix=settings.api_prefix)
app.include_router(terms_router, prefix=settings.api_prefix)
app.include_router(user_router, prefix=settings.api_prefix)
app.include_router(nist_router, prefix=settings.api_prefix)
app.include_router(build_router(CatalogService(settings.release_path, settings.catalog_database_path, settings.legacy_reference_path, settings.terminology_catalog_path, settings.textbook_inventory_path, settings.mineru_outputs_path, settings.material_spectrum_evidence_path, settings.material_spectrum_claims_path)), prefix=settings.api_prefix)

spectra_dir = settings.release_path / "assets" / "spectra"
legacy_spectra_dir = settings.legacy_reference_path / "assets" / "spectra"
if spectra_dir.exists():
    app.mount("/assets/spectra", StaticFiles(directory=spectra_dir), name="spectra")
if legacy_spectra_dir.exists():
    app.mount("/assets/legacy-spectra", StaticFiles(directory=legacy_spectra_dir), name="legacy-spectra")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "release_path": str(settings.release_path)}


@app.get("/api/manifest")
def manifest(_user: CurrentUser = Depends(require_permission("project:read"))) -> dict:
    from app.services.graph_service import GraphService

    return GraphService().manifest
