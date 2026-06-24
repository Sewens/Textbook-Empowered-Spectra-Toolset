import type { Locale } from './types'

export type ToolRoute = {
  key: string
  path: string
  title: Record<Locale, string>
  hint: Record<Locale, string>
  endpoint: string
  requiredPermission?: string
}

export const toolRoutes: ToolRoute[] = [
  { key: 'groups', path: '/', title: { zh: '基团卡片', en: 'Group Cards' }, hint: { zh: 'FG_*.json 目录', en: 'FG_*.json index' }, endpoint: 'GET /groups', requiredPermission: 'group:read' },
  { key: 'spectra', path: '/spectra', title: { zh: '谱图查看', en: 'Spectra' }, hint: { zh: '峰位与归属', en: 'peaks and assignments' }, endpoint: 'GET /spectra', requiredPermission: 'spectrum:read' },
  { key: 'search', path: '/search', title: { zh: '波数检索', en: 'Wavenumber Search' }, hint: { zh: '模板与实测峰', en: 'templates and peaks' }, endpoint: 'GET /wavenumber', requiredPermission: 'spectrum:read' },
  { key: 'compounds', path: '/compounds', title: { zh: '化合物实例', en: 'Compounds' }, hint: { zh: '去重 compound', en: 'deduplicated compounds' }, endpoint: 'GET /compounds', requiredPermission: 'compound:read' },
  { key: 'graph', path: '/graph', title: { zh: '知识图谱', en: 'Graph' }, hint: { zh: '节点与边', en: 'nodes and edges' }, endpoint: 'GET /graph', requiredPermission: 'group:read' },
  { key: 'evidence', path: '/evidence', title: { zh: '证据追踪', en: 'Evidence' }, hint: { zh: 'source claims', en: 'source claims' }, endpoint: 'GET /groups/{id}', requiredPermission: 'evidence:read' },
  { key: 'curation', path: '/curation', title: { zh: '标注流转', en: 'Curation' }, hint: { zh: 'RBAC 预留', en: 'RBAC ready' }, endpoint: 'POST /analysis', requiredPermission: 'analysis:create' },
]

export function routeForPath(pathname: string): ToolRoute {
  return toolRoutes.find((route) => route.path !== '/' && pathname.startsWith(route.path)) ?? toolRoutes[0]
}
