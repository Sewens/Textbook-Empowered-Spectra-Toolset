from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.graph_service import GraphService


class AnalysisService:
    def __init__(self, graph_service: GraphService | None = None) -> None:
        self.graph_service = graph_service or GraphService()

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        if request.wavenumber is None:
            return AnalysisResponse(summary="当前原型支持按波数进行谱学证据检索。", matches=[])
        matches = self.graph_service.search_wavenumber(request.wavenumber, request.tolerance)
        return AnalysisResponse(
            summary=f"在 ±{request.tolerance:g} cm⁻¹ 容差内找到 {len(matches)} 条候选证据。",
            matches=matches,
        )
