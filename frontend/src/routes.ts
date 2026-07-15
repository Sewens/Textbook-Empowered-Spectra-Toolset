import type { Locale } from "./types"

export type ToolRoute = { key: string; path: string; title: Record<Locale, string>; hint: Record<Locale, string>; endpoint: string; requiredPermission?: string }

export const toolRoutes: ToolRoute[] = [
  { key: "overview", path: "/", title: { zh: "知识库总览", en: "Catalog Overview" }, hint: { zh: "版本、分区与实体统计", en: "release and partitions" }, endpoint: "GET /catalog/overview", requiredPermission: "group:read" },
  { key: "concepts", path: "/concepts", title: { zh: "概念与关系", en: "Concepts" }, hint: { zh: "官能团、振动、效应概念", en: "concept registry" }, endpoint: "GET /catalog/concepts", requiredPermission: "group:read" },
  { key: "materials", path: "/materials", title: { zh: "材料实体", en: "Materials" }, hint: { zh: "教材与外部材料记录", en: "material registry" }, endpoint: "GET /catalog/materials", requiredPermission: "compound:read" },
  { key: "spectra", path: "/spectra", title: { zh: "谱图索引", en: "Spectra" }, hint: { zh: "教材 accepted / NIST staging", en: "partitioned spectra" }, endpoint: "GET /catalog/spectra", requiredPermission: "spectrum:read" },
  { key: "evidence", path: "/evidence", title: { zh: "证据链", en: "Evidence" }, hint: { zh: "原文片段与定位", en: "provenance spans" }, endpoint: "GET /catalog/evidence", requiredPermission: "evidence:read" },
  { key: "claims", path: "/claims", title: { zh: "声明与效应", en: "Claims" }, hint: { zh: "谱-构-效可追溯结论", en: "traceable claims" }, endpoint: "GET /catalog/claims", requiredPermission: "analysis:create" },
  { key: "graph", path: "/graph", title: { zh: "知识图谱", en: "Knowledge Graph" }, hint: { zh: "实体和关系边", en: "entity graph" }, endpoint: "GET /catalog/graph", requiredPermission: "group:read" },
]

export function routeForPath(pathname: string): ToolRoute { return toolRoutes.find((route) => route.path !== "/" && pathname.startsWith(route.path)) ?? toolRoutes[0] }
