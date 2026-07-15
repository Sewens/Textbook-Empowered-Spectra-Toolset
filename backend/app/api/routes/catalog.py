from fastapi import APIRouter, HTTPException, Query

from app.services.catalog_service import CatalogService


def build_router(service: CatalogService) -> APIRouter:
    router = APIRouter(prefix="/catalog", tags=["catalog-v2"])

    @router.get("/overview")
    def overview() -> dict:
        return service.overview()

    @router.get("/concepts")
    def concepts(q: str | None = Query(default=None), limit: int = Query(default=100, le=500)) -> dict:
        items = service.list_entities("concept", q, limit)
        return {"total": len(items), "items": items}

    @router.get("/materials")
    def materials(q: str | None = Query(default=None), limit: int = Query(default=100, le=500)) -> dict:
        items = service.list_entities("material", q, limit)
        return {"total": len(items), "items": items}

    @router.get("/spectra")
    def spectra(source_scope: str | None = Query(default=None, pattern="^(textbook|nist)?$"), q: str | None = Query(default=None), limit: int = Query(default=100, le=500)) -> dict:
        items = service.list_spectra(source_scope, q, limit)
        return {"total": len(items), "items": items}

    @router.get("/evidence")
    def evidence(q: str | None = Query(default=None), limit: int = Query(default=100, le=500)) -> dict:
        items = service.list_evidence(q, limit)
        return {"total": len(items), "items": items}

    @router.get("/claims")
    def claims(q: str | None = Query(default=None), limit: int = Query(default=100, le=500)) -> dict:
        items = service.list_claims(q, limit)
        return {"total": len(items), "items": items}

    @router.get("/entities/{entity_id}")
    def entity(entity_id: str) -> dict:
        item = service.get_entity(entity_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Entity not found")
        return item

    @router.get("/graph")
    def graph(limit: int = Query(default=800, le=5000)) -> dict:
        return service.graph(limit)

    return router
