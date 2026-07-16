import json
from pathlib import Path

from app.services.material_spectrum_evidence_service import MaterialSpectrumEvidenceService


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_builds_high_confidence_material_spectrum_support_from_named_figure(tmp_path: Path) -> None:
    inventory = tmp_path / "accepted"
    _write(inventory / "_all_books_summary.json", {"run_id": "demo", "book_count": 1, "books": [{"book": "教材甲"}]})
    _write(inventory / "教材甲" / "material_spectra.json", {
        "run_id": "demo",
        "source": {"source_id": "SRC_A"},
        "material_candidates": [{
            "material_candidate_id": "MAT_WATER",
            "canonical_name_candidate": "water",
            "spectrum_ids": ["SPEC_1"],
            "evidence_ids": ["EV_1"],
        }],
        "spectrum_candidates": [{
            "spectrum_candidate_id": "SPEC_1",
            "material_candidate_ids": ["MAT_WATER"],
            "evidence_ids": ["EV_1"],
            "image_candidate_ids": ["IMG_1"],
            "caption_or_context": "Figure 1.3 spectrum of water vapor",
            "source_page": 30,
            "content_list_index": 157,
        }],
        "evidence_spans": [{
            "evidence_id": "EV_1",
            "evidence_type": "chart",
            "locator": {"pdf_page": 30, "content_list_index": 157, "bbox": [1, 2, 3, 4]},
            "text_original": "Figure 1.3. Vibration-rotation spectrum of water vapor.",
        }],
        "image_candidates": [{
            "image_candidate_id": "IMG_1",
            "source_image_path": "images/demo.jpg",
        }],
    })

    items = MaterialSpectrumEvidenceService.build_from_inventory(inventory)
    assert len(items) == 1
    item = items[0]
    assert item["material_name"] == "water"
    assert item["spectrum_id"] == "SPEC_1"
    assert item["support_strength"] == "high"
    assert item["book"] == "教材甲"
    assert item["page"] == 30
    assert "images/demo.jpg" in item["image_paths"]
    assert "evidence_or_caption_names_material" in item["derivation_rules"]


def test_excludes_page_chrome_and_unlinked_noise(tmp_path: Path) -> None:
    inventory = tmp_path / "accepted"
    _write(inventory / "_all_books_summary.json", {"run_id": "demo", "book_count": 1, "books": [{"book": "教材甲"}]})
    _write(inventory / "教材甲" / "material_spectra.json", {
        "source": {"source_id": "SRC_A"},
        "material_candidates": [{"material_candidate_id": "MAT_A", "canonical_name_candidate": "acetone", "spectrum_ids": ["SPEC_1"], "evidence_ids": ["EV_PAGE"]}],
        "spectrum_candidates": [{
            "spectrum_candidate_id": "SPEC_1",
            "material_candidate_ids": ["MAT_A"],
            "evidence_ids": ["EV_PAGE"],
            "caption_or_context": "random instrumental discussion",
        }],
        "evidence_spans": [{
            "evidence_id": "EV_PAGE",
            "evidence_type": "page_number",
            "text_original": "30",
        }],
        "image_candidates": [],
    })
    assert MaterialSpectrumEvidenceService.build_from_inventory(inventory) == []
