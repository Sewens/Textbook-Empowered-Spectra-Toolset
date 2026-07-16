import json

from app.services.textbook_inventory_service import TextbookInventoryService


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_material_relationship_graph_derives_only_high_confidence_structural_edges(tmp_path):
    inventory = tmp_path / "inventory"
    _write_json(inventory / "_all_books_summary.json", {"run_id": "graph-test", "book_count": 1, "totals": {}, "unique_catalogs": {}, "books": [{"book": "教材甲"}]})
    _write_json(inventory / "_group_catalog.json", {"groups": []})
    _write_json(inventory / "_spectrum_catalog.json", {"spectra": []})
    _write_json(inventory / "_compound_catalog.json", {"materials": [
        {"material_candidate_id": "MAT_METHANOL", "source_records": [{"book": "教材甲", "record": {"canonical_name_candidate": "methanol", "group_candidate_ids": ["FG_CARBONYL"]}}]},
        {"material_candidate_id": "MAT_ETHANOL", "source_records": [{"book": "教材甲", "record": {"canonical_name_candidate": "ethanol"}}]},
        {"material_candidate_id": "MAT_UNKNOWN", "source_records": [{"book": "教材甲", "record": {"canonical_name_candidate": "实验样品甲"}}]},
    ]})

    service = TextbookInventoryService(inventory)
    graph = service.material_relationship_graph()
    repeated_graph = service.material_relationship_graph()
    assert graph["layout_key"] == repeated_graph["layout_key"]
    assert len(graph["layout_key"]) == 16
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = graph["edges"]

    assert nodes["FG_METHYL"]["type"] == "functional_group"
    assert nodes["FG_HYDROXYL"]["label"] == "羟基"
    methanol_parents = {edge["source"] for edge in edges if edge["target"] == "MAT_METHANOL" and edge["relation_type"] == "has_functional_group"}
    assert methanol_parents == {"FG_METHYL", "FG_HYDROXYL"}
    assert not any(edge["source"] == "FG_CARBONYL" and edge["target"] == "MAT_METHANOL" for edge in edges)
    shared = next(edge for edge in edges if edge["relation_type"] == "shares_functional_groups")
    assert {shared["source"], shared["target"]} == {"MAT_METHANOL", "MAT_ETHANOL"}
    assert set(shared["shared_group_ids"]) == {"FG_METHYL", "FG_HYDROXYL"}
    assert nodes["MAT_UNKNOWN"]["relationship_status"] == "needs_structure_confirmation"
    assert not any(edge["target"] == "MAT_UNKNOWN" and edge["relation_type"] == "has_functional_group" for edge in edges)
