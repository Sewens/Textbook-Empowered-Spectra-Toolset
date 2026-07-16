import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.catalog import build_router
from app.services.catalog_service import CatalogService


def test_catalog_routes_expose_release_overview_and_entity_collections(tmp_path):
    release = tmp_path / "release"
    release.mkdir()
    (release / "DATA_INVENTORY.json").write_text(json.dumps({"release_id": "api-demo", "schema_release": "ir-kg-v2.0.2"}), encoding="utf-8")
    catalog = CatalogService(release, tmp_path / "catalog.sqlite")
    app = FastAPI()
    app.include_router(build_router(catalog), prefix="/api")
    client = TestClient(app)
    overview = client.get("/api/catalog/overview")
    assert overview.status_code == 200
    assert overview.json()["release_id"] == "api-demo"
    assert client.get("/api/catalog/concepts").json() == {"total": 0, "items": []}
    assert client.get("/api/catalog/graph").json() == {"nodes": [], "edges": []}


def test_catalog_routes_expose_terms_groups_material_details_and_hierarchy(tmp_path):
    release = tmp_path / "release"
    release.mkdir()
    (release / "DATA_INVENTORY.json").write_text(json.dumps({"release_id": "api-demo"}), encoding="utf-8")
    legacy = tmp_path / "legacy"
    (legacy / "FG_DEMO.json").parent.mkdir()
    (legacy / "FG_DEMO.json").write_text(json.dumps({"group_id": "FG_DEMO", "name_zh": "示例基团", "spectral_gallery": [{"figure_id": "SPEC_DEMO", "compound_id": "CMPD_DEMO", "compound_name_zh": "示例物质", "annotated_peaks": []}]}), encoding="utf-8")
    catalog = CatalogService(release, tmp_path / "catalog.sqlite", legacy)
    app = FastAPI()
    app.include_router(build_router(catalog), prefix="/api")
    client = TestClient(app)
    assert client.get("/api/catalog/terms").json()["items"][0]["term_id"] == "FG_DEMO"
    assert client.get("/api/catalog/groups/FG_DEMO").json()["materials"][0]["entity_id"] == "CMPD_DEMO"
    assert client.get("/api/catalog/materials/CMPD_DEMO").json()["groups"][0]["group_id"] == "FG_DEMO"
    hierarchy = client.get("/api/catalog/hierarchy").json()
    assert hierarchy["edges"][0]["label"] == "has_reference_material"
