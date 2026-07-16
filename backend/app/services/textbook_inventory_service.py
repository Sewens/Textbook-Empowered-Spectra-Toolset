from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class TextbookInventoryService:
    """Lazy reader for the broad, source-preserving textbook staging catalogs."""

    def __init__(self, inventory_path: Path | None = None, source_outputs_path: Path | None = None) -> None:
        self.inventory_path = Path(inventory_path) if inventory_path else None
        self.source_outputs_path = Path(source_outputs_path) if source_outputs_path else None
        self._catalogs: dict[str, dict[str, Any]] = {}
        self._books: dict[str, dict[str, Any]] = {}
        self._relationship_graph_cache: tuple[tuple[int, int], dict[str, Any]] | None = None

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

    def unified_detail(
        self,
        kind: str,
        candidate_id: str,
        *,
        offset: int = 0,
        limit: int = 12,
        threshold: int = 12,
    ) -> dict[str, Any] | None:
        """Return material/spectrum detail with waterfall-friendly spectrum pagination.

        Always returns a summary header. Spectra are flattened across books and returned
        as a pageable stream under items. When total spectra exceed threshold,
        clients should load subsequent pages with offset/limit instead of expanding all.
        """
        id_key = {"materials": "material_candidate_id", "spectra": "spectrum_candidate_id"}[kind]
        item = self._get(kind, id_key, candidate_id)
        if item is None:
            return None

        offset = max(0, int(offset or 0))
        limit = max(1, min(int(limit or 12), 50))
        threshold = max(1, int(threshold or 12))

        books_meta: list[dict[str, Any]] = []
        flat_spectra: list[dict[str, Any]] = []
        group_map: dict[str, dict[str, Any]] = {}
        material_map: dict[str, dict[str, Any]] = {}
        total_evidence = 0
        total_images = 0

        for source in item.get("source_records", []):
            book = source.get("book", "")
            payload = self._source_book(book)
            record = self._detail_from_book(kind, candidate_id, book) or source.get("record", {})
            materials = {value.get("material_candidate_id"): value for value in payload.get("material_candidates", [])}
            groups = {value.get("group_candidate_id"): value for value in payload.get("group_candidates", [])}
            spectra = {value.get("spectrum_candidate_id"): value for value in payload.get("spectrum_candidates", [])}
            features = {value.get("feature_candidate_id"): value for value in payload.get("feature_candidates", [])}
            images = {value.get("image_candidate_id"): value for value in payload.get("image_candidates", [])}
            evidence = {value.get("evidence_id"): value for value in payload.get("evidence_spans", [])}

            spectrum_ids = record.get("spectrum_ids", []) if kind == "materials" else [candidate_id]
            material_ids = record.get("material_candidate_ids", []) if kind == "spectra" else [candidate_id]
            group_ids = record.get("group_candidate_ids", [])
            evidence_ids = [eid for eid in record.get("evidence_ids", []) if eid in evidence]
            total_evidence += len(evidence_ids)

            book_materials = [self._material_card(materials[mid]) for mid in material_ids if mid in materials]
            book_groups = [self._group_card(groups[gid]) for gid in group_ids if gid in groups]
            for mat in book_materials:
                if mat.get("id"):
                    material_map[mat["id"]] = mat
            for group in book_groups:
                if group.get("id"):
                    group_map[group["id"]] = group

            ranked_spectrum_ids = sorted(
                [sid for sid in spectrum_ids if sid in spectra],
                key=lambda sid: (
                    0 if any((images.get(iid) or {}).get("source_image_path") for iid in (spectra[sid].get("image_candidate_ids") or [])) else 1,
                    sid,
                ),
            )
            book_image_count = 0
            for sid in ranked_spectrum_ids:
                card = self._spectrum_card(book, spectra[sid], features, images, evidence)
                book_image_count += len(card.get("images") or [])
                flat_spectra.append({
                    "book": book,
                    "source_id": source.get("source_id"),
                    "page": card.get("page") or record.get("source_page"),
                    "content_list_index": card.get("content_list_index") or record.get("content_list_index"),
                    "spectrum": card,
                })
            total_images += book_image_count
            books_meta.append({
                "book": book,
                "source_id": source.get("source_id"),
                "page": record.get("source_page"),
                "content_list_index": record.get("content_list_index"),
                "materials": book_materials,
                "groups": book_groups,
                "spectra_total": len(ranked_spectrum_ids),
                "evidence_total": len(evidence_ids),
                "images_total": book_image_count,
            })

        spectra_total = len(flat_spectra)
        stream_mode = spectra_total > threshold
        page_items = flat_spectra[offset: offset + limit]
        returned = len(page_items)
        next_offset = offset + returned
        has_more = next_offset < spectra_total
        summary = self._summary_item(kind, item)
        return {
            "detail_kind": "material" if kind == "materials" else "spectrum",
            "id": candidate_id,
            "title": summary["name"],
            "review_status": summary["review_status"],
            "books": summary["books"],
            "source_count": summary["source_count"],
            "materials": list(material_map.values()),
            "groups": list(group_map.values()),
            "book_summaries": books_meta,
            "items": page_items,
            "counts": {
                "spectra_total": spectra_total,
                "evidence_total": total_evidence,
                "images_total": total_images,
                "returned": returned,
                "threshold": threshold,
                "stream": stream_mode,
            },
            "page": {
                "offset": offset,
                "limit": limit,
                "returned": returned,
                "has_more": has_more,
                "next_offset": next_offset if has_more else None,
            },
            # Backward-compatible nested cards for current page only.
            "source_cards": self._group_stream_items_as_source_cards(page_items, books_meta),
        }

    def _group_stream_items_as_source_cards(self, items: list[dict[str, Any]], books_meta: list[dict[str, Any]]) -> list[dict[str, Any]]:
        meta = {row.get("book"): row for row in books_meta}
        order: list[str] = []
        buckets: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            book = item.get("book") or ""
            if book not in buckets:
                buckets[book] = []
                order.append(book)
            buckets[book].append(item.get("spectrum") or {})
        cards: list[dict[str, Any]] = []
        for book in order:
            info = meta.get(book, {"book": book, "materials": [], "groups": [], "spectra_total": 0, "evidence_total": 0})
            spectra = buckets.get(book, [])
            cards.append({
                "book": book,
                "source_id": info.get("source_id"),
                "page": info.get("page"),
                "content_list_index": info.get("content_list_index"),
                "materials": info.get("materials", []),
                "groups": info.get("groups", []),
                "spectra": spectra,
                "evidence": [],
                "counts": {
                    "spectra_total": info.get("spectra_total", 0),
                    "spectra_returned": len(spectra),
                    "evidence_total": info.get("evidence_total", 0),
                    "evidence_returned": 0,
                    "images_returned": sum(len(spec.get("images") or []) for spec in spectra),
                    "truncated": (info.get("spectra_total", 0) or 0) > len(spectra),
                },
            })
        return cards

    @staticmethod
    def _material_card(record: dict[str, Any]) -> dict[str, Any]:
        return {"id": record.get("material_candidate_id"), "name": record.get("canonical_name_candidate"), "source_forms": record.get("source_forms", []), "material_type": record.get("material_type"), "review_status": record.get("promotion_status")}

    @staticmethod
    def _group_card(record: dict[str, Any]) -> dict[str, Any]:
        preferred = record.get("preferred_name", {})
        return {"id": record.get("group_candidate_id"), "name": preferred.get("zh") or preferred.get("en") or preferred.get("source") or record.get("group_candidate_id"), "review_status": record.get("promotion_status")}

    @staticmethod
    def _evidence_card(record: dict[str, Any]) -> dict[str, Any]:
        locator = record.get("locator", {})
        text = record.get("text_original") or ""
        if len(text) > 500:
            text = text[:500] + "..."
        return {"id": record.get("evidence_id"), "type": record.get("evidence_type"), "text": text, "page": locator.get("pdf_page"), "content_list_index": locator.get("content_list_index"), "bbox": locator.get("bbox")}

    def _spectrum_card(self, book: str, record: dict[str, Any], features: dict[str, dict[str, Any]], images: dict[str, dict[str, Any]], evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
        caption = record.get("caption_or_context") or ""
        if len(caption) > 400:
            caption = caption[:400] + "..."
        feature_ids = (record.get("feature_candidate_ids") or [])[:12]
        evidence_ids = (record.get("evidence_ids") or [])[:3]
        image_ids = (record.get("image_candidate_ids") or [])[:2]
        return {
            "id": record.get("spectrum_candidate_id"),
            "caption": caption,
            "page": record.get("source_page"),
            "content_list_index": record.get("content_list_index"),
            "features": [features[value] for value in feature_ids if value in features],
            "images": [{"id": image.get("image_candidate_id"), "book": book, "path": image.get("source_image_path"), "caption": image.get("caption_or_nearby_context")} for value in image_ids if (image := images.get(value)) and image.get("source_image_path")],
            "evidence": [self._evidence_card(evidence[value]) for value in evidence_ids if value in evidence],
        }

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

    _STRUCTURAL_GROUPS = {
        "FG_ALDEHYDE": "醛基", "FG_AMIDE": "酰胺基", "FG_ANHYDRIDE": "酸酐基", "FG_CARBONYL": "羰基", "FG_CARBONYL_KETONE": "酮羰基", "FG_CARBOXYL": "羧基", "FG_CC_DOUBLE": "碳碳双键", "FG_CC_TRIPLE": "碳碳三键", "FG_CN_AMINE": "胺C-N", "FG_COC_ETHER": "醚键", "FG_ESTER": "酯基", "FG_HYDROXYL": "羟基", "FG_ISOCYANATE": "异氰酸酯基", "FG_METHYL": "甲基", "FG_METHYLENE": "亚甲基", "FG_NITRILE": "腈基", "FG_NITRO": "硝基",
    }

    def material_relationship_graph(self) -> dict[str, Any]:
        """Return the all-material graph from conservative name-grounded rules."""
        overview = self.overview()
        if not overview.get("available"):
            return {"run_id": None, "layout_key": None, "nodes": [], "edges": [], "stats": {}}
        source_key = self._relationship_source_key()
        if self._relationship_graph_cache and self._relationship_graph_cache[0] == source_key:
            return self._relationship_graph_cache[1]
        self._catalogs.pop("materials", None)
        materials, memberships, rules = [], {}, {}
        for item in self._load("materials").get("materials", []):
            summary = self._summary_item("materials", item)
            material_id = summary["candidate_id"]
            group_rules = self._structural_groups_for_name(summary["name"])
            memberships[material_id] = set(group_rules)
            for group_id, values in group_rules.items():
                rules[(material_id, group_id)] = values
            materials.append({"id": material_id, "label": summary["name"], "type": "material", "books": summary["books"], "relationship_status": "name_rule_derived" if group_rules else "needs_structure_confirmation"})
        group_ids = {group_id for groups in memberships.values() for group_id in groups}
        nodes = [{"id": group_id, "label": self._STRUCTURAL_GROUPS[group_id], "type": "functional_group", "relationship_status": "controlled_root"} for group_id in sorted(group_ids)] + materials
        edges = []
        for material_id, groups in memberships.items():
            for group_id in sorted(groups):
                edges.append({"id": f"{group_id}__has_functional_group__{material_id}", "source": group_id, "target": material_id, "relation_type": "has_functional_group", "label": "组成基团", "derivation": "name_rule", "rules": rules[(material_id, group_id)]})
        material_ids = sorted(memberships)
        for index, left in enumerate(material_ids):
            for right in material_ids[index + 1:]:
                shared = memberships[left] & memberships[right]
                if len(shared) >= 2:
                    edges.append({"id": f"{left}__shares_functional_groups__{right}", "source": left, "target": right, "relation_type": "shares_functional_groups", "label": "共享基础基团", "derivation": "group_overlap", "shared_group_ids": sorted(shared), "shared_group_count": len(shared)})
        graph = {"run_id": overview.get("run_id"), "layout_key": self._relationship_layout_key(nodes, edges), "nodes": nodes, "edges": edges, "stats": {"functional_groups": len(group_ids), "materials": len(materials), "material_group_edges": sum(edge["relation_type"] == "has_functional_group" for edge in edges), "material_similarity_edges": sum(edge["relation_type"] == "shares_functional_groups" for edge in edges), "unresolved_materials": sum(not groups for groups in memberships.values())}, "policy": {"structural_edges": "name_rule_derived", "contextual_group_candidates_included": False, "material_similarity": "shared_two_or_more_high_confidence_groups"}}
        self._relationship_graph_cache = (source_key, graph)
        return graph

    def _relationship_source_key(self) -> tuple[int, int]:
        path = self.inventory_path / "_compound_catalog.json"
        stat = path.stat()
        return stat.st_mtime_ns, stat.st_size

    @staticmethod
    def _relationship_layout_key(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
        payload = {"nodes": sorted(node["id"] for node in nodes), "edges": sorted(edge["id"] for edge in edges)}
        return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _structural_groups_for_name(cls, name: str) -> dict[str, list[str]]:
        value, groups = name.casefold().strip(), {}
        def add(group_id: str, rule: str) -> None:
            groups.setdefault(group_id, []).append(rule)
        if any(term in value for term in ("alcohol", "methanol", "ethanol", "propanol", "butanol", "phenol")) or any(term in name for term in ("醇", "酚")):
            add("FG_HYDROXYL", "alcohol_or_phenol_name")
        if value in {"methanol", "甲醇"}:
            add("FG_METHYL", "methanol_name")
        elif value in {"ethanol", "乙醇"}:
            add("FG_METHYL", "ethanol_name")
            add("FG_METHYLENE", "ethanol_name")
        if any(term in value for term in ("aldehyde", "formaldehyde")) or "醛" in name:
            add("FG_ALDEHYDE", "aldehyde_name"); add("FG_CARBONYL", "aldehyde_name")
        if any(term in value for term in ("ketone", "acetone")) or "酮" in name:
            add("FG_CARBONYL_KETONE", "ketone_name"); add("FG_CARBONYL", "ketone_name")
        if any(term in value for term in ("carboxylic acid", "benzoic acid", "acetic acid")) or "羧酸" in name:
            add("FG_CARBOXYL", "carboxylic_acid_name")
        if any(term in value for term in ("ester", "acetate")) or "酯" in name: add("FG_ESTER", "ester_name")
        if "amide" in value or "酰胺" in name: add("FG_AMIDE", "amide_name")
        if "nitrile" in value or "腈" in name: add("FG_NITRILE", "nitrile_name")
        if "nitro" in value or "硝基" in name: add("FG_NITRO", "nitro_name")
        if "isocyanate" in value or "异氰酸酯" in name: add("FG_ISOCYANATE", "isocyanate_name")
        if "anhydride" in value or "酸酐" in name: add("FG_ANHYDRIDE", "anhydride_name")
        if "ether" in value or "醚" in name: add("FG_COC_ETHER", "ether_name")
        if "amine" in value or "胺" in name: add("FG_CN_AMINE", "amine_name")
        if "methyl" in value or "甲基" in name: add("FG_METHYL", "methyl_name")
        if "methylene" in value or "亚甲基" in name: add("FG_METHYLENE", "methylene_name")
        if "alkene" in value or "烯" in name: add("FG_CC_DOUBLE", "alkene_name")
        if "alkyne" in value or "炔" in name: add("FG_CC_TRIPLE", "alkyne_name")
        return groups

    def asset_path(self, book: str, asset_path: str) -> Path | None:
        if not self.available or book not in self.books() or not self.source_outputs_path:
            return None
        base_root = self.source_outputs_path.resolve()
        base = (base_root / book / "unzipped").resolve()
        if base_root not in base.parents:
            return None
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
        array_key = {"groups": "group_candidates", "materials": "material_candidates", "spectra": "spectrum_candidates"}[kind]
        return next((item for item in payload.get(array_key, []) if item.get(key) == candidate_id), None)

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path or not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
