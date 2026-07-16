from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TextbookInventoryService:
    """Lazy reader for the broad, source-preserving textbook staging catalogs."""

    def __init__(self, inventory_path: Path | None = None) -> None:
        self.inventory_path = Path(inventory_path) if inventory_path else None
        self._catalogs: dict[str, dict[str, Any]] = {}
        self._books: dict[str, dict[str, Any]] = {}

    @property
    def available(self) -> bool:
        return bool(self.inventory_path and (self.inventory_path / "_all_books_summary.json").exists())

    def overview(self) -> dict[str, Any]:
        if not self.available:
            return {"available": False, "run_id": None, "book_count": 0, "totals": {}, "unique_catalogs": {}}
        summary = self._read_json(self.inventory_path / "_all_books_summary.json", {})
        return {
            "available": True,
            "run_id": summary.get("run_id"),
            "book_count": summary.get("book_count", 0),
            "totals": summary.get("totals", {}),
            "unique_catalogs": summary.get("unique_catalogs", {}),
            "policy": summary.get("policy", {}),
        }

    def counts(self) -> dict[str, int]:
        overview = self.overview()
        totals = overview.get("totals", {})
        unique = overview.get("unique_catalogs", {})
        return {
            "textbook_inventory_groups": int(unique.get("groups", 0)),
            "textbook_inventory_materials": int(unique.get("materials", 0)),
            "textbook_inventory_spectra": int(unique.get("spectra", 0)),
            "textbook_inventory_features": int(totals.get("features", 0)),
            "textbook_inventory_images": int(totals.get("images", 0)),
            "textbook_inventory_evidence": int(totals.get("evidence", 0)),
        }

    def list_groups(self, query: str | None = None, book: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self._list("groups", query, book, limit)

    def list_materials(self, query: str | None = None, book: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self._list("materials", query, book, limit)

    def list_spectra(self, query: str | None = None, book: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self._list("spectra", query, book, limit)

    def get_group(self, candidate_id: str) -> dict[str, Any] | None:
        return self._get("groups", "group_candidate_id", candidate_id)

    def get_material(self, candidate_id: str) -> dict[str, Any] | None:
        return self._get("materials", "material_candidate_id", candidate_id)

    def get_spectrum(self, candidate_id: str) -> dict[str, Any] | None:
        return self._get("spectra", "spectrum_candidate_id", candidate_id)

    def books(self) -> list[str]:
        if not self.available:
            return []
        summary = self._read_json(self.inventory_path / "_all_books_summary.json", {})
        return [item.get("book", "") for item in summary.get("books", []) if item.get("book")]

    def material_detail(self, candidate_id: str) -> dict[str, Any] | None:
        return self._detail("materials", "material_candidate_id", candidate_id)

    def spectrum_detail(self, candidate_id: str) -> dict[str, Any] | None:
        return self._detail("spectra", "spectrum_candidate_id", candidate_id)

    def group_detail(self, candidate_id: str) -> dict[str, Any] | None:
        return self._detail("groups", "group_candidate_id", candidate_id)

    def _list(self, kind: str, query: str | None, book: str | None, limit: int) -> list[dict[str, Any]]:
        rows = []
        token = query.casefold() if query else None
        for item in self._load(kind).get(self._array_key(kind), []):
            source_records = item.get("source_records", [])
            if book and not any(record.get("book") == book for record in source_records):
                continue
            if token and token not in self._search_text(item).casefold():
                continue
            rows.append(self._summary_item(kind, item))
            if len(rows) >= limit:
                break
        return rows

    def _get(self, kind: str, id_key: str, candidate_id: str) -> dict[str, Any] | None:
        return next((item for item in self._load(kind).get(self._array_key(kind), []) if item.get(id_key) == candidate_id), None)

    def _detail(self, kind: str, id_key: str, candidate_id: str) -> dict[str, Any] | None:
        item = self._get(kind, id_key, candidate_id)
        if item is None:
            return None
        source_records = []
        for source in item.get("source_records", []):
            enriched = dict(source)
            book = source.get("book", "")
            record = self._detail_from_book(kind, candidate_id, book) or source.get("record", {})
            enriched["record"] = record
            book_payload = self._source_book(book)
            image_ids = set(record.get("image_candidate_ids", []))
            if image_ids:
                enriched["image_candidates"] = [image for image in book_payload.get("image_candidates", []) if image.get("image_candidate_id") in image_ids]
            evidence_ids = set(record.get("evidence_ids", []))
            if evidence_ids:
                enriched["evidence_spans"] = [evidence for evidence in book_payload.get("evidence_spans", []) if evidence.get("evidence_id") in evidence_ids]
            source_records.append(enriched)
        return self._summary_item(kind, item) | {"source_records": source_records}

    def asset_path(self, book: str, asset_path: str) -> Path | None:
        if not self.available or book not in self.books():
            return None
        base = (self.inventory_path / book / "unzipped").resolve()
        candidate = (base / asset_path).resolve()
        if base not in candidate.parents or not candidate.is_file():
            return None
        return candidate

    def _load(self, kind: str) -> dict[str, Any]:
        if kind not in self._catalogs:
            filename = {"groups": "_group_catalog.json", "materials": "_compound_catalog.json", "spectra": "_spectrum_catalog.json"}[kind]
            self._catalogs[kind] = self._read_json(self.inventory_path / filename, {}) if self.available else {}
        return self._catalogs[kind]

    @staticmethod
    def _array_key(kind: str) -> str:
        return {"groups": "groups", "materials": "materials", "spectra": "spectra"}[kind]

    @staticmethod
    def _search_text(item: dict[str, Any]) -> str:
        parts = [item.get("group_candidate_id", ""), item.get("material_candidate_id", ""), item.get("spectrum_candidate_id", "")]
        for source in item.get("source_records", []):
            parts.append(source.get("book", ""))
            record = source.get("record", {})
            parts.extend([record.get("canonical_name_candidate", ""), record.get("caption_or_context", "")])
            parts.extend(record.get("source_forms", []))
        return " ".join(str(part) for part in parts if part)

    def _summary_item(self, kind: str, item: dict[str, Any]) -> dict[str, Any]:
        sources = item.get("source_records", [])
        books = sorted({source.get("book") for source in sources if source.get("book")})
        records = [source.get("record", {}) for source in sources]
        if kind == "groups":
            name = next((record.get("preferred_name", {}).get("zh") or record.get("preferred_name", {}).get("en") for record in records), item.get("group_candidate_id"))
            item_id = item.get("group_candidate_id")
            return {"candidate_id": item_id, "candidate_type": "group", "name": name, "book_count": len(books), "source_count": len(sources), "mention_count": sum(record.get("mention_count", 0) for record in records), "spectrum_count": len({sid for record in records for sid in record.get("spectrum_ids", [])}), "review_status": "candidate_needs_review", "books": books}
        if kind == "materials":
            name = next((record.get("canonical_name_candidate") for record in records if record.get("canonical_name_candidate")), item.get("material_candidate_id"))
            item_id = item.get("material_candidate_id")
            return {"candidate_id": item_id, "candidate_type": "material", "name": name, "book_count": len(books), "source_count": len(sources), "mention_count": sum(record.get("mention_count", 0) for record in records), "spectrum_count": len({sid for record in records for sid in record.get("spectrum_ids", [])}), "group_count": len({gid for record in records for gid in record.get("group_candidate_ids", [])}), "evidence_count": len({eid for record in records for eid in record.get("evidence_ids", [])}), "review_status": "candidate_needs_review", "books": books}
        item_id = item.get("spectrum_candidate_id")
        return {"candidate_id": item_id, "candidate_type": "spectrum", "name": next((record.get("caption_or_context", "")[:160] for record in records if record.get("caption_or_context")), item_id), "book_count": len(books), "source_count": len(sources), "material_count": len({mid for record in records for mid in record.get("material_candidate_ids", [])}), "group_count": len({gid for record in records for gid in record.get("group_candidate_ids", [])}), "feature_count": len({fid for record in records for fid in record.get("feature_candidate_ids", [])}), "image_count": len({iid for record in records for iid in record.get("image_candidate_ids", [])}), "review_status": "candidate_needs_review", "books": books}

    def _source_book(self, book: str) -> dict[str, Any]:
        if book not in self._books:
            path = self.inventory_path / book / "material_spectra.json"
            self._books[book] = self._read_json(path, {})
        return self._books[book]

    def _detail_from_book(self, kind: str, candidate_id: str, book: str) -> dict[str, Any] | None:
        payload = self._source_book(book)
        key = {"groups": "group_candidate_id", "materials": "material_candidate_id", "spectra": "spectrum_candidate_id"}[kind]
        array_key = self._array_key(kind)
        return next((item for item in payload.get(array_key, []) if item.get(key) == candidate_id), None)

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path or not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
