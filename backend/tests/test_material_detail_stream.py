import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.catalog import build_router
from app.services.catalog_service import CatalogService
from app.services.textbook_inventory_service import TextbookInventoryService


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _inventory(tmp_path: Path) -> Path:
    inventory = tmp_path / "accepted"
    _write(inventory / "_all_books_summary.json", {"run_id": "run", "book_count": 1, "books": [{"book": "教材甲"}]})
    spectra = []
    evidence = []
    images = []
    spectrum_ids = []
    for i in range(30):
        sid = f"SPEC_{i}"
        eid = f"EV_{i}"
        iid = f"IMG_{i}"
        spectrum_ids.append(sid)
        spectra.append({
            "spectrum_candidate_id": sid,
            "material_candidate_ids": ["MAT_A"],
            "evidence_ids": [eid],
            "image_candidate_ids": [iid] if i < 5 else [],
            "caption_or_context": f"Figure {i} of methanol",
            "source_page": 10 + i,
            "content_list_index": i,
            "feature_candidate_ids": [],
        })
        evidence.append({
            "evidence_id": eid,
            "evidence_type": "chart" if i < 5 else "paragraph",
            "locator": {"pdf_page": 10 + i, "content_list_index": i},
            "text_original": f"Figure {i} spectrum of methanol",
        })
        images.append({
            "image_candidate_id": iid,
            "source_image_path": f"images/{i}.jpg" if i < 5 else None,
        })
    material_record = {
        "material_candidate_id": "MAT_A",
        "canonical_name_candidate": "methanol",
        "spectrum_ids": spectrum_ids,
        "evidence_ids": [e["evidence_id"] for e in evidence],
        "group_candidate_ids": ["FG_HYDROXYL"],
    }
    group_record = {"group_candidate_id": "FG_HYDROXYL", "preferred_name": {"zh": "羟基"}}
    _write(inventory / "教材甲" / "material_spectra.json", {
        "source": {"source_id": "SRC_A"},
        "material_candidates": [material_record],
        "group_candidates": [group_record],
        "spectrum_candidates": spectra,
        "feature_candidates": [],
        "evidence_spans": evidence,
        "image_candidates": images,
    })
    # Aggregate catalogs used by TextbookInventoryService.list/get.
    _write(inventory / "_compound_catalog.json", {
        "materials": [{"material_candidate_id": "MAT_A", "source_records": [{"book": "教材甲", "source_id": "SRC_A", "record": material_record}]}]
    })
    _write(inventory / "_group_catalog.json", {
        "groups": [{"group_candidate_id": "FG_HYDROXYL", "source_records": [{"book": "教材甲", "source_id": "SRC_A", "record": group_record}]}]
    })
    _write(inventory / "_spectrum_catalog.json", {
        "spectra": [{"spectrum_candidate_id": s["spectrum_candidate_id"], "source_records": [{"book": "教材甲", "source_id": "SRC_A", "record": s}]} for s in spectra]
    })
    return inventory


def test_unified_detail_streams_spectra_with_offset_limit(tmp_path: Path) -> None:
    inventory = _inventory(tmp_path)
    service = TextbookInventoryService(inventory)
    page0 = service.unified_detail("materials", "MAT_A", offset=0, limit=12, threshold=12)
    assert page0 is not None
    assert page0["counts"]["spectra_total"] == 30
    assert page0["counts"]["stream"] is True
    assert page0["page"]["returned"] == 12
    assert page0["page"]["has_more"] is True
    assert page0["page"]["next_offset"] == 12
    assert len(page0["items"]) == 12
    # image-bearing spectra should be ranked first
    assert all(item["spectrum"]["images"] for item in page0["items"][:5])

    page1 = service.unified_detail("materials", "MAT_A", offset=12, limit=12, threshold=12)
    assert page1 is not None
    assert page1["page"]["returned"] == 12
    assert page1["page"]["has_more"] is True
    assert page0["items"][0]["spectrum"]["id"] != page1["items"][0]["spectrum"]["id"]


def test_catalog_route_exposes_stream_pagination(tmp_path: Path) -> None:
    inventory = _inventory(tmp_path)
    release = tmp_path / "release"
    release.mkdir()
    (release / "DATA_INVENTORY.json").write_text(json.dumps({"release_id": "demo"}), encoding="utf-8")
    catalog = CatalogService(release, tmp_path / "catalog.sqlite", textbook_inventory_path=inventory)
    app = FastAPI()
    app.include_router(build_router(catalog), prefix="/api")
    client = TestClient(app)
    first = client.get("/api/catalog/textbook-inventory/details/materials/MAT_A?offset=0&limit=10&threshold=10").json()
    assert first["counts"]["spectra_total"] == 30
    assert first["page"]["has_more"] is True
    assert len(first["items"]) == 10
    second = client.get("/api/catalog/textbook-inventory/details/materials/MAT_A?offset=10&limit=10&threshold=10").json()
    assert len(second["items"]) == 10
    assert first["items"][0]["spectrum"]["id"] != second["items"][0]["spectrum"]["id"]
