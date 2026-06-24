from pydantic import BaseModel, Field


class WavenumberQuery(BaseModel):
    value: float
    tolerance: float = 15


class WavenumberSearchResult(BaseModel):
    group_id: str
    group_name_zh: str
    group_name_en: str
    match_type: str
    wavenumber: float | list[float]
    distance: float | None = None
    vibration_id: str | None = None
    assignment: str | None = None
    evidence_quote: str | None = None
    image_path: str | None = None
    figure_id: str | None = None
    spectrum_id: str | None = None
    compound_id: str | None = None
    compound_name_zh: str | None = None
    source_book: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class WavenumberSearchResponse(BaseModel):
    query: WavenumberQuery
    total: int
    items: list[WavenumberSearchResult]


class EffectSummary(BaseModel):
    effect_key: str
    effect_type: str
    effect_zh: str = ""
    term_id: str | None = None
    count: int


class EffectEvidence(BaseModel):
    effect_key: str
    effect_type: str
    effect_zh: str = ""
    term_id: str | None = None
    group_id: str
    group_name_zh: str
    vibration_id: str | None = None
    measured_wavenumber: float | None = None
    peak_assignment: str | None = None
    figure_id: str | None = None
    image_path: str | None = None
    evidence_quote: str | None = None


class EffectsResponse(BaseModel):
    total_effects: int
    effects: list[EffectSummary]


class EffectDetailResponse(BaseModel):
    effect_key: str
    total: int
    items: list[EffectEvidence]


class SpectraRecord(BaseModel):
    group_id: str
    group_name_zh: str
    spectrum_id: str
    figure_id: str | None = None
    figure_caption: str | None = None
    compound_id: str | None = None
    compound_name_zh: str | None = None
    compound_name_en: str | None = None
    molecular_formula: str | None = None
    smiles: str | None = None
    sample_state: str | None = None
    image_path: str | None = None
    annotated_peak_count: int = 0
    evidence_ids: list[str] = Field(default_factory=list)


class SpectraResponse(BaseModel):
    total: int
    items: list[SpectraRecord]


class AnalysisRequest(BaseModel):
    wavenumber: float | None = None
    tolerance: float = 15
    query: str | None = None


class AnalysisResponse(BaseModel):
    summary: str
    matches: list[WavenumberSearchResult] = Field(default_factory=list)
