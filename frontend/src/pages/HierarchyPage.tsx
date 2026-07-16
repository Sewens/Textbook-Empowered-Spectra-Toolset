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
  const selected = groupId || groups.find((group) => (query.data?.edges ?? []).some((edge) => edge.source === group.id))?.id || groups[0]?.id
  const option = useMemo(() => {
    const root = groups.find((node) => node.id === selected)
    const children = (query.data?.edges ?? []).filter((edge) => edge.source === selected).map((edge) => (query.data?.nodes ?? []).find((node) => node.id === edge.target)).filter(Boolean).map((node: any) => ({ id: node.id, name: node.label, value: node.id }))
    return { tooltip: { trigger: "item", triggerOn: "mousemove" }, series: [{ type: "tree", data: root ? [{ id: root.id, name: root.label, value: root.id, children }] : [], top: "8%", left: "9%", bottom: "8%", right: "26%", orient: "LR", symbol: "roundRect", symbolSize: [116, 34], initialTreeDepth: -1, expandAndCollapse: false, lineStyle: { color: "#0f766e", width: 1.5 }, label: { position: "left", verticalAlign: "middle", align: "right", fontSize: 13, overflow: "truncate", width: 150 }, leaves: { label: { position: "right", align: "left", width: 180, overflow: "truncate" } }, emphasis: { focus: "descendant" } }] }
  }, [query.data, groups, selected])
  if (query.isLoading) return <LoadingBlock />
  if (query.error) return <ErrorBlock error={query.error} />
  const childCount = (query.data?.edges ?? []).filter((edge) => edge.source === selected).length
  return <div className="page-grid graph-layout"><section className="panel"><div className="panel-head"><h2>基团 - 物质层级图</h2><Select value={selected} onChange={setGroupId} options={groups.map((group) => ({ value: group.id, label: group.label + " · " + (query.data?.edges ?? []).filter((edge) => edge.source === group.id).length + " 物质" }))} style={{ width: 280 }} /></div><div className="panel-body"><p className="hierarchy-note">基础基团为根节点，关联物质为叶子节点。选择含有实例物质的基团，点击根或叶节点可打开对应详情页。</p><ReactECharts option={option} style={{ height: 650 }} onEvents={{ click: (event: any) => event.data?.children ? navigate("/groups/" + event.data.id) : event.data?.id ? navigate("/materials/" + event.data.id) : undefined }} /></div></section><aside className="panel"><div className="panel-head"><h2>当前根节点</h2><Tag color="blue">{groups.length} groups</Tag></div><div className="panel-body"><h3>{groups.find((group) => group.id === selected)?.label}</h3><p>根节点展示该基团的关系树；叶节点进入物质信息主页，查看分子式、谱图与峰归属。</p><Tag color="green">{childCount} 个关联物质</Tag></div></aside></div>
}
