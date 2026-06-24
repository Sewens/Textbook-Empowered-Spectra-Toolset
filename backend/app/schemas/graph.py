from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class GroupIndexItem(FlexibleModel):
    group_id: str
    name_zh: str
    name_en: str
    chemical_formula: str | None = None
    smarts: str | None = None
    group_class: str | None = None
    vibration_count: int = 0
    spectrum_count: int = 0
    peak_count: int = 0
    image_count: int = 0
    evidence_count: int = 0
    compound_count: int = 0
    source_claim_count: int = 0
    relation_count: int = 0


class TextbookDefinition(FlexibleModel):
    source_book: str | None = None
    chapter: str | None = None
    section: str | None = None
    page: int | None = None
    original_quote: str | None = None


class WavenumberRange(FlexibleModel):
    min_cm_1: float | None = None
    max_cm_1: float | None = None
    peak_cm_1: float | None = None
    unit: str | None = None
    range_text_original: str | None = None
    qualifier: str | None = None


class InherentVibration(FlexibleModel):
    vibration_id: str
    symbol: str | None = None
    mode: str | None = None
    sub_mode: str | None = None
    motion_description: str | None = None
    wavenumber_ranges: list[WavenumberRange] = Field(default_factory=list)
    base_wavenumber_range: list[float] | None = None
    base_intensity: str | None = None
    base_peak_shape: str | None = None
    diagnosticity: str | None = None
    environment_scope: str | None = None
    textbook_description: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    source_claim_ids: list[str] = Field(default_factory=list)


class PeakAssignment(FlexibleModel):
    assignment_id: str | None = None
    vibration_id: str | None = None
    occurrence_id: str | None = None
    assignment_text: str | None = None
    assignment_confidence: float | None = None
    effects: list[Any] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class AnnotatedPeak(FlexibleModel):
    peak_id: str | None = None
    measured_wavenumber: float | None = None
    wavenumber_cm_1: float | None = None
    wavenumber_min_cm_1: float | None = None
    wavenumber_max_cm_1: float | None = None
    transmittance_percent: float | None = None
    intensity_label: str | None = None
    peak_shape: str | None = None
    vibration_id: str | None = None
    chemical_effect: str | None = None
    state_effect: str | None = None
    peak_assignment: str | None = None
    assignments: list[PeakAssignment] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class SpectralGalleryItem(FlexibleModel):
    spectrum_id: str | None = None
    figure_id: str | None = None
    figure_caption: str | None = None
    compound_name_zh: str | None = None
    compound_name_en: str | None = None
    compound_id: str | None = None
    smiles: str | None = None
    molecular_formula: str | None = None
    sample_state: str | None = None
    pdf_page_number: int | None = None
    page_pdf: int | None = None
    mineru_crop_image_path: str | None = None
    image_path: str | None = None
    textbook_analysis_quote: str | None = None
    analysis_quote: str | None = None
    spectrum_quality: str | None = None
    annotated_peaks: list[AnnotatedPeak] = Field(default_factory=list)
    peaks: list[AnnotatedPeak] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class FunctionalGroupDocument(FlexibleModel):
    schema_version: str | None = None
    card_type: str | None = None
    group_id: str
    name_zh: str
    name_en: str
    parent_group_id: str | None = None
    smarts: str | None = None
    chemical_formula: str | None = None
    group: dict[str, Any] = Field(default_factory=dict)
    evidence_spans: list[dict[str, Any]] = Field(default_factory=list)
    definitions: list[dict[str, Any]] = Field(default_factory=list)
    vibration_templates: list[InherentVibration] = Field(default_factory=list)
    compound_examples: list[dict[str, Any]] = Field(default_factory=list)
    source_claims: list[dict[str, Any]] = Field(default_factory=list)
    relations: list[dict[str, Any]] = Field(default_factory=list)
    quality: dict[str, Any] = Field(default_factory=dict)
    extraction_metadata: dict[str, Any] = Field(default_factory=dict)
    textbook_definitions: list[TextbookDefinition] = Field(default_factory=list)
    inherent_vibrations: list[InherentVibration] = Field(default_factory=list)
    spectral_gallery: list[SpectralGalleryItem] = Field(default_factory=list)


class GroupListResponse(BaseModel):
    total: int
    items: list[GroupIndexItem]


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    data: dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class CompoundRecord(BaseModel):
    compound_id: str
    name_zh: str | None = None
    name_en: str | None = None
    molecular_formula: str | None = None
    smiles: str | None = None
    compound_class: str | None = None
    group_ids: list[str] = Field(default_factory=list)
    spectrum_count: int = 0
    peak_count: int = 0


class CompoundListResponse(BaseModel):
    total: int
    items: list[CompoundRecord]
