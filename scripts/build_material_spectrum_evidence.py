#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
from app.services.material_spectrum_evidence_service import MaterialSpectrumEvidenceService
INVENTORY = REPO / "data" / "releases" / "textbook-materials-v1.0.0" / "accepted"
if not (INVENTORY / "_all_books_summary.json").exists():
    INVENTORY = REPO.parents[1] / "0714谱构效数据" / "material_spectra_accepted"
OUT = REPO / "data" / "releases" / "material-spectrum-evidence-v1.0.0"

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
    items = MaterialSpectrumEvidenceService.build_from_inventory(INVENTORY)
    strength = {"high": 0, "medium": 0, "low": 0}
    books = sorted({item.get("book") for item in items if item.get("book")})
    for item in items:
        strength[item.get("support_strength", "low")] = strength.get(item.get("support_strength", "low"), 0) + 1
    OUT.mkdir(parents=True, exist_ok=True)
    dump_compact(OUT / "evidence_links.json", {
        "release_version": "v1.0.0",
        "run_id": "RUN_material-spectrum-evidence-20260716-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_inventory": str(INVENTORY),
        "total": len(items),
        "items": items,
    })
    dump_compact(OUT / "manifest.json", {
        "release_version": "v1.0.0",
        "release_name": "material-spectrum-evidence-v1.0.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "schema_version": "material_spectrum_support_evidence_v1",
        "source_inventory_run_id": "RUN_precision-materials-20260716-v2",
        "counts": {
            "evidence_links": len(items),
            "books": len(books),
            "materials": len({item.get("material_id") for item in items}),
            "spectra": len({item.get("spectrum_id") for item in items}),
            "high": strength.get("high", 0),
            "medium": strength.get("medium", 0),
        },
        "policy": {
            "support_role": "material_spectrum_support",
            "requires_material_and_spectrum_link": True,
            "high": "material name appears in figure/table/image evidence",
            "medium": "material name appears in linked paragraph/caption, or figure linked via spectrum without literal name",
            "excluded": "page chrome, equations-only noise, unlinked text",
        },
    })
    readme_lines = [
        "# Material-Spectrum Support Evidence v1.0.0",
        "",
        "This release projects textbook evidence that supports material-to-spectrum correspondence.",
        "",
        "Files: evidence_links.json, manifest.json, SHA256SUMS.txt",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")
    files = sorted(path for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    checksum_lines = [f"{sha256(path)}  {path.relative_to(OUT).as_posix()}" for path in files]
    (OUT / "SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT), "total": len(items), "strength": strength, "books": len(books)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
