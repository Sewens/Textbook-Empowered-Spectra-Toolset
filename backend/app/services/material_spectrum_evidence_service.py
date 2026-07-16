from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


FIGURE_TYPES = {"chart", "image", "table", "figure", "figure_caption"}
NOISE_TYPES = {"page_number", "page_header", "page_footer", "page_aside_text", "page_footnote", "code", "algorithm"}


class MaterialSpectrumEvidenceService:
    """Project material-spectrum support evidence from precision-accepted textbook inventory."""

    def __init__(self, inventory_path: Path | None = None, release_path: Path | None = None) -> None:
        self.inventory_path = Path(inventory_path) if inventory_path else None
        self.release_path = Path(release_path) if release_path else None
        self._cache: tuple[tuple[int, int] | None, list[dict[str, Any]]] | None = None

    @property
    def available(self) -> bool:
        if self.release_path and (self.release_path / "evidence_links.json").exists():
            return True
        return bool(self.inventory_path and (self.inventory_path / "_all_books_summary.json").exists())

    def overview(self) -> dict[str, Any]:
        items = self.all_links()
        strength = {"high": 0, "medium": 0, "low": 0}
        books = set()
        materials = set()
        spectra = set()
        for item in items:
            strength[item.get("support_strength", "low")] = strength.get(item.get("support_strength", "low"), 0) + 1
            books.add(item.get("book"))
            materials.add(item.get("material_id"))
            spectra.add(item.get("spectrum_id"))
        return {
            "available": self.available,
            "total": len(items),
            "books": len([b for b in books if b]),
            "materials": len([m for m in materials if m]),
            "spectra": len([s for s in spectra if s]),
            "by_strength": strength,
            "policy": {
                "mode": "material_spectrum_support_evidence",
                "requires_material_and_spectrum_link": True,
                "prefers_named_figure_or_table_evidence": True,
            },
        }

    def list_links(self, query: str | None = None, strength: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        token = query.casefold() if query else None
        rows: list[dict[str, Any]] = []
        for item in self.all_links():
            if strength and item.get("support_strength") != strength:
                continue
            if token and token not in self._search_blob(item):
                continue
            rows.append(item)
            if len(rows) >= limit:
                break
        return rows

    def all_links(self) -> list[dict[str, Any]]:
        if not self.available:
            return []
        if self.release_path and (self.release_path / "evidence_links.json").exists():
            source_key = self._file_key(self.release_path / "evidence_links.json")
            if self._cache and self._cache[0] == source_key:
                return self._cache[1]
            items = json.loads((self.release_path / "evidence_links.json").read_text(encoding="utf-8")).get("items", [])
            self._cache = (source_key, items)
            return items
        assert self.inventory_path is not None
        source_key = self._file_key(self.inventory_path / "_all_books_summary.json")
        if self._cache and self._cache[0] == source_key:
            return self._cache[1]
        items = self.build_from_inventory(self.inventory_path)
        self._cache = (source_key, items)
        return items

    @classmethod
    def build_from_inventory(cls, inventory_path: Path) -> list[dict[str, Any]]:
        summary = cls._read_json(inventory_path / "_all_books_summary.json", {})
        records: list[dict[str, Any]] = []
        for book_meta in summary.get("books", []):
            book = book_meta.get("book")
            if not book:
                continue
            payload = cls._read_json(inventory_path / book / "material_spectra.json", {})
            materials = {item.get("material_candidate_id"): item for item in payload.get("material_candidates", [])}
            evidence = {item.get("evidence_id"): item for item in payload.get("evidence_spans", [])}
            images = {item.get("image_candidate_id"): item for item in payload.get("image_candidates", [])}
            source_id = (payload.get("source") or {}).get("source_id")
            for spectrum in payload.get("spectrum_candidates", []):
                spectrum_id = spectrum.get("spectrum_candidate_id")
                material_ids = [mid for mid in spectrum.get("material_candidate_ids", []) if mid in materials]
                if not spectrum_id or not material_ids:
                    continue
                caption = cls._clean_text(spectrum.get("caption_or_context") or "")
                image_paths = []
                for image_id in spectrum.get("image_candidate_ids", []):
                    image = images.get(image_id) or {}
                    path = image.get("source_image_path")
                    if path:
                        image_paths.append(path)
                evidence_ids = spectrum.get("evidence_ids", []) or []
                # If spectrum has no evidence ids, still create a caption-based support when caption names material.
                candidate_evidence: list[dict[str, Any] | None]
                if evidence_ids:
                    candidate_evidence = [evidence.get(eid) for eid in evidence_ids]
                else:
                    candidate_evidence = [None]
                for material_id in material_ids:
                    material = materials[material_id]
                    material_name = material.get("canonical_name_candidate") or material_id
                    for ev in candidate_evidence:
                        record = cls._make_record(
                            book=book,
                            source_id=source_id,
                            material_id=material_id,
                            material_name=material_name,
                            spectrum_id=spectrum_id,
                            spectrum=spectrum,
                            caption=caption,
                            image_paths=image_paths,
                            evidence=ev,
                        )
                        if record is not None:
                            records.append(record)
        # Prefer stronger supports first for stable browsing.
        strength_rank = {"high": 0, "medium": 1, "low": 2}
        records.sort(key=lambda item: (strength_rank.get(item.get("support_strength"), 9), item.get("book") or "", item.get("material_name") or "", item.get("evidence_link_id") or ""))
        return records

    @classmethod
    def _make_record(
        cls,
        *,
        book: str,
        source_id: str | None,
        material_id: str,
        material_name: str,
        spectrum_id: str,
        spectrum: dict[str, Any],
        caption: str,
        image_paths: list[str],
        evidence: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        evidence_id = (evidence or {}).get("evidence_id")
        evidence_type = (evidence or {}).get("evidence_type") or ("caption" if caption else "context")
        if evidence_type in NOISE_TYPES:
            return None
        text = cls._clean_text((evidence or {}).get("text_original") or caption or "")
        if not text:
            return None
        locator = (evidence or {}).get("locator") or {}
        page = locator.get("pdf_page") or spectrum.get("source_page")
        content_list_index = locator.get("content_list_index") or spectrum.get("content_list_index")
        bbox = locator.get("bbox")
        names_material = cls._names_material(material_name, text) or cls._names_material(material_name, caption)
        is_figure_like = evidence_type in FIGURE_TYPES or bool(re.search(r"(?i)\bfigure\b|图\s*\d+|表\s*\d+", text))
        rules = ["spectrum_links_material"]
        if names_material:
            rules.append("evidence_or_caption_names_material")
        if is_figure_like:
            rules.append("figure_table_or_image_context")
        if image_paths:
            rules.append("has_spectrum_image")
        # Keep only useful supports for material-spectrum correspondence.
        if names_material and is_figure_like:
            strength = "high"
        elif names_material:
            strength = "medium"
        elif is_figure_like and image_paths:
            # Figure/table linked to material via spectrum graph, but text does not literally name it.
            strength = "medium"
            rules.append("figure_linked_via_spectrum_without_literal_name")
        else:
            return None
        link_seed = f"{book}|{material_id}|{spectrum_id}|{evidence_id or 'CAPTION'}|{strength}"
        evidence_link_id = "EVL_" + hashlib.sha1(link_seed.encode("utf-8")).hexdigest()[:20]
        return {
            "evidence_link_id": evidence_link_id,
            "evidence_id": evidence_id or evidence_link_id,
            "support_role": "material_spectrum_support",
            "support_strength": strength,
            "material_id": material_id,
            "material_name": material_name,
            "spectrum_id": spectrum_id,
            "book": book,
            "source_id": source_id,
            "evidence_type": evidence_type,
            "text": text[:1200],
            "spectrum_caption": caption[:500] if caption else None,
            "page": page,
            "content_list_index": content_list_index,
            "bbox": bbox,
            "image_paths": image_paths[:4],
            "source_scope": "textbook",
            "review_status": "precision_screened_needs_review",
            "derivation_rules": rules,
            "payload": {
                "material_id": material_id,
                "material_name": material_name,
                "spectrum_id": spectrum_id,
                "book": book,
                "support_strength": strength,
                "locator": {"pdf_page": page, "content_list_index": content_list_index, "bbox": bbox},
                "image_paths": image_paths[:4],
                "derivation_rules": rules,
            },
        }

    @staticmethod
    def _names_material(name: str, text: str) -> bool:
        value = (name or "").strip()
        blob = text or ""
        if not value or not blob:
            return False
        if value.casefold() in blob.casefold():
            return True
        # Tolerate simple spaced chemical tokens like "H O H" for water-related figures.
        compact_name = re.sub(r"\s+", "", value).casefold()
        compact_text = re.sub(r"\s+", "", blob).casefold()
        return bool(compact_name) and compact_name in compact_text

    @staticmethod
    def _clean_text(text: str) -> str:
        value = text or ""
        value = value.replace("text\n", " ").replace("\n", " ")
        value = re.sub(r"equation_inline\n?", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    @staticmethod
    def _search_blob(item: dict[str, Any]) -> str:
        parts = [
            item.get("evidence_link_id"),
            item.get("evidence_id"),
            item.get("material_id"),
            item.get("material_name"),
            item.get("spectrum_id"),
            item.get("book"),
            item.get("text"),
            item.get("spectrum_caption"),
            item.get("support_strength"),
        ]
        return " ".join(str(part) for part in parts if part).casefold()

    @staticmethod
    def _file_key(path: Path) -> tuple[int, int]:
        stat = path.stat()
        return stat.st_mtime_ns, stat.st_size

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
