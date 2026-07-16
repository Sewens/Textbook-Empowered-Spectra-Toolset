from fastapi import APIRouter, HTTPException, Query

from app.services.catalog_service import CatalogService


def build_router(service: CatalogService) -> APIRouter:
    router = APIRouter(prefix="/catalog", tags=["catalog-v2"])

    @router.get("/overview")
    def overview() -> dict:
        return service.overview()

    @router.get("/terms")
    def terms(q: str | None = Query(default=None), limit: int = Query(default=300, le=1000)) -> dict:
        items = service.list_terms(q, limit)
        return {"total": len(items), "items": items}

    @router.get("/terms/{term_id}", name="catalog_term_detail")
    def catalog_term_detail(term_id: str) -> dict:
        item = service.get_term(term_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Term not found")
        return item

    @router.get("/groups/{group_id}")
    def group(group_id: str) -> dict:
        item = service.group_detail(group_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Group not found")
        return item

    @router.get("/reference-materials")
    def reference_materials(q: str | None = Query(default=None), limit: int = Query(default=300, le=1000)) -> dict:
        items = service.list_reference_materials(q, limit)
        return {"total": len(items), "items": items}

    @router.get("/materials/{material_id}")
    def material(material_id: str) -> dict:
        item = service.material_detail(material_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Material not found")
        return item

    @router.get("/hierarchy")
    def hierarchy(limit: int = Query(default=1200, le=5000)) -> dict:
        return service.hierarchy(limit)

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
