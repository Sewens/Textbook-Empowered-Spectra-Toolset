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


def test_catalog_routes_expose_multisource_terminology_catalog(tmp_path):
    import json

    from app.services.terminology_service import TerminologyCatalogService

    catalog_path = tmp_path / "_terminology_catalog.json"
    catalog_path.write_text(json.dumps({
        "source_count": 2,
        "terms": [{
            "term_id": "TERM_wavenumber",
            "concept_type": "radiation_quantity",
            "preferred_name": {"zh": "波数", "en": "wavenumber"},
            "all_source_forms": ["波数", "wavenumber"],
            "source_book_count": 2,
            "source_records": [{"book": "教材甲", "source_id": "SRC_A", "evidence_ids": ["EV_A"]}, {"book": "教材乙", "source_id": "SRC_B", "evidence_ids": ["EV_B"]}],
            "all_evidence_ids": ["EV_A", "EV_B"],
            "status": "candidate_needs_review"
        }],
        "source_specific_claims": [{"claim_id": "CL_A", "subject_ref": "TERM_wavenumber", "source_id": "SRC_A", "book": "教材甲", "evidence_ids": ["EV_A"]}],
        "evidence_spans": [{"evidence_id": "EV_A", "book": "教材甲", "text_original": "波数是..."}, {"evidence_id": "EV_B", "book": "教材乙", "text_original": "Wavenumber is..."}]
    }, ensure_ascii=False), encoding="utf-8")
    terminology = TerminologyCatalogService(catalog_path)
    assert terminology.overview_counts() == {"terminology_terms": 1, "terminology_sources": 2, "terminology_claims": 1, "terminology_evidence": 2}
    item = terminology.get_term("TERM_wavenumber")
    assert len(item["source_records"]) == 2
    assert item["source_specific_claims"][0]["book"] == "教材甲"
