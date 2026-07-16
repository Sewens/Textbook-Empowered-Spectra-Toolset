export type RoleCode = 'ordinary_user' | 'data_admin' | 'site_admin'
export type Locale = 'zh' | 'en'

export interface CurrentUser {
  id: string
  name: string
  role: { code: RoleCode; name_zh: string; description: string }
  permissions: string[]
}

export interface ManifestStats {
  functional_groups: number
  evidence_spans: number
  vibration_templates: number
  source_claims: number
  relations: number
  compound_examples: number
  spectra: number
  peaks: number
  image_assets: number
}

export interface ManifestResponse {
  release_path: string
  release_id: string
  schema_version: string
  document_version: string
  generated_at: string
  status: string
  stats: ManifestStats
  schema_summary: Record<string, unknown>
  data_summary: Record<string, unknown>
}

export interface GroupIndexItem {
  group_id: string
  name_zh: string
  name_en: string
  chemical_formula: string | null
  smarts: string | null
  group_class?: string | null
  vibration_count: number
  spectrum_count: number
  peak_count: number
  image_count: number
  evidence_count: number
  compound_count: number
  source_claim_count: number
  relation_count: number
}

export interface WavenumberRange {
  min_cm_1?: number | null
  max_cm_1?: number | null
  peak_cm_1?: number | null
  unit?: string | null
  range_text_original?: string | null
  qualifier?: string | null
}

export interface InherentVibration {
  vibration_id: string
  symbol: string | null
  mode: string | null
  sub_mode?: string | null
  motion_description?: string | null
  wavenumber_ranges?: WavenumberRange[]
  base_wavenumber_range?: [number, number] | null
  base_intensity?: string | null
  base_peak_shape?: string | null
  diagnosticity?: string | null
  environment_scope?: string | null
  textbook_description?: string | null
  evidence_ids?: string[]
  source_claim_ids?: string[]
}

export interface PeakAssignment {
  assignment_id?: string | null
  vibration_id?: string | null
  occurrence_id?: string | null
  assignment_text?: string | null
  assignment_confidence?: number | null
  effects?: unknown[]
  evidence_ids?: string[]
  notes?: string | null
}

export interface AnnotatedPeak {
  peak_id?: string | null
  measured_wavenumber?: number | null
  wavenumber_cm_1?: number | null
  wavenumber_min_cm_1?: number | null
  wavenumber_max_cm_1?: number | null
  transmittance_percent?: number | null
  intensity_label?: string | null
  peak_shape?: string | null
  vibration_id?: string | null
  chemical_effect?: string | null
  state_effect?: string | null
  peak_assignment?: string | null
  assignments?: PeakAssignment[]
  evidence_ids?: string[]
  notes?: string | null
}

export interface SpectralGalleryItem {
  spectrum_id?: string | null
  figure_id?: string | null
  figure_caption?: string | null
  compound_id?: string | null
  compound_name_zh?: string | null
  compound_name_en?: string | null
  molecular_formula?: string | null
  smiles?: string | null
  sample_state?: string | null
  pdf_page_number?: number | null
  mineru_crop_image_path?: string | null
  image_path?: string | null
  textbook_analysis_quote?: string | null
  analysis_quote?: string | null
  annotated_peaks?: AnnotatedPeak[]
  peaks?: AnnotatedPeak[]
  evidence_ids?: string[]
}

export interface FunctionalGroupDocument {
  schema_version?: string | null
  card_type?: string | null
  group_id: string
  name_zh: string
  name_en: string
  parent_group_id?: string | null
  smarts: string | null
  chemical_formula: string | null
  group: Record<string, any>
  evidence_spans: Record<string, any>[]
  definitions: Record<string, any>[]
  vibration_templates: InherentVibration[]
  compound_examples: Record<string, any>[]
  source_claims: Record<string, any>[]
  relations: Record<string, any>[]
  quality: Record<string, any>
  extraction_metadata: Record<string, any>
  textbook_definitions: Record<string, any>[]
  inherent_vibrations: InherentVibration[]
  spectral_gallery: SpectralGalleryItem[]
}

export interface CompoundRecord {
  compound_id: string
  name_zh?: string | null
  name_en?: string | null
  molecular_formula?: string | null
  smiles?: string | null
  compound_class?: string | null
  group_ids: string[]
  spectrum_count: number
  peak_count: number
}

export interface SpectraRecord {
  group_id: string
  group_name_zh: string
  spectrum_id: string
  figure_id?: string | null
  figure_caption?: string | null
  compound_id?: string | null
  compound_name_zh?: string | null
  compound_name_en?: string | null
  molecular_formula?: string | null
  smiles?: string | null
  sample_state?: string | null
  image_path?: string | null
  annotated_peak_count: number
  evidence_ids: string[]
}

export interface WavenumberSearchResult {
  group_id: string
  group_name_zh: string
  group_name_en: string
  match_type: string
  wavenumber: number | number[]
  distance?: number | null
  vibration_id?: string | null
  assignment?: string | null
  evidence_quote?: string | null
  image_path?: string | null
  figure_id?: string | null
  spectrum_id?: string | null
  compound_id?: string | null
  compound_name_zh?: string | null
  source_book?: string | null
  evidence_ids: string[]
}

export interface EffectSummary {
  effect_key: string
  effect_type: string
  effect_zh: string
  term_id?: string | null
  count: number
}

export interface GraphNode { id: string; label: string; type: string; data: Record<string, unknown> }
export interface GraphEdge { id: string; source: string; target: string; label: string; data: Record<string, unknown> }
export interface GraphResponse { nodes: GraphNode[]; edges: GraphEdge[] }


export type CatalogEntityType = "concept" | "material" | "claim" | "source"

export interface CatalogOverview {
  release_id: string
  schema_release: string | null
  packet_schema: string | null
  release_status: string | null
  counts: Record<string, number>
  data_partitions: { accepted_textbook_packets: number; nist_metadata_records: number; quarantine_included: boolean; nist_is_staging: boolean }
}

export interface CatalogEntity {
  entity_id: string
  entity_type: string
  name: string
  source_scope: "textbook" | "nist"
  review_status: string
  payload: Record<string, unknown>
}

export interface CatalogSpectrum {
  spectrum_id: string
  material_id: string | null
  modality: string | null
  technique: string | null
  source_scope: "textbook" | "nist"
  review_status: string
  payload: Record<string, unknown>
}

export interface CatalogEvidence {
  evidence_id: string
  source_id: string
  evidence_type: string | null
  text: string | null
  source_scope: "textbook" | "nist"
  review_status: string
  payload: Record<string, unknown>
}


export interface KnowledgeTerm { term_id: string; term_type: "concept" | "group"; name: string; source_scope: string; payload: Record<string, any> }
export interface KnowledgeSpectrum { spectrum_id: string; material_id: string; image_url?: string | null; peaks: Array<{ measured_wavenumber?: number; peak_assignment?: string }>; payload: Record<string, any> }
export interface GroupKnowledgeDetail extends CatalogEntity { materials: CatalogEntity[]; spectra: KnowledgeSpectrum[]; vibrations: Record<string, any>[] }
export interface MaterialKnowledgeDetail extends CatalogEntity { groups: Array<CatalogEntity & { group_id: string }>; spectra: KnowledgeSpectrum[] }
