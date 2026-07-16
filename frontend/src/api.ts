import axios from 'axios'
import type {
  CompoundRecord,
  CurrentUser,
  EffectSummary,
  FunctionalGroupDocument,
  GraphResponse,
  GroupIndexItem,
  ManifestResponse,
  RoleCode,
  SpectraRecord,
  WavenumberSearchResult,
  TerminologyDetail,
} from './types'

const ROLE_STORAGE_KEY = 'spectra.role'

export function getStoredRole(): RoleCode {
  const value = localStorage.getItem(ROLE_STORAGE_KEY)
  return value === 'data_admin' || value === 'site_admin' ? value : 'ordinary_user'
}

export function setStoredRole(role: RoleCode) {
  localStorage.setItem(ROLE_STORAGE_KEY, role)
}

export const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  config.headers.set('X-User-Role', getStoredRole())
  return config
})

export function resolveSpectraUrl(path: string | null | undefined): string | null {
  if (!path) return null
  if (/^https?:\/\//.test(path) || path.startsWith('/')) return path
  return path.replace(/^assets\/spectra\//, '/assets/spectra/')
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  const response = await api.get<CurrentUser>('/user/me')
  return response.data
}

export async function fetchManifest(): Promise<ManifestResponse> {
  const response = await api.get<ManifestResponse>('/manifest')
  return response.data
}

export async function fetchGroups(q?: string): Promise<GroupIndexItem[]> {
  const response = await api.get<{ total: number; items: GroupIndexItem[] }>('/groups', { params: { q } })
  return response.data.items
}

export async function fetchGroup(groupId: string): Promise<FunctionalGroupDocument> {
  const response = await api.get<FunctionalGroupDocument>('/groups/' + groupId)
  return response.data
}

export async function fetchCompounds(q?: string): Promise<CompoundRecord[]> {
  const response = await api.get<{ total: number; items: CompoundRecord[] }>('/compounds', { params: { q } })
  return response.data.items
}

export async function fetchSpectra(): Promise<SpectraRecord[]> {
  const response = await api.get<{ total: number; items: SpectraRecord[] }>('/spectra')
  return response.data.items
}

export async function searchWavenumber(value: number, tolerance = 15): Promise<WavenumberSearchResult[]> {
  const response = await api.get<{ total: number; items: WavenumberSearchResult[] }>('/wavenumber', { params: { value, tolerance } })
  return response.data.items.sort((a, b) => (a.distance ?? 0) - (b.distance ?? 0))
}

export async function fetchEffects(): Promise<EffectSummary[]> {
  const response = await api.get<{ total_effects: number; effects: EffectSummary[] }>('/effects')
  return response.data.effects
}

export async function fetchGraph(): Promise<GraphResponse> {
  const response = await api.get<GraphResponse>('/graph')
  return response.data
}


export async function fetchCatalogOverview() {
  const response = await api.get<import("./types").CatalogOverview>("/catalog/overview")
  return response.data
}

export async function fetchCatalogEntities(type: import("./types").CatalogEntityType, q?: string) {
  const response = await api.get<{ total: number; items: import("./types").CatalogEntity[] }>("/catalog/" + type + "s", { params: { q } })
  return response.data.items
}

export async function fetchCatalogSpectra(source_scope?: "textbook" | "nist", q?: string) {
  const response = await api.get<{ total: number; items: import("./types").CatalogSpectrum[] }>("/catalog/spectra", { params: { source_scope, q } })
  return response.data.items
}

export async function fetchCatalogEvidence(q?: string) {
  const response = await api.get<{ total: number; items: import("./types").CatalogEvidence[] }>("/catalog/evidence", { params: { q } })
  return response.data.items
}

export async function fetchCatalogGraph(): Promise<GraphResponse> {
  const response = await api.get<GraphResponse>("/catalog/graph")
  return response.data
}


export async function fetchCatalogTerms(q?: string) {
  const response = await api.get<{ total: number; items: import("./types").KnowledgeTerm[] }>("/catalog/terms", { params: { q } })
  return response.data.items
}

export async function fetchCatalogTerm(termId: string): Promise<TerminologyDetail> {
  const response = await api.get<TerminologyDetail>("/catalog/terms/" + termId)
  return response.data
}

export async function fetchCatalogGroup(groupId: string) {
  const response = await api.get<import("./types").GroupKnowledgeDetail>("/catalog/groups/" + groupId)
  return response.data
}

export async function fetchCatalogMaterial(materialId: string) {
  const response = await api.get<import("./types").MaterialKnowledgeDetail>("/catalog/materials/" + materialId)
  return response.data
}

export async function fetchCatalogHierarchy() {
  const response = await api.get<GraphResponse>("/catalog/hierarchy")
  return response.data
}


export async function fetchReferenceMaterials(q?: string) {
  const response = await api.get<{ total: number; items: import("./types").CatalogEntity[] }>("/catalog/reference-materials", { params: { q } })
  return response.data.items
}

export async function fetchNistStats(): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>("/nist/stats")
  return response.data
}

export async function fetchTextbookInventoryOverview(): Promise<import("./types").TextbookInventoryOverview> {
  const response = await api.get<import("./types").TextbookInventoryOverview>("/catalog/textbook-inventory/overview")
  return response.data
}

export async function fetchTextbookInventoryBooks(): Promise<string[]> {
  const response = await api.get<{ total: number; items: string[] }>("/catalog/textbook-inventory/books")
  return response.data.items
}

export async function fetchTextbookInventory(kind: import("./types").TextbookInventoryKind, q?: string, book?: string): Promise<import("./types").TextbookInventoryRow[]> {
  const response = await api.get<{ total: number; items: import("./types").TextbookInventoryRow[] }>("/catalog/textbook-inventory/" + kind, { params: { q, book, limit: 500 } })
  return response.data.items
}

export async function fetchTextbookInventoryDetail(kind: import("./types").TextbookInventoryKind, candidateId: string): Promise<import("./types").TextbookInventoryDetail> {
  const response = await api.get<import("./types").TextbookInventoryDetail>("/catalog/textbook-inventory/" + kind + "/" + encodeURIComponent(candidateId))
  return response.data
}

export async function fetchTextbookInventoryUnifiedDetail(kind: "materials" | "spectra", candidateId: string): Promise<import("./types").UnifiedTextbookDetail> {
  const response = await api.get<import("./types").UnifiedTextbookDetail>("/catalog/textbook-inventory/details/" + kind + "/" + encodeURIComponent(candidateId))
  return response.data
}
