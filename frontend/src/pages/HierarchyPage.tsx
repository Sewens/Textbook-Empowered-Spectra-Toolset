import { Checkbox, Divider, Input, List, Space, Statistic, Tag } from "antd"
import ReactECharts from "echarts-for-react"
import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchMaterialRelationshipGraph } from "../api"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

export default function HierarchyPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [showStructure, setShowStructure] = useState(true)
  const [showSimilarity, setShowSimilarity] = useState(true)
  const query = useQuery({ queryKey: ["material-relationship-graph"], queryFn: fetchMaterialRelationshipGraph })
  const allNodes = query.data?.nodes ?? []
  const unresolved = allNodes.filter((node) => node.relationship_status === "needs_structure_confirmation")
  const plottedNodes = allNodes.filter((node) => node.relationship_status !== "needs_structure_confirmation")
  const option = useMemo(() => {
    const graph = query.data
    const token = search.trim().toLocaleLowerCase()
    const visibleEdges = (graph?.edges ?? []).filter((edge) => edge.relation_type === "has_functional_group" ? showStructure : showSimilarity)
    const isMatch = (label: string) => !token || label.toLocaleLowerCase().includes(token)
    return {
      animation: false,
      tooltip: { trigger: "item", confine: true, formatter: (item: any) => {
        if (item.dataType === "edge") return item.data.derivation === "group_overlap" ? item.data.label + "<br/>共享：" + (item.data.shared_group_ids || []).join("、") : item.data.label + "<br/>规则：" + (item.data.rules || []).join("、")
        return item.data.name + "<br/>" + (item.data.relationship_status === "controlled_root" ? "基础基团根节点" : "名称规则已确认")
      } },
      legend: [{ data: ["基础基团", "名称规则已确认"] }],
      series: [{ type: "graph", layout: "force", roam: true, draggable: true,
        data: plottedNodes.map((node) => {
          const root = node.type === "functional_group"
          const matched = isMatch(node.label)
          return { id: node.id, name: node.label, category: root ? 0 : 1, symbol: root ? "roundRect" : "circle", symbolSize: root ? 40 : 9, label: { show: root || (matched && Boolean(token)), position: root ? "inside" : "right", color: root ? "#fff" : "#1e293b", fontSize: root ? 12 : 11, overflow: "truncate", width: 150 }, itemStyle: { color: root ? "#0f766e" : "#d97706", opacity: matched || !token ? 1 : 0.08 }, emphasis: { focus: "adjacency", label: { show: true } }, relationship_status: node.relationship_status }
        }),
        links: visibleEdges.map((edge) => ({ id: edge.id, source: edge.source, target: edge.target, relation_type: edge.relation_type, label: edge.label, derivation: edge.derivation, shared_group_ids: edge.shared_group_ids, rules: edge.rules, lineStyle: { color: edge.relation_type === "has_functional_group" ? "#0f766e" : "#94a3b8", width: edge.relation_type === "has_functional_group" ? 1.2 : 0.45, opacity: edge.relation_type === "has_functional_group" ? 0.42 : 0.12, curveness: edge.relation_type === "shares_functional_groups" ? 0.08 : 0 } })),
        categories: [{ name: "基础基团" }, { name: "名称规则已确认" }], force: { repulsion: 105, gravity: 0.015, edgeLength: [16, 95], friction: 0.65 }, emphasis: { focus: "adjacency" }
      }]
    }
  }, [plottedNodes, query.data, search, showSimilarity, showStructure])
  if (query.isLoading) return <LoadingBlock />
  if (query.error) return <ErrorBlock error={query.error} />
  const stats = query.data?.stats ?? {}
  return <div className="page-grid graph-layout"><section className="panel"><div className="panel-head"><div><h2>全局基团 - 物质关系图</h2><small>{query.data?.run_id} · 仅绘制具有基础基团关系的节点</small></div><Input.Search allowClear value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索基团或物质，图中高亮定位" style={{ width: 290 }} /></div><div className="panel-body"><p className="hierarchy-note">根节点为受控基础基团；实线是名称规则确认的“基团组成物质”关系，灰线是共享两个及以上基础基团的派生结构关联。待结构确认物质不参与力导向布局，列在右侧供继续审核。</p><Space wrap style={{ marginBottom: 12 }}><Checkbox checked={showStructure} onChange={(event) => setShowStructure(event.target.checked)}>显示基团组成关系</Checkbox><Checkbox checked={showSimilarity} onChange={(event) => setShowSimilarity(event.target.checked)}>显示物质结构关联</Checkbox><Tag color="gold">可缩放 / 拖拽 / 悬停查看规则</Tag></Space><ReactECharts option={option} style={{ height: 760 }} opts={{ renderer: "canvas" }} onEvents={{ click: (event: any) => event.dataType === "node" && event.data?.relationship_status !== "controlled_root" ? navigate("/materials/" + event.data.id) : undefined }} /></div></section><aside className="panel"><div className="panel-head"><h2>关系口径</h2><Tag color="cyan">全图</Tag></div><div className="panel-body"><Statistic title="基础基团根节点" value={stats.functional_groups ?? 0} /><Statistic title="入图物质节点" value={plottedNodes.filter((node) => node.type === "material").length} style={{ marginTop: 18 }} /><Statistic title="基团组成边" value={stats.material_group_edges ?? 0} style={{ marginTop: 18 }} /><Statistic title="物质结构关联边" value={stats.material_similarity_edges ?? 0} style={{ marginTop: 18 }} /><Divider plain>待结构确认物质 · {unresolved.length}</Divider><p className="hierarchy-note">未绘入图，避免游离节点拖慢布局；点击可进入物质详情。</p><List size="small" dataSource={unresolved} pagination={{ pageSize: 8, size: "small", showSizeChanger: false }} renderItem={(node) => <List.Item style={{ cursor: "pointer" }} onClick={() => navigate("/materials/" + node.id)}><span>{node.label}</span><Tag>待确认</Tag></List.Item>} /></div></aside></div>
}
