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
