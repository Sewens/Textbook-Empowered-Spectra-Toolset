#!/usr/bin/env python3
"""Build a precision material catalog from the source-preserving clean textbook pass."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "0714谱构效数据" / "material_spectra_clean"
OUTPUT = ROOT / "0714谱构效数据" / "material_spectra_accepted"
QUARANTINE = ROOT / "0714谱构效数据" / "material_spectra_quarantine"
RUN_ID = "RUN_precision-materials-20260716-v2"

GENERIC = {
    "gas", "gases", "liquid", "liquids", "solid", "solids", "sample", "samples", "material", "materials",
    "condensed-phase samples", "diameter", "modulation spectrometry", "modulation measurements",
    "food and drug administration", "compound", "compounds", "molecule", "molecules", "carboxylic acid",
    "n-oxide", "mono-n-oxide", "trioxide", "pentaoxide", "hydroperoxide", "p-toluene", "dibenzene",
    "thioalkane", "thioalkene", "chloroalkane", "nitroalkane", "non-alkane", "some alkane", "sec-alcohol",
    "tetrafluoride", "monochloride", "sulphoxide", "selenoxide", "thioacid", "altogether",
}
BAD = re.compile(r"(?i)(?:^s\s*\d+|\btext\b|\b(?:spectrometr|spectroscop|interferometer|detector|resolution|wavenumber|technique|measurement)\b|\b(?:is|are|with|that|which|cannot|usually|many|types|found|combination)\b)")
OCR_FORMULA = re.compile(r"^(?:AsSi|PSi|SSi|USi|BAs|FCl|CIMn|CIRe|CITc|FMn|FRe|FTc|SMo|UAs|NAr)", re.I)
FORMULA = re.compile(r"^(?:[A-Z][a-z]?\d*)+$")
CHEMICAL = re.compile(r"(?i)(benz|xylene|toluene|phenol|aniline|acetone|methanol|ethanol|propanol|butanol|aldehyde|ketone|acid|ester|ether|amine|amide|nitrile|acetate|chloride|bromide|fluoride|sulfate|phosphate|silicate|oxide|hydroxide|carbonate|nitrate|poly|cellulose|glucose|fructose|sucrose|nylon|kapton|water|ammonia|chloroform|mineral|quartz|calcite|mica|olivine|feldspar|kaolinite|montmorillonite|zeolite|alumina|silica)")
CHINESE = re.compile(r"[\u4e00-\u9fff].*(?:酸|醇|酚|醛|酮|胺|酰胺|酯|醚|苯|烷|烯|炔|腈|硝基|聚|矿|盐|氧化|硫酸|磷酸|硅酸)")
CHINESE_FRAGMENT = re.compile(r"^(?:用|使|包括|而|且|等|后|或|如|以|当|从|因|对于|但|由于|最后|根据|主要|不能|这种|它们|我们|通常|也|毫|例如|这|同时|报道|层|比|类|产生|此时|发现|吸收带|谱带|基团|原料|温度|氢键|频率|强度|样品|物质|化合物|矿物).*")
CHINESE_PROCESS = re.compile(r"(?:冲洗|清除|测定|说明|鉴定|应用|取代后|强度|频率|温度|样品|谱带|吸收带|基团|类型|来源|原料|氢键|区间|方法|技术|依次用|可以制成|有助于|溶于|图谱主要|测量了|通常不需要|大多数|主要显示|提出了|迫使|估计|反映了|含有|属于|形成|表示)")
CHINESE_GRAMMAR = re.compile(r"[的及和或而且以用将在于从比为是有无可能会了中上下前后内外每些各这那它其本某大小高低长短多少]")
CHINESE_CATEGORY = re.compile(r"^(?:同|直|脂肪|芳香|卤代|改性|纯|气体|液态|固态|金属|各种|两种|一二|型|属于|即|只有|号|还|故|则|对一|对液态|对金属|有苯|后面|区间|多层|这种|主要|本族|种矿物|系列矿物|共生|无乙醇|白丙烯酸|明显|迫使|提出|测量|估计|图谱|依次|磨光|喷以|氢化).*")
CHINESE_GENERIC_CLASS = re.compile(r"^(?:伯|仲|叔)(?:胺|酰胺|醇|酚)$|^(?:一|二|三|四|五|六)?(?:氯代|溴代|氟代)?(?:烷|烯|炔|苯|醇|酚|醚|酯|酸|胺|酰胺)$|(?:取代苯|烷基|芳基|脂肪酸|羧酸|磺酸|碳酸|硅酸|磷酸|族矿物|系列矿物|矿物)$|^(?:对位|邻位|间位|单核|单取代|二取代|三取代|共轭|芳香|芳族|脂肪|脂肪族|开链|环状|游离|气态|晶态|无水|高密度|低密度|线型|不同浓度|带|含).*")


def rejection_reason(name: str, evidence: list[str]) -> str | None:
    value = name.strip()
    lower = value.casefold()
    if not value or lower in GENERIC:
        return "generic_category_or_class"
    if BAD.search(value):
        return "sentence_method_or_ocr_fragment"
    if OCR_FORMULA.match(value):
        return "ocr_formula_sequence"
    if re.search(r"[\u4e00-\u9fff]", value) and (CHINESE_FRAGMENT.match(value) or CHINESE_PROCESS.search(value) or CHINESE_CATEGORY.match(value)):
        return "chinese_sentence_or_process_fragment"
    if re.search(r"[\u4e00-\u9fff]", value) and CHINESE_GENERIC_CLASS.search(value):
        return "generic_chemical_class_not_specific_material"
    if re.search(r"[\u4e00-\u9fff]", value) and CHINESE_GRAMMAR.search(value):
        return "chinese_grammar_fragment"
    if FORMULA.fullmatch(value):
        if len(value) > 18 or max((int(x) for x in re.findall(r"\d+", value)), default=1) > 12:
            return "unvalidated_formula"
    elif not CHEMICAL.search(value) and not CHINESE.search(value):
        return "unvalidated_material_name"
    if not any(value.casefold() in text.casefold() for text in evidence if text):
        return "no_direct_name_evidence"
    return None


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    QUARANTINE.mkdir(parents=True, exist_ok=True)
    material_catalog: dict[str, list[dict]] = defaultdict(list)
    group_catalog: dict[str, list[dict]] = defaultdict(list)
    spectrum_catalog: dict[str, list[dict]] = defaultdict(list)
    quarantined: list[dict] = []
    books: list[dict] = []

    for book_dir in sorted(p for p in INPUT.iterdir() if p.is_dir()):
        source = read_json(book_dir / "material_spectra.json")
        evidence = {item["evidence_id"]: item for item in source.get("evidence_spans", [])}
        accepted_materials = []
        accepted_ids = set()
        for item in source.get("material_candidates", []):
            evidence_items = [evidence[eid] for eid in item.get("evidence_ids", []) if eid in evidence]
            texts = [entry.get("text_original", "") for entry in evidence_items]
            name = item.get("canonical_name_candidate", "")
            reason = rejection_reason(name, texts)
            if not reason and not any(entry.get("evidence_type") in {"image", "chart", "table", "figure"} and name.casefold() in entry.get("text_original", "").casefold() for entry in evidence_items):
                reason = "no_direct_figure_or_table_evidence"
            if reason:
                quarantined.append({"book": book_dir.name, "candidate_id": item.get("material_candidate_id"), "name": item.get("canonical_name_candidate"), "reason": reason, "evidence_ids": item.get("evidence_ids", [])})
                continue
            item = dict(item)
            item["promotion_status"] = "accepted_precision_candidate"
            accepted_materials.append(item)
            accepted_ids.add(item["material_candidate_id"])

        accepted_spectra = []
        for item in source.get("spectrum_candidates", []):
            material_ids = sorted(set(item.get("material_candidate_ids", [])) & accepted_ids)
            if not material_ids:
                continue
            item = dict(item)
            item["material_candidate_ids"] = material_ids
            item["promotion_status"] = "accepted_precision_candidate"
            accepted_spectra.append(item)
        accepted_spectrum_ids = {item["spectrum_candidate_id"] for item in accepted_spectra}
        group_ids = {gid for item in accepted_materials for gid in item.get("group_candidate_ids", [])}
        group_ids |= {gid for item in accepted_spectra for gid in item.get("group_candidate_ids", [])}
        accepted_groups = [dict(item) for item in source.get("group_candidates", []) if item.get("group_candidate_id") in group_ids]
        feature_ids = {fid for item in accepted_spectra for fid in item.get("feature_candidate_ids", [])}
        image_ids = {iid for item in accepted_spectra for iid in item.get("image_candidate_ids", [])}
        evidence_ids = {eid for item in accepted_materials for eid in item.get("evidence_ids", [])}
        evidence_ids |= {eid for item in accepted_spectra for eid in item.get("evidence_ids", [])}
        payload = source | {
            "run_id": RUN_ID,
            "scope": source.get("scope", {}) | {"unit_type": "precision_accepted_materials"},
            "group_candidates": accepted_groups,
            "material_candidates": accepted_materials,
            "spectrum_candidates": accepted_spectra,
            "feature_candidates": [item for item in source.get("feature_candidates", []) if item.get("feature_candidate_id") in feature_ids],
            "image_candidates": [item for item in source.get("image_candidates", []) if item.get("image_candidate_id") in image_ids],
            "evidence_spans": [item for item in source.get("evidence_spans", []) if item.get("evidence_id") in evidence_ids],
            "quality": {"status": "accepted_precision_candidate", "direct_name_evidence_required": True, "accepted_material_count": len(accepted_materials)},
        }
        write_json(OUTPUT / book_dir.name / "material_spectra.json", payload)
        for item in accepted_materials:
            material_catalog[item["material_candidate_id"]].append({"book": book_dir.name, "source_id": payload["source"]["source_id"], "record": item})
        for item in accepted_groups:
            group_catalog[item["group_candidate_id"]].append({"book": book_dir.name, "source_id": payload["source"]["source_id"], "record": item})
        for item in accepted_spectra:
            spectrum_catalog[item["spectrum_candidate_id"]].append({"book": book_dir.name, "source_id": payload["source"]["source_id"], "record": item})
        books.append({"book": book_dir.name, "materials": len(accepted_materials), "spectra": len(accepted_spectra), "groups": len(accepted_groups), "evidence": len(payload["evidence_spans"])})

    def catalog(key: str, records: dict[str, list[dict]]) -> list[dict]:
        return [{key: identifier, "source_records": sources} for identifier, sources in sorted(records.items())]
    materials = catalog("material_candidate_id", material_catalog)
    groups = catalog("group_candidate_id", group_catalog)
    spectra = catalog("spectrum_candidate_id", spectrum_catalog)
    write_json(OUTPUT / "_compound_catalog.json", {"run_id": RUN_ID, "unique_candidates": len(materials), "materials": materials})
    write_json(OUTPUT / "_group_catalog.json", {"run_id": RUN_ID, "unique_candidates": len(groups), "groups": groups})
    write_json(OUTPUT / "_spectrum_catalog.json", {"run_id": RUN_ID, "unique_candidates": len(spectra), "spectra": spectra})
    summary = {"run_id": RUN_ID, "book_count": len(books), "books": books, "unique_catalogs": {"materials": len(materials), "groups": len(groups), "spectra": len(spectra)}, "totals": {"materials": sum(item["materials"] for item in books), "spectra": sum(item["spectra"] for item in books), "evidence": sum(item["evidence"] for item in books), "quarantined_material_candidates": len(quarantined)}, "policy": {"mode": "precision_accepted_materials", "direct_name_evidence_required": True, "broad_catalog_retained_for_audit": True}}
    write_json(OUTPUT / "_all_books_summary.json", summary)
    write_json(QUARANTINE / "rejected_material_candidates.json", {"run_id": RUN_ID, "records": quarantined})
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == "__main__":
    main()
