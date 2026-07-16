import { useMemo, useState } from "react"
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom"
import { Button, Dropdown, Select, Tag } from "antd"
import { GlobalOutlined, UserOutlined } from "@ant-design/icons"
import { useQuery, useQueryClient } from "@tanstack/react-query"

import { fetchCurrentUser, getStoredRole, setStoredRole } from "./api"
import { routeForPath, toolRoutes } from "./routes"
import type { Locale, RoleCode } from "./types"
import MaterialsPage from "./pages/MaterialsPage"

const roleOptions: { value: RoleCode; label: string }[] = [{ value: "ordinary_user", label: "普通用户" }, { value: "data_admin", label: "数据管理员" }, { value: "site_admin", label: "网站管理员" }]

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [locale, setLocale] = useState<Locale>("zh")
  const [role, setRole] = useState<RoleCode>(getStoredRole())
  const activeRoute = useMemo(() => routeForPath(location.pathname), [location.pathname])
  const userQuery = useQuery({ queryKey: ["current-user", role], queryFn: fetchCurrentUser })
  const permissions = userQuery.data?.permissions ?? []
  const forbidden = activeRoute.requiredPermission ? !permissions.includes(activeRoute.requiredPermission) : false
  function changeRole(next: RoleCode) { setStoredRole(next); setRole(next); void queryClient.invalidateQueries() }
  return <div className="app-shell">
    <header className="banner"><Link className="brand" to="/"><span className="mark" /><span><strong>Spectra Corpus Toolset</strong><small>谱-构-效知识图谱工作台</small></span></Link><p className="banner-copy">以物质为中心展示基团、红外谱图、特性候选和可追溯教材证据。</p><div className="banner-actions"><div className="lang-switch"><button className={locale === "zh" ? "active" : ""} onClick={() => setLocale("zh")}>中</button><button className={locale === "en" ? "active" : ""} onClick={() => setLocale("en")}>EN</button></div><Dropdown trigger={["click"]} dropdownRender={() => <div className="account-popover"><span className="field-label">本地开发角色</span><Select<RoleCode> value={role} options={roleOptions} onChange={changeRole} style={{ width: 210 }} /><p>权限以 API 为准；前端仅提供工作流入口。</p></div>}><Button icon={<UserOutlined />}>{userQuery.data?.role.name_zh ?? "账户入口"}</Button></Dropdown><Button icon={<GlobalOutlined />} onClick={() => navigate(activeRoute.path)}>{activeRoute.endpoint}</Button></div></header>
    <nav className="tool-tabs" aria-label="Tool routes">{toolRoutes.map((route) => <Link key={route.key} className={"tool-tab " + (activeRoute.key === route.key ? "active" : "")} to={route.path}><span>{route.title[locale]}</span><small>{route.hint[locale]}</small></Link>)}</nav>
    <main id="main_frame"><div className="frame-head"><div className="frame-title"><strong>{activeRoute.title[locale]}</strong><span>{activeRoute.endpoint}</span></div><div className="frame-actions">{forbidden ? <Tag color="error">forbidden · {activeRoute.requiredPermission}</Tag> : <Tag color="processing">schema v2.0.2</Tag>}<Tag>{userQuery.data?.role.code ?? role}</Tag></div></div><section className="frame-body">{forbidden ? <div className="state-panel"><h2>当前角色无权访问</h2><p>请选择有相应权限的本地开发角色。</p></div> : <Routes><Route path="/" element={<Navigate to="/materials" replace />} /><Route path="/materials" element={<MaterialsPage />} /><Route path="/materialsz" element={<Navigate to="/materials" replace />} /><Route path="*" element={<Navigate to="/materials" replace />} /></Routes>}</section></main>
    <footer className="footer"><span>IR KG schema v2.0.2 · spectrum-structure-effect workbench</span><span>{activeRoute.endpoint}</span></footer>
  </div>
}

export default App
