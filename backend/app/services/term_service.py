import json
import re
from functools import cached_property
from pathlib import Path

from app.core.config import get_settings
from app.schemas.terms import RelatedGroupRef, TermDetail, TermItem


class TermService:
    def __init__(self, release_path: Path | None = None) -> None:
        self.release_path = release_path or get_settings().release_path
        self._terms_path = self.release_path.parent / "basic_terms" / "ir_basic_terms.json"

    @cached_property
    def _raw_terms(self) -> list[dict]:
        if not self._terms_path.exists():
            return []
        with self._terms_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)["terms"]

    @cached_property
    def _group_index(self) -> list[dict]:
        groups: list[dict] = []
        for path in sorted(self.release_path.glob("FG_*.json")):
            with path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
            group = raw.get("group") or {}
            patterns = group.get("smarts_patterns") or []
            groups.append({
                "group_id": raw.get("group_id"),
                "name_zh": raw.get("name_zh") or group.get("canonical_name_zh") or "",
                "name_en": raw.get("name_en") or group.get("canonical_name_en") or "",
                "chemical_formula": raw.get("chemical_formula") or group.get("formula_fragment"),
                "smarts": raw.get("smarts") or (patterns[0].get("pattern") if patterns else None),
            })
        return groups

    def list_terms(self, category: str | None = None) -> list[TermItem]:
        items: list[TermItem] = []
        for raw in self._raw_terms:
            if category and raw.get("category") != category:
                continue
            items.append(TermItem(
                term_id=raw["term_id"],
                category=raw["category"],
                term_en=raw["term_en"],
                term_zh=raw["term_zh"],
                aliases=raw.get("aliases", []),
                definition_zh=raw.get("definition_zh"),
            ))
        return items

    def get_term(self, term_id: str) -> TermDetail | None:
        raw = None
        for candidate in self._raw_terms:
            if candidate["term_id"] == term_id:
                raw = candidate
                break
        if not raw:
            return None

        source_data = raw.get("source") or {}
        source = None
        if source_data:
            from app.schemas.terms import TermSource

            source = TermSource(
                source_id=source_data.get("source_id", ""),
                source_title=source_data.get("source_title", ""),
                page_index=source_data.get("page_index"),
                matched_keyword=source_data.get("matched_keyword"),
                evidence_text=source_data.get("evidence_text"),
                evidence_quality=source_data.get("evidence_quality"),
            )

        return TermDetail(
            term_id=raw["term_id"],
            category=raw["category"],
            term_en=raw["term_en"],
            term_zh=raw["term_zh"],
            aliases=raw.get("aliases", []),
            definition_zh=raw.get("definition_zh"),
            source=source,
            related_groups=self._match_related_groups(raw),
        )

    def _match_related_groups(self, raw_term: dict) -> list[RelatedGroupRef]:
        """Match a basic term to functional groups using keyword overlap between
        term_en, term_zh, aliases and group name_zh, name_en, chemical_formula."""
        keywords: list[str] = []
        keywords.append(raw_term["term_en"].lower())
        keywords.append(raw_term["term_zh"].lower())
        for alias in raw_term.get("aliases", []):
            keywords.append(alias.lower())

        results: list[RelatedGroupRef] = []
        for group in self._group_index:
            match_score = 0
            best_reason = ""
            target_texts: list[str] = [
                group["name_zh"].lower() if group.get("name_zh") else "",
                group["name_en"].lower() if group.get("name_en") else "",
                group.get("chemical_formula", "") or "",
            ]
            for kw in keywords:
                if not kw or len(kw) < 2:
                    continue
                for target in target_texts:
                    if kw in target:
                        score = len(kw) / max(len(target), 1)
                        if score > match_score:
                            match_score = score
                            best_reason = f"关键词「{kw}」匹配到「{target}」"
            if match_score > 0.3 or any(
                kw in target_text for kw_text in keywords for kw in (kw_text.split(";") if kw_text else []) for target_text in target_texts if kw and len(kw) > 2 and kw in target_text
            ):
                # stronger matching: check if any full alias matches a group name exactly
                group_name_zh_lower = group.get("name_zh", "").lower()
                group_name_en_lower = group.get("name_en", "").lower()
                exact_match = raw_term["term_zh"] in group_name_zh_lower or raw_term["term_en"].lower() in group_name_en_lower
                for alias in raw_term.get("aliases", []):
                    if alias.lower() in group_name_zh_lower or alias.lower() in group_name_en_lower:
                        exact_match = True
                        break
                if exact_match or match_score > 0.3:
                    results.append(RelatedGroupRef(
                        group_id=group["group_id"],
                        name_zh=group.get("name_zh", ""),
                        name_en=group.get("name_en", ""),
                        match_reason=best_reason or "关键词匹配",
                    ))

        # deduplicate by group_id
        seen: set[str] = set()
        unique: list[RelatedGroupRef] = []
        for ref in results:
            if ref.group_id not in seen:
                seen.add(ref.group_id)
                unique.append(ref)
        return unique

    def categories(self) -> list[str]:
        cats: set[str] = set()
        for raw in self._raw_terms:
            if raw.get("category"):
                cats.add(raw["category"])
        return sorted(cats)


