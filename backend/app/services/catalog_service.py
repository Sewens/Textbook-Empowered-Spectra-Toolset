import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from app.services.terminology_service import TerminologyCatalogService


class CatalogService:
    def __init__(self, release_path: Path, database_path: Path, legacy_reference_path: Path | None = None, terminology_path: Path | None = None) -> None:
        self.release_path = Path(release_path)
        self.legacy_reference_path = Path(legacy_reference_path) if legacy_reference_path else None
        self.database_path = Path(database_path)
        self.terminology = TerminologyCatalogService(terminology_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_index()

    def overview(self) -> dict[str, Any]:
        inventory = self._read_json(self.release_path / "DATA_INVENTORY.json", {})
        counts = {label: self._count(kind) for label, kind in {"concepts": "concept", "materials": "material", "spectra": "spectrum", "features": "feature", "claims": "claim", "evidence": "evidence", "sources": "source"}.items()}
        counts.update(self.terminology.overview_counts())
        return {"release_id": inventory.get("release_id", self.release_path.name), "schema_release": inventory.get("schema_release"), "packet_schema": inventory.get("packet_schema"), "release_status": inventory.get("release_status"), "counts": counts, "data_partitions": {"accepted_textbook_packets": inventory.get("textbooks", {}).get("accepted_packets", 0), "nist_metadata_records": inventory.get("nist", {}).get("metadata_records", 0), "terminology_catalog": self.terminology.available, "quarantine_included": False, "nist_is_staging": True}}

    def list_entities(self, entity_type: str, query: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        sql, values = "SELECT * FROM entity WHERE entity_type = ?", [entity_type]
        if query:
            sql += " AND (lower(name) LIKE ? OR lower(entity_id) LIKE ? OR lower(payload_json) LIKE ?)"
            token = f"%{query.lower()}%"
            values.extend([token, token, token])
        sql += " ORDER BY name COLLATE NOCASE, entity_id LIMIT ?"
        values.append(limit)
        with self._connect() as con:
            return [self._entity(row) for row in con.execute(sql, values)]

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute("SELECT * FROM entity WHERE entity_id = ?", (entity_id,)).fetchone()
        return self._entity(row) if row else None

    def list_spectra(self, source_scope: str | None = None, query: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        sql, values = "SELECT * FROM spectrum WHERE 1 = 1", []
        if source_scope:
            sql += " AND source_scope = ?"
            values.append(source_scope)
        if query:
            sql += " AND (lower(spectrum_id) LIKE ? OR lower(material_id) LIKE ? OR lower(payload_json) LIKE ?)"
            token = f"%{query.lower()}%"
            values.extend([token, token, token])
        sql += " ORDER BY source_scope, spectrum_id LIMIT ?"
        values.append(limit)
        with self._connect() as con:
            return [self._spectrum(row) for row in con.execute(sql, values)]

    def list_evidence(self, query: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        sql, values = "SELECT * FROM evidence", []
        if query:
            sql += " WHERE lower(text) LIKE ? OR lower(evidence_id) LIKE ?"
            token = f"%{query.lower()}%"
            values.extend([token, token])
        sql += " ORDER BY evidence_id LIMIT ?"
        values.append(limit)
        with self._connect() as con:
            return [{"evidence_id": row["evidence_id"], "source_id": row["source_id"], "evidence_type": row["evidence_type"], "text": row["text"], "source_scope": row["source_scope"], "review_status": row["review_status"], "payload": json.loads(row["payload_json"])} for row in con.execute(sql, values)]

    def list_claims(self, query: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.list_entities("claim", query, limit)

    def graph(self, limit: int = 800) -> dict[str, list[dict[str, Any]]]:
        with self._connect() as con:
            edges = [dict(row) for row in con.execute("SELECT * FROM relation ORDER BY source_scope, predicate, relation_id LIMIT ?", (limit * 3,))]
            node_ids: set[str] = set()
            selected_edges: list[dict[str, Any]] = []
            for edge in edges:
                expanded = node_ids | {edge["source_id"], edge["target_id"]}
                if len(expanded) > limit:
                    continue
                node_ids = expanded
                selected_edges.append(edge)
            if not node_ids:
                records = []
            else:
                placeholders = ",".join("?" for _ in node_ids)
                records = [self._entity(row) for row in con.execute("SELECT * FROM entity WHERE entity_id IN (" + placeholders + ")", tuple(node_ids))]
        return {"nodes": [{"id": item["entity_id"], "label": item["name"], "type": item["entity_type"], "data": item} for item in records], "edges": [{"id": item["relation_id"], "source": item["source_id"], "target": item["target_id"], "label": item["predicate"], "data": json.loads(item["payload_json"])} for item in selected_edges]}

    def _ensure_index(self) -> None:
        fingerprint = self._fingerprint()
        with self._connect() as con:
            self._create_schema(con)
            current = con.execute("SELECT value FROM metadata WHERE key = ?", ("fingerprint",)).fetchone()
            if current and current["value"] == fingerprint:
                return
            for table in ["entity", "spectrum", "evidence", "relation", "metadata"]:
                con.execute(f"DELETE FROM {table}")
            for path in sorted((self.release_path / "textbooks" / "accepted_packets").glob("*.json")):
                self._import_packet(con, self._read_json(path, {}))
            for record in self._read_jsonl(self.release_path / "nist" / "metadata_inventory" / "nist_ir_metadata_inventory.jsonl"):
                self._import_nist(con, record)
            self._import_legacy_reference(con)
            con.execute("INSERT INTO metadata VALUES (?, ?)", ("fingerprint", fingerprint))
            con.commit()

    def _import_packet(self, con: sqlite3.Connection, packet: dict[str, Any]) -> None:
        source, scope = packet.get("source", {}), "textbook"
        source_id = source.get("source_id", packet.get("packet_id", "SRC_UNKNOWN"))
        self._put_entity(con, source_id, "source", source.get("title", source_id), scope, "accepted", source)
        for evidence in packet.get("evidence_spans", []):
            entity_id = evidence["evidence_id"]
            status = evidence.get("review_status", "accepted")
            self._put_entity(con, entity_id, "evidence", evidence.get("text_original") or entity_id, scope, status, evidence)
            con.execute("INSERT OR REPLACE INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?)", (entity_id, source_id, evidence.get("evidence_type"), evidence.get("text_original"), scope, status, self._dump(evidence)))
            self._rel(con, source_id, entity_id, "has_evidence", scope, {})
        for concept in packet.get("concepts", []):
            names = concept.get("names", {})
            self._put_entity(con, concept["concept_id"], "concept", names.get("zh") or names.get("en") or concept["concept_id"], scope, concept.get("status", "accepted"), concept)
            self._rel(con, source_id, concept["concept_id"], "defines", scope, {})
        for material in packet.get("materials", []):
            self._put_entity(con, material["material_id"], "material", material.get("canonical_name") or material["material_id"], scope, material.get("review_status", "accepted"), material)
            self._rel(con, source_id, material["material_id"], "mentions", scope, {})
        for occurrence in packet.get("group_occurrences", []):
            self._rel(con, occurrence.get("material_id"), occurrence.get("group_concept_id"), "has_group", scope, occurrence)
        for spectrum in packet.get("spectra", []):
            entity_id, status = spectrum["spectrum_id"], spectrum.get("review_status", "accepted")
            self._put_entity(con, entity_id, "spectrum", entity_id, scope, status, spectrum)
            con.execute("INSERT OR REPLACE INTO spectrum VALUES (?, ?, ?, ?, ?, ?, ?)", (entity_id, spectrum.get("material_id"), spectrum.get("modality"), spectrum.get("technique"), scope, status, self._dump(spectrum)))
            self._rel(con, spectrum.get("material_id"), entity_id, "has_spectrum", scope, {})
        for feature in packet.get("spectral_features", []):
            entity_id = feature["feature_id"]
            self._put_entity(con, entity_id, "feature", feature.get("raw_text") or entity_id, scope, feature.get("review_status", "accepted"), feature)
            self._rel(con, feature.get("spectrum_id"), entity_id, "has_feature", scope, {})
        for assignment in packet.get("assignments", []):
            self._rel(con, assignment.get("feature_id"), assignment.get("target_concept_id"), "assigned_to", scope, assignment)
        for claim in packet.get("claims", []):
            entity_id = claim["claim_id"]
            self._put_entity(con, entity_id, "claim", claim.get("predicate", entity_id), scope, claim.get("review_status", "accepted"), claim)
            self._rel(con, entity_id, claim.get("subject_entity_id"), "asserts_about", scope, claim)
            self._rel(con, entity_id, claim.get("object_entity_id"), claim.get("predicate", "related_to"), scope, claim)
            self._rel(con, entity_id, claim.get("primary_evidence_id"), "supported_by", scope, {})

    def _import_nist(self, con: sqlite3.Connection, record: dict[str, Any]) -> None:
        source, material, spectrum, scope = record.get("source", {}), record.get("material", {}), record.get("spectrum", {}), "nist"
        source_id = source.get("source_id", "SRC_NIST")
        self._put_entity(con, source_id, "source", source.get("title", source_id), scope, source.get("license_status", "needs_review"), source)
        material_id = material.get("material_id")
        if material_id:
            self._put_entity(con, material_id, "material", material.get("name", material_id), scope, record.get("record_status", "metadata_inventory"), material)
            self._rel(con, source_id, material_id, "catalogs", scope, {"record_id": record.get("record_id")})
        spectrum_id = spectrum.get("spectrum_id")
        if spectrum_id:
            status = spectrum.get("review_status", record.get("record_status", "metadata_inventory"))
            self._put_entity(con, spectrum_id, "spectrum", spectrum_id, scope, status, spectrum)
            con.execute("INSERT OR REPLACE INTO spectrum VALUES (?, ?, ?, ?, ?, ?, ?)", (spectrum_id, material_id, spectrum.get("modality"), spectrum.get("technique"), scope, status, self._dump(record)))
            self._rel(con, material_id, spectrum_id, "has_spectrum", scope, {"record_id": record.get("record_id")})

    def _put_entity(self, con: sqlite3.Connection, entity_id: str | None, entity_type: str, name: str, scope: str, status: str, payload: dict[str, Any]) -> None:
        if entity_id:
            con.execute("INSERT OR REPLACE INTO entity VALUES (?, ?, ?, ?, ?, ?)", (entity_id, entity_type, name, scope, status, self._dump(payload)))

    def _rel(self, con: sqlite3.Connection, source_id: str | None, target_id: str | None, predicate: str, scope: str, payload: dict[str, Any]) -> None:
        if source_id and target_id:
            relation_id = hashlib.sha1(f"{source_id}|{predicate}|{target_id}".encode()).hexdigest()
            con.execute("INSERT OR REPLACE INTO relation VALUES (?, ?, ?, ?, ?, ?)", (relation_id, source_id, target_id, predicate, scope, self._dump(payload)))

    def _create_schema(self, con: sqlite3.Connection) -> None:
        con.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        con.execute("CREATE TABLE IF NOT EXISTS entity (entity_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL, name TEXT NOT NULL, source_scope TEXT NOT NULL, review_status TEXT NOT NULL, payload_json TEXT NOT NULL)")
        con.execute("CREATE TABLE IF NOT EXISTS spectrum (spectrum_id TEXT PRIMARY KEY, material_id TEXT, modality TEXT, technique TEXT, source_scope TEXT NOT NULL, review_status TEXT NOT NULL, payload_json TEXT NOT NULL)")
        con.execute("CREATE TABLE IF NOT EXISTS evidence (evidence_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, evidence_type TEXT, text TEXT, source_scope TEXT NOT NULL, review_status TEXT NOT NULL, payload_json TEXT NOT NULL)")
        con.execute("CREATE TABLE IF NOT EXISTS relation (relation_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, target_id TEXT NOT NULL, predicate TEXT NOT NULL, source_scope TEXT NOT NULL, payload_json TEXT NOT NULL)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_entity_type_name ON entity(entity_type, name)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_spectrum_scope ON spectrum(source_scope, spectrum_id)")

    def _count(self, entity_type: str) -> int:
        with self._connect() as con:
            return int(con.execute("SELECT count(*) FROM entity WHERE entity_type = ?", (entity_type,)).fetchone()[0])

    def _fingerprint(self) -> str:
        digest = hashlib.sha256()
        paths = [self.release_path / "DATA_INVENTORY.json", self.release_path / "nist" / "metadata_inventory" / "nist_ir_metadata_inventory.jsonl"] + sorted((self.release_path / "textbooks" / "accepted_packets").glob("*.json"))
        if self.legacy_reference_path and self.legacy_reference_path.exists():
            paths.extend(sorted(self.legacy_reference_path.glob("FG_*.json")))
        for path in paths:
            if path.exists():
                stat = path.stat()
                digest.update(f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}".encode())
        return digest.hexdigest()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.database_path)
        con.row_factory = sqlite3.Row
        return con

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _entity(row: sqlite3.Row) -> dict[str, Any]:
        return {"entity_id": row["entity_id"], "entity_type": row["entity_type"], "name": row["name"], "source_scope": row["source_scope"], "review_status": row["review_status"], "payload": json.loads(row["payload_json"])}

    @staticmethod
    def _spectrum(row: sqlite3.Row) -> dict[str, Any]:
        payload = json.loads(row["payload_json"])
        return {"spectrum_id": row["spectrum_id"], "material_id": row["material_id"], "modality": row["modality"], "technique": row["technique"], "source_scope": row["source_scope"], "review_status": row["review_status"], "peaks": payload.get("annotated_peaks") or payload.get("peaks") or [], "image_url": payload.get("image_url"), "payload": payload}


    def list_terms(self, query: str | None = None, limit: int = 300) -> list[dict[str, Any]]:
        if self.terminology.available:
            return self.terminology.list_terms(query, limit)
        sql, values = "SELECT * FROM entity WHERE entity_type IN (\"concept\", \"group\")", []
        if query:
            sql += " AND (lower(name) LIKE ? OR lower(entity_id) LIKE ? OR lower(payload_json) LIKE ?)"
            token = f"%{query.lower()}%"
            values.extend([token, token, token])
        sql += " ORDER BY entity_type DESC, name COLLATE NOCASE LIMIT ?"
        values.append(limit)
        with self._connect() as con:
            return [{"term_id": row["entity_id"], "term_type": row["entity_type"], "name": row["name"], "source_scope": row["source_scope"], "payload": json.loads(row["payload_json"])} for row in con.execute(sql, values)]

    def get_term(self, term_id: str) -> dict[str, Any] | None:
        if self.terminology.available:
            return self.terminology.get_term(term_id)
        return self.get_entity(term_id)

    def group_detail(self, group_id: str) -> dict[str, Any] | None:
        group = self.get_entity(group_id)
        if not group or group["entity_type"] != "group":
            return None
        with self._connect() as con:
            material_rows = [dict(row) for row in con.execute("SELECT target_id FROM relation WHERE source_id = ? AND predicate = ?", (group_id, "has_reference_material"))]
            material_ids = [row["target_id"] for row in material_rows]
            materials = [self._entity(row) for row in con.execute("SELECT * FROM entity WHERE entity_id IN (" + ",".join("?" for _ in material_ids) + ")", tuple(material_ids))] if material_ids else []
            spectra = [self._spectrum(row) for row in con.execute("SELECT * FROM spectrum WHERE material_id IN (" + ",".join("?" for _ in material_ids) + ")", tuple(material_ids))] if material_ids else []
        return group | {"materials": materials, "spectra": spectra, "vibrations": group["payload"].get("inherent_vibrations", [])}

    def material_detail(self, material_id: str) -> dict[str, Any] | None:
        material = self.get_entity(material_id)
        if not material or material["entity_type"] != "material":
            return None
        with self._connect() as con:
            groups = [self._entity(row) | {"group_id": row["entity_id"]} for row in con.execute("SELECT e.* FROM relation r JOIN entity e ON e.entity_id = r.source_id WHERE r.target_id = ? AND r.predicate = ?", (material_id, "has_reference_material"))]
            spectra = [self._spectrum(row) for row in con.execute("SELECT * FROM spectrum WHERE material_id = ? ORDER BY spectrum_id", (material_id,))]
        return material | {"groups": groups, "spectra": spectra}

    def hierarchy(self, limit: int = 1200) -> dict[str, list[dict[str, Any]]]:
        with self._connect() as con:
            groups = [self._entity(row) for row in con.execute("SELECT * FROM entity WHERE entity_type = \"group\" ORDER BY name LIMIT ?", (limit,))]
            group_ids = {item["entity_id"] for item in groups}
            relations = [dict(row) for row in con.execute("SELECT * FROM relation WHERE predicate = \"has_reference_material\" ORDER BY source_id LIMIT ?", (limit * 8,))]
            material_ids = {row["target_id"] for row in relations if row["source_id"] in group_ids}
            materials = [self._entity(row) for row in con.execute("SELECT * FROM entity WHERE entity_id IN (" + ",".join("?" for _ in material_ids) + ")", tuple(material_ids))] if material_ids else []
        nodes = [{"id": item["entity_id"], "label": item["name"], "type": item["entity_type"], "data": item} for item in groups + materials]
        return {"nodes": nodes, "edges": [{"id": row["relation_id"], "source": row["source_id"], "target": row["target_id"], "label": row["predicate"], "data": json.loads(row["payload_json"])} for row in relations if row["source_id"] in group_ids and row["target_id"] in material_ids]}

    def _import_legacy_reference(self, con: sqlite3.Connection) -> None:
        if not self.legacy_reference_path or not self.legacy_reference_path.exists():
            return
        scope, source_id = "legacy_reference", "SRC_LEGACY_IR_REFERENCE_V07"
        self._put_entity(con, source_id, "source", "IR Reference Cards v0.7", scope, "reference", {"source_type": "legacy_reference"})
        for path in sorted(self.legacy_reference_path.glob("FG_*.json")):
            group = self._read_json(path, {})
            group_id = group.get("group_id")
            if not group_id:
                continue
            name = group.get("name_zh") or group.get("group", {}).get("canonical_name_zh") or group_id
            self._put_entity(con, group_id, "group", name, scope, "reference", group)
            self._rel(con, source_id, group_id, "defines", scope, {})
            for item in group.get("spectral_gallery", []):
                material_id = item.get("compound_id") or "MAT_LEGACY_" + hashlib.sha1((item.get("smiles") or item.get("compound_name_en") or item.get("compound_name_zh") or item.get("figure_id", "")).encode()).hexdigest()[:16]
                material = {"material_id": material_id, "name_zh": item.get("compound_name_zh"), "name_en": item.get("compound_name_en"), "formula": item.get("molecular_formula"), "smiles": item.get("smiles")}
                self._put_entity(con, material_id, "material", item.get("compound_name_zh") or item.get("compound_name_en") or material_id, scope, "reference", material)
                self._rel(con, group_id, material_id, "has_reference_material", scope, {"group_id": group_id})
                spectrum_id = item.get("spectrum_id") or item.get("figure_id")
                if spectrum_id:
                    payload = item | {"group_id": group_id, "image_url": self._legacy_image_url(item.get("mineru_crop_image_path") or item.get("image_path"))}
                    self._put_entity(con, spectrum_id, "spectrum", spectrum_id, scope, "reference", payload)
                    con.execute("INSERT OR REPLACE INTO spectrum VALUES (?, ?, ?, ?, ?, ?, ?)", (spectrum_id, material_id, "IR", "reference_card", scope, "reference", self._dump(payload)))
                    self._rel(con, material_id, spectrum_id, "has_spectrum", scope, {"group_id": group_id})

    @staticmethod
    def _legacy_image_url(path: str | None) -> str | None:
        if not path:
            return None
        return "/assets/legacy-spectra/" + Path(path).name


    def list_reference_materials(self, query: str | None = None, limit: int = 300) -> list[dict[str, Any]]:
        sql, values = "SELECT * FROM entity WHERE entity_type = \"material\" AND source_scope IN (\"legacy_reference\", \"textbook\")", []
        if query:
            sql += " AND (lower(name) LIKE ? OR lower(entity_id) LIKE ? OR lower(payload_json) LIKE ?)"
            token = f"%{query.lower()}%"
            values.extend([token, token, token])
        sql += " ORDER BY name COLLATE NOCASE LIMIT ?"
        values.append(limit)
        with self._connect() as con:
            return [self._entity(row) for row in con.execute(sql, values)]
