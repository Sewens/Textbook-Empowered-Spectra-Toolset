from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


SPECTRAL_CUES = re.compile(r"(?i)(infrared|IR\b|spectrum|spectra|absorption|band|stretch|bend|vibration|wavenumber|红外|光谱|吸收|谱带|峰|伸缩|弯曲|振动|波数)")
FREQUENCY = re.compile(r"(?<![\w.])(\d{3,4}(?:\.\d+)?)\s*(?:-|–|—|to|~|～)\s*(\d{3,4}(?:\.\d+)?)\s*(?:cm\s*(?:\^?\{?\s*-?1\s*\}?|[-−]1)|cm-1|cm⁻¹)", re.I)
SINGLE_FREQUENCY = re.compile(r"(?<![\w.])(\d{3,4}(?:\.\d+)?)\s*(?:cm\s*(?:\^?\{?\s*-?1\s*\}?|[-−]1)|cm-1|cm⁻¹)", re.I)
EFFECT_PATTERNS = [
    ("hydrogen_bonding_broadens", re.compile(r"(?i)(hydrogen bond|氢键).{0,120}(broaden|broader|broad|变宽|展宽|峰宽)", re.S), "broadened_by", "increase_width"),
    ("conjugation_lowers_wavenumber", re.compile(r"(?i)(conjugat|共轭).{0,160}(lower|lowered|decrease|decreased|red.?shift|降低|低频|红移)", re.S), "shifted_by", "decrease"),
    ("polar_solvent_broadens", re.compile(r"(?i)(polar solvent|极性溶剂).{0,160}(broaden|broader|变宽|展宽)", re.S), "broadened_by", "increase_width"),
]


