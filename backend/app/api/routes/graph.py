from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import CurrentUser, require_permission
from app.schemas.graph import CompoundListResponse, FunctionalGroupDocument, GraphResponse, GroupListResponse
from app.services.graph_service import GraphService

router = APIRouter(prefix="/groups", tags=["groups"])
graph_router = APIRouter(prefix="/graph", tags=["graph"])
compound_router = APIRouter(prefix="/compounds", tags=["compounds"])
service = GraphService()


@router.get("", response_model=GroupListResponse)
def list_groups(q: str | None = Query(default=None), _user: CurrentUser = Depends(require_permission("group:read"))) -> GroupListResponse:
    items = service.list_groups(q)
    return GroupListResponse(total=len(items), items=items)


@router.get("/{group_id}", response_model=FunctionalGroupDocument)
def get_group(group_id: str, _user: CurrentUser = Depends(require_permission("group:read"))) -> FunctionalGroupDocument:
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@graph_router.get("", response_model=GraphResponse)
def get_graph(_user: CurrentUser = Depends(require_permission("group:read"))) -> GraphResponse:
    return service.build_graph()


@compound_router.get("", response_model=CompoundListResponse)
def list_compounds(q: str | None = Query(default=None), _user: CurrentUser = Depends(require_permission("compound:read"))) -> CompoundListResponse:
    items = service.list_compounds(q)
    return CompoundListResponse(total=len(items), items=items)
