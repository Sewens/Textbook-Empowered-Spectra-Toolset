import json

from app.services.catalog_service import CatalogService


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _packet():
    return {
        "packet_id": "PKT_DEMO", "packet_status": "accepted", "schema_version": "ir-extraction-packet-2.0.1",
        "source": {"source_id": "SRC_TEXTBOOK", "source_type": "textbook", "title": "Demo spectroscopy"},
        "extraction_meta": {"run_id": "RUN_DEMO", "created_at": "2026-07-15T00:00:00+00:00"},
        "evidence_spans": [{"evidence_id": "EV_DEMO", "evidence_type": "paragraph", "text_original": "A carbonyl band shifts with conjugation.", "locator": {"content_list_index": 3}, "review_status": "accepted"}],
        "concepts": [{"concept_id": "CON_CARBONYL", "concept_type": "functional_group", "names": {"zh": "羰基", "en": "carbonyl"}, "definition": "C=O group", "status": "active"}],
        "materials": [{"material_id": "MAT_ACETONE", "material_type": "compound", "canonical_name": "acetone", "formula": "C3H6O", "external_ids": {"CAS": "67-64-1"}, "review_status": "accepted"}],
        "material_states": [], "group_occurrences": [{"occurrence_id": "OCC_ACETONE_CARBONYL", "material_id": "MAT_ACETONE", "group_concept_id": "CON_CARBONYL", "occurrence_index": 1}],
        "spectra": [{"spectrum_id": "SPEC_TEXTBOOK", "material_id": "MAT_ACETONE", "modality": "IR", "technique": "transmission", "axis": {"x_min": 400, "x_max": 4000}, "review_status": "accepted"}],
        "spectral_features": [{"feature_id": "FEAT_CARBONYL", "spectrum_id": "SPEC_TEXTBOOK", "feature_type": "band", "value_lower": 1705, "value_upper": 1725, "unit": "cm-1", "raw_text": "1715 cm-1", "review_status": "accepted"}],
        "assignments": [{"assignment_id": "ASN_CARBONYL", "feature_id": "FEAT_CARBONYL", "target_concept_id": "CON_CARBONYL", "assignment_role": "primary", "review_status": "accepted"}],
        "reference_bands": [], "diagnostic_patterns": [],
        "claims": [{"claim_id": "CLM_DEMO", "subject_entity_id": "CON_CARBONYL", "predicate": "affected_by", "object_value_json": {"effect": "conjugation"}, "assertion_status": "asserted", "review_status": "accepted", "primary_evidence_id": "EV_DEMO"}],
        "assets": [], "unresolved_items": [],
    }


def _nist_record():
    return {
        "record_id": "NISTIR_DEMO", "record_status": "jcamp_parsed",
        "source": {"source_id": "SRC_NIST", "source_type": "nist_webbook", "title": "NIST", "license_status": "nist_srd_restricted"},
        "material": {"material_id": "MAT_NIST_ACETONE", "name": "Acetone", "formula": "C3H6O", "identifiers": [{"scheme": "CAS", "value": "67-64-1"}]},
        "spectrum": {"spectrum_id": "SPEC_NIST", "modality": "IR", "technique": "IR", "sample_context": {"state": "gas"}, "axis": {"x_min": 450, "x_max": 4000}, "npoints": 100, "assets": [], "review_status": "needs_review"},
        "qa": {"parser_qa_passed": True, "license_qa": "needs_review"},
    }


def test_catalog_imports_accepted_textbook_and_staging_nist_records(tmp_path):
    release = tmp_path / "release"
    _write_json(release / "DATA_INVENTORY.json", {"release_id": "demo-v2", "schema_release": "ir-kg-v2.0.2", "textbooks": {"accepted_packets": 1}, "nist": {"metadata_records": 1}})
    _write_json(release / "textbooks" / "accepted_packets" / "PKT_DEMO.json", _packet())
    nist_path = release / "nist" / "metadata_inventory" / "nist_ir_metadata_inventory.jsonl"
    nist_path.parent.mkdir(parents=True)
    nist_path.write_text(json.dumps(_nist_record()) + chr(10), encoding="utf-8")
    catalog = CatalogService(release, tmp_path / "catalog.sqlite")
    overview = catalog.overview()
    assert overview["release_id"] == "demo-v2"
    assert overview["counts"]["concepts"] == 1
    assert overview["counts"]["materials"] == 2
    assert overview["counts"]["spectra"] == 2
    assert overview["counts"]["claims"] == 1
    assert overview["data_partitions"]["quarantine_included"] is False
    assert catalog.list_entities("concept")[0]["name"] == "羰基"
    assert catalog.list_entities("material", "acetone")[0]["entity_id"] == "MAT_ACETONE"
    assert catalog.list_spectra(source_scope="nist")[0]["spectrum_id"] == "SPEC_NIST"
    assert catalog.list_evidence()[0]["text"] == "A carbonyl band shifts with conjugation."
    graph = catalog.graph()
    assert {node["type"] for node in graph["nodes"]} >= {"concept", "material", "spectrum", "feature", "claim"}
    assert any(edge["label"] == "assigned_to" for edge in graph["edges"])
