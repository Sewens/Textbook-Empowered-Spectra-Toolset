import { Select, Tag } from "antd"
import ReactECharts from "echarts-for-react"
import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogHierarchy } from "../api"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

export default function HierarchyPage() {
  const navigate = useNavigate()
  const [groupId, setGroupId] = useState<string>()
  const query = useQuery({ queryKey: ["catalog-hierarchy"], queryFn: fetchCatalogHierarchy })
  const groups = (query.data?.nodes ?? []).filter((node) => node.type === "group")
  const selected = groupId || groups[0]?.id
  const graph = useMemo(() => {
    const edges = (query.data?.edges ?? []).filter((edge) => edge.source === selected)
    const root = groups.find((node) => node.id === selected)
    const leaves = edges.map((edge) => (query.data?.nodes ?? []).find((node) => node.id === edge.target)).filter(Boolean)
    return { tooltip: { formatter: (params: any) => params.data.name }, series: [{ type: "graph", layout: "none", roam: true, symbolSize: (item: any) => item.category === 0 ? 52 : 28, data: [root && { id: root.id, name: root.label, x: 80, y: Math.max(240, leaves.length * 32), category: 0 }, ...leaves.map((leaf: any, index) => ({ id: leaf.id, name: leaf.label, x: 700, y: 40 + index * 56, category: 1 }))].filter(Boolean), links: edges.map((edge) => ({ source: edge.source, target: edge.target })), categories: [{ name: "基础基团" }, { name: "关联物质" }], lineStyle: { color: "#0f766e", width: 1.5, curveness: 0.08 }, label: { show: true, position: "right", fontSize: 12 }, emphasis: { focus: "adjacency" } }] }
  }, [query.data, groups, selected])
  if (query.isLoading) return <LoadingBlock />
  if (query.error) return <ErrorBlock error={query.error} />
  return <div className="page-grid graph-layout"><section className="panel"><div className="panel-head"><h2>基团 - 物质层级图</h2><Select value={selected} onChange={setGroupId} options={groups.map((group) => ({ value: group.id, label: group.label }))} style={{ width: 250 }} /></div><div className="panel-body"><p className="hierarchy-note">以基础基团为根节点，关联物质为叶子节点；该视图使用历史参考卡片保持既有的基团-实例浏览能力。</p><ReactECharts option={graph} style={{ height: 650 }} onEvents={{ click: (event: any) => event.dataType === "node" && event.data?.category === 0 ? navigate("/groups/" + event.data.id) : event.dataType === "node" ? navigate("/materials/" + event.data.id) : undefined }} /></div></section><aside className="panel"><div className="panel-head"><h2>当前根节点</h2><Tag color="blue">{groups.length} groups</Tag></div><div className="panel-body"><h3>{groups.find((group) => group.id === selected)?.label}</h3><p>点击中心根节点查看基团知识、振动模板与谱图；点击叶节点进入物质信息主页。</p><Tag color="green">{(query.data?.edges ?? []).filter((edge) => edge.source === selected).length} 个关联物质</Tag></div></aside></div>
}
