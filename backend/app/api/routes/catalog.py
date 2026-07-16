from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.security import CurrentUser, require_permission
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
    def evidence(q: str | None = Query(default=None), strength: str | None = Query(default=None, pattern="^(high|medium|low)?$"), limit: int = Query(default=300, le=2000)) -> dict:
        items = service.list_evidence(q, limit, strength)
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

    @router.get("/material-relationship-graph")
    def material_relationship_graph() -> dict:
        return service.material_relationship_graph()

    @router.get("/textbook-inventory/overview")
    def textbook_inventory_overview() -> dict:
        return service.textbook_inventory_overview()

    @router.get("/textbook-inventory/books")
    def textbook_inventory_books() -> dict:
        books = service.textbook_inventory_books()
        return {"total": len(books), "items": books}

    @router.get("/textbook-inventory/details/{kind}/{candidate_id}")
    def textbook_inventory_unified_detail(
        kind: str,
        candidate_id: str,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=12, ge=1, le=50),
        threshold: int = Query(default=12, ge=1, le=200),
    ) -> dict:
        if kind not in {"materials", "spectra"}:
            raise HTTPException(status_code=404, detail="Inventory detail kind not found")
        item = service.textbook_inventory_unified_detail(kind, candidate_id, offset=offset, limit=limit, threshold=threshold)
        if item is None:
            raise HTTPException(status_code=404, detail="Inventory candidate not found")
        return item

    @router.get("/textbook-inventory/assets/{book}/{asset_path:path}")
    def textbook_inventory_asset(book: str, asset_path: str, _user: CurrentUser = Depends(require_permission("evidence:read"))):
        path = service.textbook_inventory_asset(book, asset_path)
        if path is None:
            raise HTTPException(status_code=404, detail="Inventory asset not found")
        return FileResponse(path)

    @router.get("/textbook-inventory/{kind}")
    def textbook_inventory_list(kind: str, q: str | None = Query(default=None), book: str | None = Query(default=None), limit: int = Query(default=100, le=500)) -> dict:
        if kind not in {"groups", "materials", "spectra"}:
            raise HTTPException(status_code=404, detail="Inventory kind not found")
        items = service.textbook_inventory_list(kind, q, book, limit)
        return {"total": len(items), "items": items}

    @router.get("/textbook-inventory/{kind}/{candidate_id}")
    def textbook_inventory_detail(kind: str, candidate_id: str) -> dict:
        if kind not in {"groups", "materials", "spectra"}:
            raise HTTPException(status_code=404, detail="Inventory kind not found")
        item = service.textbook_inventory_detail(kind, candidate_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Inventory candidate not found")
        return item

    return router
