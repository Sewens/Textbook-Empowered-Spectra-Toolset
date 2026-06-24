from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_manifest_exposes_v07_release_stats():
    response = client.get("/api/manifest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "0.7-native-superset"
    assert payload["stats"]["functional_groups"] == 37
    assert payload["stats"]["compound_examples"] == 97
    assert payload["stats"]["peaks"] == 196


def test_groups_endpoint_returns_v07_card_index():
    response = client.get("/api/groups")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 37
    assert len(payload["items"]) == 37
    assert payload["items"][0]["group_id"].startswith("FG_")
    assert payload["items"][0]["evidence_count"] >= 1
    assert payload["items"][0]["source_claim_count"] >= 1


def test_group_detail_contains_v07_entities():
    response = client.get("/api/groups/FG_CARBONYL_KETONE")
    assert response.status_code == 200
    payload = response.json()
    assert payload["group_id"] == "FG_CARBONYL_KETONE"
    assert payload["group"]["canonical_name_zh"] == "酮羰基"
    assert len(payload["evidence_spans"]) >= 1
    assert len(payload["vibration_templates"]) >= 1
    assert len(payload["compound_examples"]) >= 1
    assert len(payload["source_claims"]) >= 1
    first_example = payload["compound_examples"][0]
    assert first_example["compound"]["compound_id"].startswith("CMPD_")
    assert first_example["spectra"][0]["peaks"][0]["assignments"]


def test_wavenumber_search_returns_measured_and_template_evidence():
    response = client.get("/api/wavenumber", params={"value": 1715, "tolerance": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"]["value"] == 1715
    assert payload["total"] >= 1
    assert any(item["match_type"] == "measured_peak" for item in payload["items"])
    assert any(item["group_id"] == "FG_CARBONYL_KETONE" for item in payload["items"])
    assert any(item["compound_id"] == "CMPD_ACETONE" for item in payload["items"])


def test_spectra_endpoint_returns_v07_spectrum_records():
    response = client.get("/api/spectra")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 97
    assert any(item["compound_id"] and item["annotated_peak_count"] >= 1 for item in payload["items"])


def test_compounds_endpoint_deduplicates_compounds():
    response = client.get("/api/compounds")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 46
    acetone = next(item for item in payload["items"] if item["compound_id"] == "CMPD_ACETONE")
    assert "FG_CARBONYL_KETONE" in acetone["group_ids"]
    assert acetone["smiles"] == "CC(=O)C"


def test_graph_contains_group_compound_spectrum_and_vibration_nodes():
    response = client.get("/api/graph")
    assert response.status_code == 200
    payload = response.json()
    node_types = {node["type"] for node in payload["nodes"]}
    assert {"group", "vibration", "compound", "spectrum"} <= node_types
    assert any(edge["label"] == "contains_group" for edge in payload["edges"])
