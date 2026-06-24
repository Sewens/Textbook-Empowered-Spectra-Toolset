from app.services.graph_service import GraphService


class GraphRepository:
    """Prototype repository backed by release JSON files.

    The class exists so the API boundary can later move from JSON files to
    PostgreSQL/SQLite tables without changing route handlers.
    """

    def __init__(self, service: GraphService | None = None) -> None:
        self.service = service or GraphService()
