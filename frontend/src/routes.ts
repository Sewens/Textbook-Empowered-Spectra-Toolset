import type { Locale } from "./types"

export type ToolRoute = { key: string; path: string; title: Record<Locale, string>; hint: Record<Locale, string>; endpoint: string; requiredPermission?: string }

export const toolRoutes: ToolRoute[] = [
  { key: "materials", path: "/materials", title: { zh: "物质信息", en: "Materials" }, hint: { zh: "物质、基团、特性与谱图", en: "materials, groups and spectra" }, endpoint: "GET /catalog/textbook-inventory/materials", requiredPermission: "compound:read" },
]

export function routeForPath(pathname: string): ToolRoute { return toolRoutes.find((route) => route.path !== "/" && pathname.startsWith(route.path)) ?? toolRoutes[0] }
