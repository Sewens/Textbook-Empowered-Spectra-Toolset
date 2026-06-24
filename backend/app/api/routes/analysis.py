from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.core.security import CurrentUser, require_permission
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    EffectDetailResponse,
    EffectsResponse,
    SpectraResponse,
    WavenumberQuery,
    WavenumberSearchResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.graph_service import GraphService

router = APIRouter(tags=["analysis"])
service = GraphService()
analysis_service = AnalysisService(service)


@router.get("/wavenumber", response_model=WavenumberSearchResponse)
def search_wavenumber(value: float = Query(...), tolerance: float = Query(15, ge=0), _user: CurrentUser = Depends(require_permission("spectrum:read"))) -> WavenumberSearchResponse:
    items = service.search_wavenumber(value, tolerance)
    return WavenumberSearchResponse(query=WavenumberQuery(value=value, tolerance=tolerance), total=len(items), items=items[:200])


@router.get("/effects", response_model=EffectsResponse)
def list_effects(_user: CurrentUser = Depends(require_permission("evidence:read"))) -> EffectsResponse:
    effects = service.list_effects()
    return EffectsResponse(total_effects=len(effects), effects=effects)


@router.get("/effects/{effect_key}", response_model=EffectDetailResponse)
def get_effect(effect_key: str, _user: CurrentUser = Depends(require_permission("evidence:read"))) -> EffectDetailResponse:
    items = service.get_effect(effect_key)
    return EffectDetailResponse(effect_key=effect_key, total=len(items), items=items)


@router.get("/spectra", response_model=SpectraResponse)
def list_spectra(_user: CurrentUser = Depends(require_permission("spectrum:read"))) -> SpectraResponse:
    items = service.list_spectra()
    return SpectraResponse(total=len(items), items=items)


@router.post("/analysis", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest, background_tasks: BackgroundTasks, _user: CurrentUser = Depends(require_permission("analysis:create"))) -> AnalysisResponse:
    # Prototype path: short deterministic task runs inline. BackgroundTasks is kept
    # in the API signature for future async report persistence.
    background_tasks.add_task(lambda: None)
    return analysis_service.analyze(request)
