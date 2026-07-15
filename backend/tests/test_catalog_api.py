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
