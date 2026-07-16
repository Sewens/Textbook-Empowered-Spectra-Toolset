#!/usr/bin/env python3
"""Package the precision-screened textbook materials into a Git-trackable release."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO.parents[1] / "0714谱构效数据"
SOURCE_ACCEPTED = WORKSPACE / "material_spectra_accepted"
SOURCE_QUARANTINE = WORKSPACE / "material_spectra_quarantine"
RELEASE = REPO / "data" / "releases" / "textbook-materials-v1.0.0"


def dump_compact(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if not (SOURCE_ACCEPTED / "_all_books_summary.json").exists():
        raise SystemExit(f"Missing accepted source: {SOURCE_ACCEPTED}")
    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    accepted = RELEASE / "accepted"
    quarantine = RELEASE / "quarantine"
    for source in sorted(SOURCE_ACCEPTED.rglob("*.json")):
        destination = accepted / source.relative_to(SOURCE_ACCEPTED)
        dump_compact(destination, json.loads(source.read_text(encoding="utf-8")))
    for source in sorted(SOURCE_QUARANTINE.rglob("*.json")):
        destination = quarantine / source.relative_to(SOURCE_QUARANTINE)
        dump_compact(destination, json.loads(source.read_text(encoding="utf-8")))

    summary = json.loads((accepted / "_all_books_summary.json").read_text(encoding="utf-8"))
    manifest = {
        "release_version": "v1.0.0",
        "release_name": "textbook-materials-v1.0.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "schema_version": "textbook_material_inventory_v1",
        "run_id": summary["run_id"],
        "partition": "accepted_precision_candidate",
        "quality_gate": {
            "direct_name_evidence_required": True,
            "direct_figure_or_table_evidence_required": True,
            "rejects": ["sample_state", "instrument_or_method", "chapter_or_sentence_fragment", "OCR_formula_sequence", "generic_chemical_class"],
            "review_status": "precision_screened_needs_review",
        },
        "counts": {
            "books": summary["book_count"],
            "unique_materials": summary["unique_catalogs"]["materials"],
            "unique_groups": summary["unique_catalogs"]["groups"],
            "unique_spectra": summary["unique_catalogs"]["spectra"],
            "material_source_records": summary["totals"]["materials"],
            "spectrum_source_records": summary["totals"]["spectra"],
            "evidence_records": summary["totals"]["evidence"],
            "quarantined_material_candidates": summary["totals"]["quarantined_material_candidates"],
        },
        "source_provenance": {
            "corpus": "31 MinerU-parsed infrared spectroscopy textbooks",
            "per_record": ["book", "source_id", "pdf_page", "content_list_index", "bbox", "text_original", "content_hash"],
            "image_assets": "Relative source_image_path values resolve against the configured MinerU textbook output root; source images are not duplicated in this release.",
        },
        "layout": {
            "accepted": "API-compatible inventory root with per-book material_spectra.json plus aggregate catalogs",
            "quarantine": "rejected_material_candidates.json with reason and source links",
        },
    }
    dump_compact(RELEASE / "manifest.json", manifest)
    (RELEASE / "README.md").write_text("""# Textbook Materials v1.0.0

This is the versioned precision-screened textbook material release used by the `materials` API.

## Scope

- 31 MinerU-parsed infrared spectroscopy textbooks
- `accepted/`: only candidates with direct naming evidence in a figure or table context
- `quarantine/`: excluded candidates with machine-readable rejection reasons
- Every accepted source record retains textbook title, page/locator, bounding box, original evidence text, and relative image path.

## Layout

- `accepted/_compound_catalog.json`: deduplicated material browse catalog
- `accepted/_group_catalog.json`: deduplicated related-group catalog
- `accepted/_spectrum_catalog.json`: deduplicated spectrum catalog
- `accepted/<book>/material_spectra.json`: book-native records and evidence
- `quarantine/rejected_material_candidates.json`: audit partition
- `manifest.json`: release contract and counts
- `SHA256SUMS.txt`: integrity checksums

## Reproduce

Run `python scripts/build_accepted_material_catalog.py`, then
`python scripts/package_textbook_material_release.py` from the repository root.

Source textbook images remain in the configured MinerU output root and are referenced by validated relative paths; this release does not redistribute the original textbook assets.
""", encoding="utf-8")
    files = sorted(path for path in RELEASE.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    lines = [f"{sha256(path)}  {path.relative_to(RELEASE).as_posix()}" for path in files]
    (RELEASE / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"release": str(RELEASE), "files": len(files) + 1, "bytes": sum(p.stat().st_size for p in files) + (RELEASE / "SHA256SUMS.txt").stat().st_size, "manifest": manifest}, ensure_ascii=False))

if __name__ == "__main__":
    main()
