import json
from functools import cached_property
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.schemas.analysis import EffectEvidence, EffectSummary, SpectraRecord, WavenumberSearchResult
from app.schemas.graph import CompoundRecord, FunctionalGroupDocument, GraphEdge, GraphNode, GraphResponse, GroupIndexItem
from app.services.term_service import EFFECT_ZH_MAP


class GraphService:
    def __init__(self, release_path: Path | None = None) -> None:
        settings = get_settings()
        self.release_path = release_path or settings.release_path
        self.docs_summary_path = settings.docs_summary_path

    @cached_property
    def manifest(self) -> dict:
        summary = self._read_json(self.docs_summary_path) if self.docs_summary_path.exists() else {}
        stats = self._compute_stats()
        return {
            "release_path": str(self.release_path),
            "release_id": summary.get("version", {}).get("knowledge_release_id", self.release_path.name),
            "schema_version": summary.get("version", {}).get("schema_version"),
            "document_version": summary.get("version", {}).get("document_version"),
            "generated_at": summary.get("version", {}).get("generated_at"),
            "status": summary.get("version", {}).get("status"),
            "stats": stats,
            "schema_summary": summary.get("schema_summary", {}),
            "data_summary": summary.get("data_summary", {}),
        }

    @cached_property
    def groups(self) -> dict[str, FunctionalGroupDocument]:
        loaded: dict[str, FunctionalGroupDocument] = {}
        for path in sorted(self.release_path.glob("FG_*.json")):
            raw = self._normalize_card(self._read_json(path))
            loaded[raw["group_id"]] = FunctionalGroupDocument.model_validate(raw)
        return loaded

    @cached_property
    def index(self) -> list[GroupIndexItem]:
        return [self._index_item(group) for group in self.groups.values()]

    def list_groups(self, query: str | None = None) -> list[GroupIndexItem]:
        items = self.index
        if not query:
            return items
        q = query.lower()
        return [
            item for item in items
            if q in item.group_id.lower()
            or q in item.name_zh.lower()
            or q in item.name_en.lower()
            or q in (item.chemical_formula or "").lower()
            or q in (item.smarts or "").lower()
            or q in (item.group_class or "").lower()
        ]

    def get_group(self, group_id: str) -> FunctionalGroupDocument | None:
        return self.groups.get(group_id)

    def list_compounds(self, query: str | None = None) -> list[CompoundRecord]:
        compounds: dict[str, dict[str, Any]] = {}
        for group in self.groups.values():
            for example in group.compound_examples:
                compound = example.get("compound") or {}
                compound_id = compound.get("compound_id") or example.get("example_id")
                if not compound_id:
                    continue
                names = compound.get("names") or {}
                rec = compounds.setdefault(compound_id, {
                    "compound_id": compound_id,
                    "name_zh": names.get("zh"),
                    "name_en": names.get("en"),
                    "molecular_formula": compound.get("molecular_formula"),
                    "smiles": compound.get("smiles"),
                    "compound_class": compound.get("compound_class"),
                    "group_ids": set(),
                    "spectrum_count": 0,
                    "peak_count": 0,
                })
                rec["group_ids"].add(group.group_id)
                spectra = example.get("spectra") or []
                rec["spectrum_count"] += len(spectra)
                rec["peak_count"] += sum(len(s.get("peaks") or []) for s in spectra)
        items = [CompoundRecord(**{**rec, "group_ids": sorted(rec["group_ids"])}) for rec in compounds.values()]
        if query:
            q = query.lower()
            items = [item for item in items if q in item.compound_id.lower() or q in (item.name_zh or "").lower() or q in (item.name_en or "").lower() or q in (item.molecular_formula or "").lower()]
        return sorted(items, key=lambda item: (-item.spectrum_count, item.compound_id))

    def build_graph(self) -> GraphResponse:
        nodes: dict[str, GraphNode] = {}
        edges: dict[str, GraphEdge] = {}
        for group in self.groups.values():
            nodes[group.group_id] = GraphNode(
                id=group.group_id,
                label=group.name_zh,
                type="group",
                data={"name_en": group.name_en, "formula": group.chemical_formula, "smarts": group.smarts, "count": len(group.compound_examples)},
            )
            for vib in group.vibration_templates or group.inherent_vibrations:
                node_id = f"{group.group_id}:{vib.vibration_id}"
                nodes[node_id] = GraphNode(
                    id=node_id,
                    label=vib.symbol or vib.mode or vib.vibration_id,
                    type="vibration",
                    data={"mode": vib.mode, "range": self._range_label(vib), "diagnosticity": vib.diagnosticity},
                )
                edges[f"{group.group_id}->{node_id}"] = GraphEdge(id=f"{group.group_id}->{node_id}", source=group.group_id, target=node_id, label="has_vibration")
            for example in group.compound_examples:
                compound = example.get("compound") or {}
                compound_id = compound.get("compound_id")
                if compound_id:
                    names = compound.get("names") or {}
                    nodes.setdefault(compound_id, GraphNode(id=compound_id, label=names.get("zh") or names.get("en") or compound_id, type="compound", data={"smiles": compound.get("smiles"), "formula": compound.get("molecular_formula")}))
                    edges.setdefault(f"{compound_id}->{group.group_id}", GraphEdge(id=f"{compound_id}->{group.group_id}", source=compound_id, target=group.group_id, label="contains_group"))
                for spectrum in example.get("spectra") or []:
                    spectrum_id = spectrum.get("spectrum_id")
                    if spectrum_id and compound_id:
                        nodes.setdefault(spectrum_id, GraphNode(id=spectrum_id, label=spectrum.get("figure_id") or spectrum_id, type="spectrum", data={"image_path": spectrum.get("image_path"), "peak_count": len(spectrum.get("peaks") or [])}))
                        edges.setdefault(f"{compound_id}->{spectrum_id}", GraphEdge(id=f"{compound_id}->{spectrum_id}", source=compound_id, target=spectrum_id, label="has_spectrum"))
            for i, relation in enumerate(group.relations):
                subject = relation.get("subject")
                obj = relation.get("object")
                if subject and obj and subject in nodes and obj in nodes:
                    edge_id = f"rel:{group.group_id}:{i}:{subject}->{obj}"
                    edges.setdefault(edge_id, GraphEdge(id=edge_id, source=subject, target=obj, label=relation.get("relation_type", "related_to"), data=relation))
        return GraphResponse(nodes=list(nodes.values()), edges=list(edges.values()))

    def search_wavenumber(self, value: float, tolerance: float = 15) -> list[WavenumberSearchResult]:
        results: list[WavenumberSearchResult] = []
        for group in self.groups.values():
            evidence_by_id = {e.get("evidence_id"): e for e in group.evidence_spans}
            for example in group.compound_examples:
                compound = example.get("compound") or {}
                names = compound.get("names") or {}
                for spectrum in example.get("spectra") or []:
                    quote = spectrum.get("analysis_quote")
                    for peak in spectrum.get("peaks") or []:
                        matches = self._peak_match_values(peak)
                        for wavenumber, distance, is_range in matches:
                            if distance <= tolerance:
                                assignment = self._assignment_text(peak)
                                evidence_ids = peak.get("evidence_ids") or []
                                source_book = self._first_source_book(evidence_ids, evidence_by_id)
                                results.append(WavenumberSearchResult(
                                    group_id=group.group_id,
                                    group_name_zh=group.name_zh,
                                    group_name_en=group.name_en,
                                    match_type="measured_peak_range" if is_range else "measured_peak",
                                    wavenumber=wavenumber,
                                    distance=distance,
                                    vibration_id=self._assignment_vibration_id(peak),
                                    assignment=assignment or peak.get("notes"),
                                    evidence_quote=quote,
                                    image_path=spectrum.get("image_path"),
                                    figure_id=spectrum.get("figure_id"),
                                    spectrum_id=spectrum.get("spectrum_id"),
                                    compound_id=compound.get("compound_id"),
                                    compound_name_zh=names.get("zh"),
                                    source_book=source_book,
                                    evidence_ids=evidence_ids,
                                ))
            for vib in group.vibration_templates:
                for wr in vib.wavenumber_ranges:
                    match = self._range_match(wr.model_dump(), value)
                    if match and match[1] <= tolerance:
                        wavenumber, distance, is_range = match
                        results.append(WavenumberSearchResult(
                            group_id=group.group_id,
                            group_name_zh=group.name_zh,
                            group_name_en=group.name_en,
                            match_type="template_range" if is_range else "template_peak",
                            wavenumber=wavenumber,
                            distance=distance,
                            vibration_id=vib.vibration_id,
                            assignment=vib.textbook_description,
                            evidence_quote=vib.textbook_description,
                            evidence_ids=vib.evidence_ids,
                        ))
        return sorted(results, key=lambda item: (0 if item.match_type.startswith("measured") else 1, item.distance or 0))

    def list_effects(self) -> list[EffectSummary]:
        counts: dict[tuple[str, str], int] = {}
        for evidence in self._iter_effect_evidence():
            key = (evidence.effect_key, evidence.effect_type)
            counts[key] = counts.get(key, 0) + 1
        return sorted([EffectSummary(effect_key=key, effect_type=kind, effect_zh=EFFECT_ZH_MAP.get(key, (key, None))[0], term_id=EFFECT_ZH_MAP.get(key, (key, None))[1], count=count) for (key, kind), count in counts.items()], key=lambda item: (-item.count, item.effect_type, item.effect_key))

    def get_effect(self, effect_key: str) -> list[EffectEvidence]:
        return [item for item in self._iter_effect_evidence() if item.effect_key == effect_key]

    def list_spectra(self) -> list[SpectraRecord]:
        spectra: list[SpectraRecord] = []
        for group in self.groups.values():
            for example in group.compound_examples:
                compound = example.get("compound") or {}
                names = compound.get("names") or {}
                substance = example.get("substance") or {}
                for spectrum in example.get("spectra") or []:
                    spectrum_id = spectrum.get("spectrum_id") or spectrum.get("figure_id")
                    if not spectrum_id:
                        continue
                    spectra.append(SpectraRecord(
                        group_id=group.group_id,
                        group_name_zh=group.name_zh,
                        spectrum_id=spectrum_id,
                        figure_id=spectrum.get("figure_id"),
                        figure_caption=spectrum.get("figure_caption"),
                        compound_id=compound.get("compound_id"),
                        compound_name_zh=names.get("zh"),
                        compound_name_en=names.get("en"),
                        molecular_formula=compound.get("molecular_formula"),
                        smiles=compound.get("smiles"),
                        sample_state=substance.get("physical_state"),
                        image_path=spectrum.get("image_path"),
                        annotated_peak_count=len(spectrum.get("peaks") or []),
                        evidence_ids=spectrum.get("evidence_ids") or [],
                    ))
        return sorted(spectra, key=lambda item: (item.group_id, item.spectrum_id))

    def _iter_effect_evidence(self) -> list[EffectEvidence]:
        evidence: list[EffectEvidence] = []
        for group in self.groups.values():
            for gallery in group.spectral_gallery:
                for peak in gallery.annotated_peaks:
                    for effect_type, effect_key in (("chemical", peak.chemical_effect), ("state", peak.state_effect)):
                        if not effect_key:
                            continue
                        zh, term_id = EFFECT_ZH_MAP.get(effect_key, (effect_key, None))
                        evidence.append(EffectEvidence(effect_key=effect_key, effect_type=effect_type, effect_zh=zh, term_id=term_id, group_id=group.group_id, group_name_zh=group.name_zh, vibration_id=peak.vibration_id, measured_wavenumber=peak.measured_wavenumber, peak_assignment=peak.peak_assignment, figure_id=gallery.figure_id, image_path=gallery.mineru_crop_image_path, evidence_quote=gallery.textbook_analysis_quote))
        return evidence

    def _compute_stats(self) -> dict[str, int]:
        groups = list(self.groups.values()) if "groups" in self.__dict__ else [FunctionalGroupDocument.model_validate(self._normalize_card(self._read_json(path))) for path in sorted(self.release_path.glob("FG_*.json"))]
        return {
            "functional_groups": len(groups),
            "evidence_spans": sum(len(g.evidence_spans) for g in groups),
            "vibration_templates": sum(len(g.vibration_templates) for g in groups),
            "source_claims": sum(len(g.source_claims) for g in groups),
            "relations": sum(len(g.relations) for g in groups),
            "compound_examples": sum(len(g.compound_examples) for g in groups),
            "spectra": sum(len(ex.get("spectra") or []) for g in groups for ex in g.compound_examples),
            "peaks": sum(len(sp.get("peaks") or []) for g in groups for ex in g.compound_examples for sp in (ex.get("spectra") or [])),
            "image_assets": len(list((self.release_path / "assets" / "spectra").glob("*"))) if (self.release_path / "assets" / "spectra").exists() else 0,
        }

    def _index_item(self, group: FunctionalGroupDocument) -> GroupIndexItem:
        spectra = [sp for ex in group.compound_examples for sp in (ex.get("spectra") or [])]
        peaks = [pk for sp in spectra for pk in (sp.get("peaks") or [])]
        images = [sp.get("image_path") for sp in spectra if sp.get("image_path")]
        return GroupIndexItem(group_id=group.group_id, name_zh=group.name_zh, name_en=group.name_en, chemical_formula=group.chemical_formula, smarts=group.smarts, group_class=(group.group or {}).get("group_class"), vibration_count=len(group.vibration_templates), spectrum_count=len(spectra), peak_count=len(peaks), image_count=len(images), evidence_count=len(group.evidence_spans), compound_count=len(group.compound_examples), source_claim_count=len(group.source_claims), relation_count=len(group.relations))

    def _normalize_card(self, raw: dict[str, Any]) -> dict[str, Any]:
        group = raw.get("group") or {}
        raw.setdefault("name_zh", group.get("canonical_name_zh") or raw.get("group_id"))
        raw.setdefault("name_en", group.get("canonical_name_en") or raw.get("group_id"))
        if not raw.get("smarts"):
            raw["smarts"] = self._first_smarts(group)
        if not raw.get("chemical_formula"):
            raw["chemical_formula"] = group.get("formula_fragment")
        raw["inherent_vibrations"] = raw.get("vibration_templates") or raw.get("inherent_vibrations") or []
        raw["spectral_gallery"] = self._gallery_from_examples(raw.get("compound_examples") or []) or raw.get("spectral_gallery") or []
        return raw

    def _gallery_from_examples(self, examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
        gallery: list[dict[str, Any]] = []
        for example in examples:
            compound = example.get("compound") or {}
            names = compound.get("names") or {}
            substance = example.get("substance") or {}
            for spectrum in example.get("spectra") or []:
                gallery.append({
                    "spectrum_id": spectrum.get("spectrum_id"),
                    "figure_id": spectrum.get("figure_id") or spectrum.get("spectrum_id"),
                    "figure_caption": spectrum.get("figure_caption"),
                    "compound_id": compound.get("compound_id"),
                    "compound_name_zh": names.get("zh"),
                    "compound_name_en": names.get("en"),
                    "molecular_formula": compound.get("molecular_formula"),
                    "smiles": compound.get("smiles"),
                    "sample_state": substance.get("physical_state"),
                    "pdf_page_number": spectrum.get("page_pdf"),
                    "mineru_crop_image_path": spectrum.get("image_path"),
                    "textbook_analysis_quote": spectrum.get("analysis_quote"),
                    "annotated_peaks": [self._legacy_peak(peak) for peak in spectrum.get("peaks") or []],
                })
        return gallery

    def _legacy_peak(self, peak: dict[str, Any]) -> dict[str, Any]:
        assignments = peak.get("assignments") or []
        first = assignments[0] if assignments else {}
        return {"peak_id": peak.get("peak_id"), "measured_wavenumber": peak.get("wavenumber_cm_1") or peak.get("wavenumber_min_cm_1"), "transmittance_percent": peak.get("transmittance_percent"), "vibration_id": first.get("vibration_id"), "peak_assignment": first.get("assignment_text") or peak.get("notes"), "assignments": assignments, "evidence_ids": peak.get("evidence_ids") or []}

    @staticmethod
    def _first_smarts(group: dict[str, Any]) -> str | None:
        patterns = group.get("smarts_patterns") or []
        return patterns[0].get("pattern") if patterns else None

    @staticmethod
    def _read_json(path: Path) -> dict | list:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _range_label(vib: Any) -> list[float] | str | None:
        if getattr(vib, "base_wavenumber_range", None):
            return vib.base_wavenumber_range
        ranges = getattr(vib, "wavenumber_ranges", []) or []
        if not ranges:
            return None
        first = ranges[0]
        if first.peak_cm_1 is not None:
            return str(first.peak_cm_1)
        return [first.min_cm_1, first.max_cm_1]

    @classmethod
    def _peak_match_values(cls, peak: dict[str, Any]) -> list[tuple[float | list[float], float, bool]]:
        if peak.get("wavenumber_cm_1") is not None:
            return [(float(peak["wavenumber_cm_1"]), 0, False)]
        if peak.get("wavenumber_min_cm_1") is not None and peak.get("wavenumber_max_cm_1") is not None:
            low, high = sorted([float(peak["wavenumber_min_cm_1"]), float(peak["wavenumber_max_cm_1"])])
            return [([low, high], 0, True)]
        return []

    @classmethod
    def _range_match(cls, range_obj: dict[str, Any], value: float) -> tuple[float | list[float], float, bool] | None:
        if range_obj.get("peak_cm_1") is not None:
            peak = float(range_obj["peak_cm_1"])
            return peak, abs(peak - value), False
        if range_obj.get("min_cm_1") is not None and range_obj.get("max_cm_1") is not None:
            low, high = sorted([float(range_obj["min_cm_1"]), float(range_obj["max_cm_1"])])
            distance = 0 if low <= value <= high else min(abs(value - low), abs(value - high))
            return [low, high], distance, True
        return None

    @staticmethod
    def _assignment_text(peak: dict[str, Any]) -> str | None:
        assignments = peak.get("assignments") or []
        return "; ".join(filter(None, [a.get("assignment_text") for a in assignments])) or None

    @staticmethod
    def _assignment_vibration_id(peak: dict[str, Any]) -> str | None:
        for assignment in peak.get("assignments") or []:
            if assignment.get("vibration_id"):
                return assignment["vibration_id"]
        return None

    @staticmethod
    def _first_source_book(evidence_ids: list[str], evidence_by_id: dict[str, dict[str, Any]]) -> str | None:
        for evidence_id in evidence_ids:
            evidence = evidence_by_id.get(evidence_id) or {}
            source = evidence.get("source") or evidence.get("source_book")
            if isinstance(source, dict):
                return source.get("source_title") or source.get("book_title")
            if source:
                return str(source)
        return None
