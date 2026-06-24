import { useMemo, useState } from 'react'
import { Link, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { Button, Dropdown, Select, Tag } from 'antd'
import { GlobalOutlined, UserOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchCurrentUser, getStoredRole, setStoredRole } from './api'
import { routeForPath, toolRoutes } from './routes'
import type { Locale, RoleCode } from './types'
import GroupsPage from './pages/GroupsPage'
import SpectraPage from './pages/SpectraPage'
import SearchPage from './pages/SearchPage'
import CompoundsPage from './pages/CompoundsPage'
import GraphPage from './pages/GraphPage'
import EvidencePage from './pages/EvidencePage'
import CurationPage from './pages/CurationPage'

const roleOptions: { value: RoleCode; label: string }[] = [
  { value: 'ordinary_user', label: '普通用户' },
  { value: 'data_admin', label: '数据管理员' },
  { value: 'site_admin', label: '网站管理员' },
]

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [locale, setLocale] = useState<Locale>('zh')
  const [role, setRole] = useState<RoleCode>(getStoredRole())
  const activeRoute = useMemo(() => routeForPath(location.pathname), [location.pathname])
  const userQuery = useQuery({ queryKey: ['current-user', role], queryFn: fetchCurrentUser })
  const permissions = userQuery.data?.permissions ?? []
  const forbidden = activeRoute.requiredPermission ? !permissions.includes(activeRoute.requiredPermission) : false

  function changeRole(next: RoleCode) {
    setStoredRole(next)
    setRole(next)
    void queryClient.invalidateQueries()
  }

  return (
    <div className="app-shell">
      <header className="banner">
        <Link className="brand" to="/">
          <span className="mark" aria-hidden="true" />
          <span>
            <strong>Spectra Corpus Toolset</strong>
            <small>IR-IE v0.7 谱学语料库与工具集</small>
          </span>
        </Link>
        <p className="banner-copy">
          面向材料科学家的谱学知识工作台：顶部只保留账户与语言，工具切换集中在路由 tab，当前工具在 main_frame 中展开。
        </p>
        <div className="banner-actions">
          <div className="lang-switch" aria-label="Language switch">
            <button className={locale === 'zh' ? 'active' : ''} onClick={() => setLocale('zh')}>中</button>
            <button className={locale === 'en' ? 'active' : ''} onClick={() => setLocale('en')}>EN</button>
          </div>
          <Dropdown
            trigger={['click']}
            dropdownRender={() => (
              <div className="account-popover">
                <span className="field-label">本地开发角色</span>
                <Select<RoleCode> value={role} options={roleOptions} onChange={changeRole} style={{ width: 210 }} />
                <p>前端只做 UX 准备；实际权限由后端 RBAC 拒绝或放行。</p>
              </div>
            )}
          >
            <Button icon={<UserOutlined />}>{userQuery.data?.role.name_zh ?? '账户入口'}</Button>
          </Dropdown>
          <Button icon={<GlobalOutlined />} onClick={() => navigate(activeRoute.path)}>{activeRoute.endpoint}</Button>
        </div>
      </header>

      <nav className="tool-tabs" aria-label="Tool routes">
        {toolRoutes.map((route) => (
          <Link key={route.key} className={'tool-tab ' + (activeRoute.key === route.key ? 'active' : '')} to={route.path}>
            <span>{route.title[locale]}</span>
            <small>{route.hint[locale]}</small>
          </Link>
        ))}
      </nav>

      <main id="main_frame">
        <div className="frame-head">
          <div className="frame-title">
            <strong>{activeRoute.title[locale]}</strong>
            <span>{activeRoute.endpoint}</span>
          </div>
          <div className="frame-actions">
            {forbidden ? <Tag color="error">forbidden · {activeRoute.requiredPermission}</Tag> : <Tag color="processing">schema v0.7</Tag>}
            <Tag>{userQuery.data?.role.code ?? role}</Tag>
          </div>
        </div>
        <section className="frame-body">
          {forbidden ? (
            <div className="state-panel"><h2>当前角色无权访问</h2><p>请选择数据管理员或网站管理员，或等待后续正式登录系统接入。</p></div>
          ) : (
            <Routes>
              <Route path="/" element={<GroupsPage />} />
              <Route path="/groups/:groupId" element={<GroupsPage />} />
              <Route path="/spectra" element={<SpectraPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/compounds" element={<CompoundsPage />} />
              <Route path="/graph" element={<GraphPage />} />
              <Route path="/evidence" element={<EvidencePage />} />
              <Route path="/curation" element={<CurationPage />} />
            </Routes>
          )}
        </section>
      </main>

      <footer className="footer"><span>IR-IE v0.7 · JupyterLab-style workbench</span><span>{activeRoute.endpoint}</span></footer>
    </div>
  )
}

export default App
