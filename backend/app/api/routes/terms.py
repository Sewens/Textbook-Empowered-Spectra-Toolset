from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import CurrentUser, require_permission
from app.schemas.terms import TermDetail, TermsListResponse
from app.services.term_service import TermService

router = APIRouter(prefix="/terms", tags=["terms"])
service = TermService()


@router.get("", response_model=TermsListResponse)
def list_terms(category: str | None = Query(default=None), _user: CurrentUser = Depends(require_permission("term:read"))) -> TermsListResponse:
    items = service.list_terms(category)
    return TermsListResponse(total=len(items), items=items)


@router.get("/categories")
def categories(_user: CurrentUser = Depends(require_permission("term:read"))) -> list[str]:
    return service.categories()


@router.get("/{term_id}", response_model=TermDetail)
def get_term(term_id: str, _user: CurrentUser = Depends(require_permission("term:read"))) -> TermDetail:
    term = service.get_term(term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term