# Effect → Chinese label + related basic term mapping
EFFECT_ZH_MAP: dict[str, tuple[str, str | None]] = {
    # ── Chemical effects ──
    "induction_withdrawing": ("吸电子诱导效应", "IR_TERM_116"),
    "induction_withdrawing_dominant": ("吸电子诱导效应（主导）", "IR_TERM_116"),
    "conjugation_aromatic": ("芳环共轭效应", "IR_TERM_115"),
    "conjugation": ("共轭效应", "IR_TERM_115"),
    "conjugation_diene_coupling": ("共轭二烯耦合", "IR_TERM_115"),
    "conjugation_p_pi": ("p-π共轭", "IR_TERM_115"),
    "conjugation_p_pi_halogen": ("卤素p-π共轭", "IR_TERM_115"),
    "conjugation_pi_p": ("π-p共轭", "IR_TERM_115"),
    "conjugation_pi_pi": ("π-π共轭", "IR_TERM_115"),
    "hyperconjugation": ("超共轭效应", "IR_TERM_115"),
    "hyperconjugation_predominant": ("超共轭效应（主导）", "IR_TERM_115"),
    "hyperconjugation_sigma_p": ("σ-p超共轭", "IR_TERM_115"),
    "hyperconjugation_sigma_pi": ("σ-π超共轭", "IR_TERM_115"),
    "hyperconjugation_sigma_pi_aromatic": ("芳香σ-π超共轭", "IR_TERM_115"),
    "induction_and_hyperconjugation": ("诱导+超共轭共存", "IR_TERM_116"),
    "induction_and_hyperconjugation_balanced": ("诱导+超共轭抵消", "IR_TERM_116"),
    "induction_monosubstitution": ("单取代诱导效应", "IR_TERM_116"),
    "induction_monosubstitution_silicon": ("硅取代诱导效应", "IR_TERM_116"),
    "induction_disubstitution": ("双取代诱导效应", "IR_TERM_116"),
    "induction_trisubstitution": ("三取代诱导效应", "IR_TERM_116"),
    "ring_strain": ("环张力效应", None),
    "ring_strain_small": ("小环张力效应", None),
    "fermi_resonance": ("费米共振", "IR_TERM_117"),
    "hydrogen_bonding_intramolecular": ("分子内氢键", "IR_TERM_114"),
    "hydrogen_bonding_association": ("氢键缔合", "IR_TERM_114"),
    "methyl_substitution": ("甲基取代效应", "IR_TERM_040"),
    "polar_substitution_hydroxy": ("羟基极性取代", "IR_TERM_043"),
    "polar_substitution_multi_hydroxy": ("多羟基极性取代", "IR_TERM_043"),
    "bidentate_chelation": ("双齿螯合配位", None),
    "bridging_coordination": ("桥式配位", None),
    "monodentate_coordination": ("单齿配位", None),
    "centrosymmetric": ("中心对称", "IR_TERM_109"),
    "centrosymmetric_inactive": ("中心对称红外非活性", "IR_TERM_109"),
    "centrosymmetric_raman_active": ("中心对称拉曼活性", "IR_TERM_109"),
    "vibrational_coupling": ("振动耦合", "IR_TERM_091"),
    "vibrational_coupling_gem_dimethyl": ("借二甲基耦合分裂", "IR_TERM_091"),
    # ── State effects ──
    "Z-conformation_packing": ("Z字构型有序堆积", None),
    "hydrogen_bonding_steric_hindrance": ("氢键空间位阻效应", "IR_TERM_114"),
    "hydrogen_bonding_weak": ("弱氢键作用", "IR_TERM_114"),
    "crystalline_packing": ("晶体堆积效应", "IR_TERM_025"),
    "crystalline_progression": ("结晶态等间距系列峰", "IR_TERM_025"),
}