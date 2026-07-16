import type { Locale } from "./types"

export type ToolRoute = { key: string; path: string; title: Record<Locale, string>; hint: Record<Locale, string>; endpoint: string; requiredPermission?: string }

export const toolRoutes: ToolRoute[] = [
  { key: "overview", path: "/", title: { zh: "知识库总览", en: "Catalog Overview" }, hint: { zh: "版本、分区与实体统计", en: "release and partitions" }, endpoint: "GET /catalog/overview", requiredPermission: "group:read" },
  { key: "terms", path: "/terms", title: { zh: "基础术语库", en: "Terms" }, hint: { zh: "术语与关联基团", en: "terms and groups" }, endpoint: "GET /catalog/terms", requiredPermission: "group:read" },
  { key: "groups", path: "/groups", title: { zh: "基团与谱图", en: "Group Cards" }, hint: { zh: "基团、振动与实例谱图", en: "groups and spectra" }, endpoint: "GET /catalog/groups/{id}", requiredPermission: "group:read" },
  { key: "materials", path: "/materials", title: { zh: "物质信息", en: "Materials" }, hint: { zh: "分子式、结构与谱峰", en: "formula and peaks" }, endpoint: "GET /catalog/materials/{id}", requiredPermission: "compound:read" },
  { key: "textbook-inventory", path: "/textbook-inventory", title: { zh: "教材物质谱图", en: "Textbook Inventory" }, hint: { zh: "基团、化合物与候选谱图", en: "groups, compounds and spectra" }, endpoint: "GET /catalog/textbook-inventory/overview", requiredPermission: "compound:read" },
  { key: "spectra", path: "/spectra", title: { zh: "全量谱图索引", en: "All Spectra" }, hint: { zh: "教材 / NIST 分区", en: "partitioned spectra" }, endpoint: "GET /catalog/spectra", requiredPermission: "spectrum:read" },
  { key: "hierarchy", path: "/hierarchy", title: { zh: "基团-物质层级", en: "Group Tree" }, hint: { zh: "根基团与叶物质", en: "roots and leaves" }, endpoint: "GET /catalog/hierarchy", requiredPermission: "group:read" },
  { key: "evidence", path: "/evidence", title: { zh: "证据链", en: "Evidence" }, hint: { zh: "原文片段与定位", en: "provenance spans" }, endpoint: "GET /catalog/evidence", requiredPermission: "evidence:read" },
  { key: "claims", path: "/claims", title: { zh: "声明与效应", en: "Claims" }, hint: { zh: "谱-构-效可追溯结论", en: "traceable claims" }, endpoint: "GET /catalog/claims", requiredPermission: "evidence:read" },
]

export function routeForPath(pathname: string): ToolRoute { return toolRoutes.find((route) => route.path !== "/" && pathname.startsWith(route.path)) ?? toolRoutes[0] }