class MaterialSpectrumClaimsService:
    """Strictly project textbook claims only from direct material-spectrum evidence."""

    def __init__(self, evidence_release_path: Path | None = None, claims_release_path: Path | None = None) -> None:
        self.evidence_release_path = Path(evidence_release_path) if evidence_release_path else None
        self.claims_release_path = Path(claims_release_path) if claims_release_path else None
        self._cache: tuple[tuple[int, int], list[dict[str, Any]]] | None = None

    @property
    def available(self) -> bool:
        return bool(self.claims_release_path and (self.claims_release_path / "claims.json").exists())

    def overview(self) -> dict[str, Any]:
        items = self.all_claims()
        predicates: dict[str, int] = {}
        for item in items:
            predicates[item["predicate"]] = predicates.get(item["predicate"], 0) + 1
        return {"available": self.available, "total": len(items), "by_predicate": predicates}

    def all_claims(self) -> list[dict[str, Any]]:
        if not self.available:
            return []
        path = self.claims_release_path / "claims.json"
        stat = path.stat()
        key = (stat.st_mtime_ns, stat.st_size)
        if self._cache and self._cache[0] == key:
            return self._cache[1]
        items = json.loads(path.read_text(encoding="utf-8")).get("items", [])
        self._cache = (key, items)
        return items

    def list_claims(self, query: str | None = None, predicate: str | None = None, limit: int = 300) -> list[dict[str, Any]]:
        token = query.casefold() if query else None
        output = []
        for claim in self.all_claims():
            if predicate and claim.get("predicate") != predicate:
                continue
            if token and token not in " ".join(str(claim.get(k, "")) for k in ["material_name", "spectrum_id", "book", "object_label", "evidence_text", "predicate"]).casefold():
                continue
            output.append(claim)
            if len(output) >= limit:
                break
        return output

    @classmethod
    def build_claims(cls, evidence_release_path: Path) -> list[dict[str, Any]]:
        evidence_file = evidence_release_path / "evidence_links.json"
        items = json.loads(evidence_file.read_text(encoding="utf-8")).get("items", [])
        claims: list[dict[str, Any]] = []
        seen: set[str] = set()
        for link in items:
            claim = cls._claim_from_link(link)
            if not claim or claim["claim_id"] in seen:
                continue
            seen.add(claim["claim_id"])
            claims.append(claim)
        rank = {"has_observed_band": 0, "broadened_by": 1, "shifted_by": 1}
        claims.sort(key=lambda c: (rank.get(c["predicate"], 9), c["book"], c["material_name"], c["claim_id"]))
        return claims

    @classmethod
    def _claim_from_link(cls, link: dict[str, Any]) -> dict[str, Any] | None:
        text = cls._clean(link.get("text") or "")
        material = (link.get("material_name") or "").strip()
        spectrum_id = link.get("spectrum_id")
        evidence_id = link.get("evidence_id")
        if not (material and spectrum_id and evidence_id and link.get("book")):
            return None
        # A material name elsewhere in a long paragraph is not enough. Keep only
        # the local sentence that names the material and contains a spectral value.
        local_text = cls._material_frequency_sentence(text, material)
        if not local_text or not SPECTRAL_CUES.search(local_text) or not cls._direct_material_spectrum_statement(local_text, material):
            return None
        values = cls._nearest_material_frequencies(local_text, material)
        if not values:
            return None
        effect = next(((name, predicate, direction) for name, pattern, predicate, direction in EFFECT_PATTERNS if pattern.search(local_text)), None)
        predicate = effect[1] if effect else "has_observed_band"
        first = values[0]
        object_label = effect[0].replace("_", " ") if effect else first[2]
        seed = "|".join([str(link.get("material_id")), str(spectrum_id), str(evidence_id), predicate, object_label])
        return {
            "claim_id": "CLM_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20],
            "material_id": link.get("material_id"),
            "material_name": material,
            "spectrum_id": spectrum_id,
            "predicate": predicate,
            "object_label": object_label,
            "object": {"frequencies_cm1": [{"lower": low, "upper": high, "raw_text": raw} for low, high, raw in values[:8]], "effect": effect[0] if effect else None},
            "qualifiers": {"direction": effect[2] if effect else None, "evidence_type": link.get("evidence_type"), "page": link.get("page")},
            "evidence_ids": [evidence_id],
            "evidence_text": local_text[:700],
            "book": link.get("book"),
            "source_id": link.get("source_id"),
            "page": link.get("page"),
            "image_paths": link.get("image_paths") or [],
            "assertion_status": "asserted",
            "review_status": "precision_screened_needs_review",
            "extraction_confidence": 0.94 if link.get("support_strength") == "high" else 0.88,
            "derivation_rules": ["direct_material_literal", "linked_material_spectrum_evidence", "spectral_cue", "frequency_with_cm1"] + (["explicit_effect_pattern"] if effect else []),
        }

    @classmethod
    def _nearest_material_frequencies(cls, text: str, material: str) -> list[tuple[float, float, str]]:
        # Keep only frequencies nearest to an exact material mention. This prevents
        # a material listed in a paragraph from inheriting a later, unrelated peak.
        positions = [match.start() for match in cls._material_matches(text, material)]
        candidates: list[tuple[int, float, float, str]] = []
        for match in FREQUENCY.finditer(text):
            low, high = float(match.group(1)), float(match.group(2))
            distance = min(abs(match.start() - pos) for pos in positions)
            candidates.append((distance, low, high, f"{match.group(1)}-{match.group(2)} cm-1"))
        for match in SINGLE_FREQUENCY.finditer(text):
            value = float(match.group(1))
            distance = min(abs(match.start() - pos) for pos in positions)
            candidates.append((distance, value, value, f"{match.group(1)} cm-1"))
        if not candidates:
            return []
        closest = min(item[0] for item in candidates)
        # A band must be close to its named material, and ties retain paired bands.
        if closest > 90:
            return []
        values: list[tuple[float, float, str]] = []
        seen: set[tuple[float, float]] = set()
        for distance, low, high, raw in candidates:
            if distance > closest + 24:
                continue
            key = (low, high)
            if key not in seen:
                seen.add(key)
                values.append((low, high, raw))
        return values

    @staticmethod
    def _material_matches(text: str, material: str):
        value = material.strip()
        if re.fullmatch(r"[A-Za-z0-9]{1,4}", value):
            return list(re.finditer(r"(?i)(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_{}]|\s*[_{]?\s*\d)", text))
        return list(re.finditer(re.escape(value), text, re.I))

    @classmethod
    def _direct_material_spectrum_statement(cls, text: str, material: str) -> bool:
        escaped = re.escape(material)
        # A substance must be grammatically tied to a spectrum/band assertion, not
        # merely appear as a fragment of a formula, an example list, or a ring/group.
        patterns = [
            rf"(?i)(?:spectrum|spectra|infrared|IR|band)\s+(?:of|for|from)\s+(?:the\s+)?{escaped}\b",
            rf"(?i)\b{escaped}\b.{0,55}(?:spectrum|spectra|infrared|IR|band|absorbs|absorption|exhibits|shows|appears)",
            rf"(?i)(?:spectrum|spectra|infrared|IR|band).{0,55}\b{escaped}\b",
            rf"{escaped}.{{0,45}}(?:的红外光谱|红外光谱|光谱中|谱图中|谱带|吸收峰|吸收带|出现在|位于)",
            rf"(?:{escaped})\s*(?:的)?\s*(?:红外|IR)\s*(?:光谱|谱图)",
        ]
        return any(re.search(pattern, text, re.S) for pattern in patterns)

    @classmethod
    def _material_frequency_sentence(cls, text: str, material: str) -> str | None:
        # Preserve localized factual support; do not bind a paragraph-wide material mention
        # to frequencies that actually describe a different compound or generic group.
        chunks = [part.strip() for part in re.split(r"(?<=[.!?。；;])\s+", text) if part.strip()]
        for chunk in chunks:
            if cls._contains_material(chunk, material) and SINGLE_FREQUENCY.search(chunk):
                return chunk
        return None

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\s+", " ", text.replace("text\n", " ").replace("\n", " ")).strip()

    @classmethod
    def _contains_material(cls, text: str, material: str) -> bool:
        return bool(cls._material_matches(text, material))
