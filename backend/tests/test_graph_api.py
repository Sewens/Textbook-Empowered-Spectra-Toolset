from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_catalog_overview_exposes_schema_native_release_boundary():
    response = client.get("/api/catalog/overview")
    assert response.status_code == 200
    payload = response.json()
    assert {"release_id", "schema_release", "counts", "data_partitions"} <= payload.keys()
    assert payload["data_partitions"]["quarantine_included"] is False
    assert payload["data_partitions"]["nist_is_staging"] is True


def test_catalog_collections_are_partition_aware_and_paginated():
    for path in ["/api/catalog/concepts", "/api/catalog/materials?limit=2", "/api/catalog/spectra?source_scope=nist&limit=2", "/api/catalog/evidence", "/api/catalog/claims"]:
        response = client.get(path)
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == len(payload["items"])


def test_catalog_graph_contains_only_nodes_referenced_by_returned_edges():
    response = client.get("/api/catalog/graph?limit=200")
    assert response.status_code == 200
    payload = response.json()
    node_ids = {node["id"] for node in payload["nodes"]}
    assert all(edge["source"] in node_ids and edge["target"] in node_ids for edge in payload["edges"])
