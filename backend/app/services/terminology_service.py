import json
from pathlib import Path
from typing import Any


class TerminologyCatalogService:
    """Read the deduplicated terminology view without mutating raw textbook data."""

    def __init__(self, catalog_path: Path | None = None) -> None:
        self.catalog_path = Path(catalog_path) if catalog_path else None
        self._catalog: dict[str, Any] | None = None

    @property
    def available(self) -> bool:
        return bool(self.catalog_path and self.catalog_path.exists())

    def _load(self) -> dict[str, Any]:
        if self._catalog is None:
            if not self.available:
                self._catalog = {"terms": [], "source_specific_claims": [], "evidence_spans": [], "source_count": 0}
            else:
                self._catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        return self._catalog

    def overview_counts(self) -> dict[str, int]:
        data = self._load()
        return {
            "terminology_terms": len(data.get("terms", [])),
            "terminology_sources": int(data.get("source_count", 0)),
            "terminology_claims": len(data.get("source_specific_claims", [])),
            "terminology_evidence": len(data.get("evidence_spans", [])),
        }

    def list_terms(self, query: str | None = None, limit: int = 300) -> list[dict[str, Any]]:
        terms = self._load().get("terms", [])
        token = query.casefold() if query else None
        rows = []
        for term in terms:
            names = term.get("preferred_name", {})
            search_text = " ".join([term.get("term_id", ""), term.get("concept_type", ""), *[str(v) for v in names.values()], *term.get("all_source_forms", [])]).casefold()
            if token and token not in search_text:
                continue
            rows.append(self._list_item(term))
            if len(rows) >= limit:
                break
        return rows

    def get_term(self, term_id: str) -> dict[str, Any] | None:
        data = self._load()
        term = next((item for item in data.get("terms", []) if item.get("term_id") == term_id), None)
        if term is None:
            return None
        source_ids = {row.get("source_id") for row in term.get("source_records", [])}
        claims = [claim for claim in data.get("source_specific_claims", []) if claim.get("source_id") in source_ids and claim.get("subject_ref") == term_id]
        evidence_ids = set(term.get("all_evidence_ids", []))
        evidence = [item for item in data.get("evidence_spans", []) if item.get("evidence_id") in evidence_ids]
        return self._list_item(term) | {"source_records": term.get("source_records", []), "source_specific_claims": claims, "evidence_spans": evidence}

    @staticmethod
    def _list_item(term: dict[str, Any]) -> dict[str, Any]:
        names = term.get("preferred_name", {})
        return {
            "term_id": term["term_id"],
            "term_type": "concept",
            "name": names.get("zh") or names.get("en") or names.get("source") or term["term_id"],
            "source_scope": "textbook",
            "payload": {
                "concept_type": term.get("concept_type"),
                "preferred_name": names,
                "all_source_forms": term.get("all_source_forms", []),
                "source_book_count": term.get("source_book_count", 0),
                "source_count": len(term.get("source_records", [])),
                "evidence_count": len(term.get("all_evidence_ids", [])),
                "status": term.get("status", "candidate_needs_review"),
            },
        }
