import { Checkbox, Divider, Input, List, Space, Statistic, Tag } from "antd"
import ReactECharts from "echarts-for-react"
import { useMemo, useRef } from "react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchMaterialRelationshipGraph } from "../api"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"
import type { MaterialRelationshipEdge, MaterialRelationshipNode } from "../types"

type Position = { x: number; y: number }

function normalizePositions(positions: Record<string, Position>, width = 1680, height = 980, padding = 80): Record<string, Position> {
  const pts = Object.values(positions)
  if (!pts.length) return positions
  const xs = pts.map((p) => p.x)
  const ys = pts.map((p) => p.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const spanX = Math.max(maxX - minX, 1)
  const spanY = Math.max(maxY - minY, 1)
  const scale = Math.min((width - padding * 2) / spanX, (height - padding * 2) / spanY)
  const next: Record<string, Position> = {}
  for (const [id, pos] of Object.entries(positions)) {
    next[id] = {
      x: padding + (pos.x - minX) * scale,
      y: padding + (pos.y - minY) * scale,
    }
  }
  return next
}

function placeAroundHub(hub: Position, count: number, index: number): Position {
  // Concentric rings with circumference-aware capacity so nodes stay readable.
  let remaining = index
  let ring = 0
  while (true) {
    const radius = 92 + ring * 46
    const capacity = Math.max(8, Math.floor((2 * Math.PI * radius) / 34))
    if (remaining < capacity) {
      const angle = (2 * Math.PI * remaining) / capacity - Math.PI / 2
      return {
        x: hub.x + Math.cos(angle) * radius,
        y: hub.y + Math.sin(angle) * radius,
      }
    }
    remaining -= capacity
    ring += 1
  }
}

function buildClusterLayout(nodes: MaterialRelationshipNode[], edges: MaterialRelationshipEdge[]): Record<string, Position> {
  const groups = nodes.filter((node) => node.type === "functional_group")
  const materials = nodes.filter((node) => node.type === "material")
  const membership = new Map<string, string[]>()
  for (const edge of edges) {
    if (edge.relation_type !== "has_functional_group") continue
    const list = membership.get(edge.target) ?? []
    list.push(edge.source)
    membership.set(edge.target, list)
  }

  const buckets = new Map<string, MaterialRelationshipNode[]>()
  const multi: MaterialRelationshipNode[] = []
  for (const material of materials) {
    const parents = membership.get(material.id) ?? []
    if (parents.length === 1) {
      const list = buckets.get(parents[0]) ?? []
      list.push(material)
      buckets.set(parents[0], list)
    } else if (parents.length > 1) {
      multi.push(material)
    }
  }

  const groupOrder = [...groups].sort((a, b) => {
    const ac = (buckets.get(a.id) ?? []).length
    const bc = (buckets.get(b.id) ?? []).length
    return bc - ac || a.label.localeCompare(b.label, "zh")
  })

  // Angular space proportional to cluster size so large hubs are not adjacent and cramped.
  const weights = groupOrder.map((group) => Math.max(1, (buckets.get(group.id) ?? []).length))
  const totalWeight = weights.reduce((sum, value) => sum + value, 0)
  const positions: Record<string, Position> = {}
  let angleCursor = -Math.PI / 2
  const hubRadius = 760

  groupOrder.forEach((group, index) => {
    const slice = (2 * Math.PI * weights[index]) / totalWeight
    const angle = angleCursor + slice / 2
    positions[group.id] = {
      x: Math.cos(angle) * hubRadius,
      y: Math.sin(angle) * hubRadius,
    }
    angleCursor += slice
  })

  for (const group of groupOrder) {
    const members = (buckets.get(group.id) ?? []).sort((a, b) => a.label.localeCompare(b.label, "zh"))
    const hub = positions[group.id]
    members.forEach((material, index) => {
      positions[material.id] = placeAroundHub(hub, members.length, index)
    })
  }

  // Multi-parent materials occupy a medium ring so they do not form a center pile.
  multi.sort((a, b) => a.label.localeCompare(b.label, "zh")).forEach((material, index) => {
    const parents = membership.get(material.id) ?? []
    const parentPositions = parents.map((id) => positions[id]).filter(Boolean)
    if (!parentPositions.length) {
      const angle = (2 * Math.PI * index) / Math.max(multi.length, 1) - Math.PI / 2
      positions[material.id] = { x: Math.cos(angle) * 220, y: Math.sin(angle) * 220 }
      return
    }
    const avgX = parentPositions.reduce((sum, pos) => sum + pos.x, 0) / parentPositions.length
    const avgY = parentPositions.reduce((sum, pos) => sum + pos.y, 0) / parentPositions.length
    const baseAngle = Math.atan2(avgY, avgX)
    const ring = Math.floor(index / 28)
    const inRing = index % 28
    const radius = 250 + ring * 42
    const angle = baseAngle + ((inRing - 13.5) / 28) * 1.1
    positions[material.id] = {
      x: Math.cos(angle) * radius * 0.55 + avgX * 0.45,
      y: Math.sin(angle) * radius * 0.55 + avgY * 0.45,
    }
  })

  return normalizePositions(positions)
}

export default function HierarchyPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [showStructure, setShowStructure] = useState(true)
  const [showSimilarity, setShowSimilarity] = useState(false)
  const chartRef = useRef<any>(null)
  const query = useQuery({ queryKey: ["material-relationship-graph"], queryFn: fetchMaterialRelationshipGraph })
  const allNodes = query.data?.nodes ?? []
  const unresolved = allNodes.filter((node) => node.relationship_status === "needs_structure_confirmation")
  const plottedNodes = allNodes.filter((node) => node.relationship_status !== "needs_structure_confirmation")
  const layoutKey = query.data?.layout_key ? "material-relationship-layout-v5:" + query.data.layout_key : null

  const positions = useMemo(() => {
    if (!query.data) return {} as Record<string, Position>
    if (layoutKey) {
      try {
        const cached = JSON.parse(localStorage.getItem(layoutKey) || "{}") as Record<string, Position>
        if (plottedNodes.length > 0 && plottedNodes.every((node) => cached[node.id])) return cached
      } catch {
        /* ignore broken cache */
      }
    }
    const next = buildClusterLayout(plottedNodes, query.data.edges ?? [])
    if (layoutKey && Object.keys(next).length === plottedNodes.length) {
      localStorage.setItem(layoutKey, JSON.stringify(next))
    }
    return next
  }, [layoutKey, plottedNodes, query.data])

  const option = useMemo(() => {
    const graph = query.data
    const token = search.trim().toLocaleLowerCase()
    const visibleEdges = (graph?.edges ?? []).filter((edge) => edge.relation_type === "has_functional_group" ? showStructure : showSimilarity)
    const isMatch = (label: string) => !token || label.toLocaleLowerCase().includes(token)
    return {
      animation: false,
      tooltip: {
        trigger: "item",
        confine: true,
        formatter: (item: any) => {
          if (item.dataType === "edge") {
            return item.data.derivation === "group_overlap"
              ? item.data.label + "<br/>共享：" + (item.data.shared_group_ids || []).join("、")
              : item.data.label + "<br/>规则：" + (item.data.rules || []).join("、")
          }
          return item.data.name + "<br/>" + (item.data.relationship_status === "controlled_root" ? "基础基团根节点" : "名称规则已确认")
        },
      },
      legend: [{ data: ["基础基团", "名称规则已确认"], bottom: 8 }],
      series: [{
        type: "graph",
        layout: "none",
        roam: true,
        draggable: true,
        zoom: 1,
        scaleLimit: { min: 0.15, max: 8 },
        left: 20,
        right: 20,
        top: 20,
        bottom: 40,
        data: plottedNodes.map((node) => {
          const root = node.type === "functional_group"
          const matched = isMatch(node.label)
          const pos = positions[node.id] || { x: 0, y: 0 }
          return {
            id: node.id,
            name: node.label,
            x: pos.x,
            y: pos.y,
            category: root ? 0 : 1,
            symbol: root ? "roundRect" : "circle",
            symbolSize: root ? 64 : 13,
            label: {
              show: root || (matched && Boolean(token)),
              position: root ? "inside" : "right",
              color: root ? "#fff" : "#0f172a",
              fontSize: root ? 12 : 11,
              fontWeight: root ? 600 : 400,
              overflow: "truncate",
              width: root ? 78 : 120,
            },
            itemStyle: {
              color: root ? "#0f766e" : "#d97706",
              borderColor: root ? "#115e59" : "#b45309",
              borderWidth: root ? 1 : 0.6,
              opacity: matched || !token ? 1 : 0.08,
              shadowBlur: root ? 10 : 0,
              shadowColor: "rgba(15, 118, 110, 0.28)",
            },
            emphasis: { focus: "adjacency", label: { show: true } },
            relationship_status: node.relationship_status,
          }
        }),
        links: visibleEdges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          relation_type: edge.relation_type,
          label: edge.label,
          derivation: edge.derivation,
          shared_group_ids: edge.shared_group_ids,
          rules: edge.rules,
          lineStyle: {
            color: edge.relation_type === "has_functional_group" ? "#0f766e" : "#cbd5e1",
            width: edge.relation_type === "has_functional_group" ? 1.2 : 0.35,
            opacity: edge.relation_type === "has_functional_group" ? 0.38 : 0.07,
            curveness: edge.relation_type === "shares_functional_groups" ? 0.12 : 0.04,
          },
        })),
        categories: [{ name: "基础基团" }, { name: "名称规则已确认" }],
        emphasis: { focus: "adjacency", lineStyle: { width: 2.2, opacity: 0.9 } },
      }],
    }
  }, [plottedNodes, positions, query.data, search, showSimilarity, showStructure])

  if (query.isLoading) return <LoadingBlock />
  if (query.error) return <ErrorBlock error={query.error} />
  const stats = query.data?.stats ?? {}
  const plottedMaterialCount = plottedNodes.filter((node) => node.type === "material").length
  const usedCache = Boolean(layoutKey && plottedNodes.every((node) => {
    try {
      const cached = JSON.parse(localStorage.getItem(layoutKey) || "{}")
      return Boolean(cached[node.id])
    } catch {
      return false
    }
  }))

  return (
    <div className="page-grid graph-layout">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>全局基团 - 物质关系图</h2>
            <small>{query.data?.run_id} · 基团枢纽聚类布局 · 节点按簇分散排布</small>
          </div>
          <Input.Search allowClear value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索基团或物质，图中高亮定位" style={{ width: 290 }} />
        </div>
        <div className="panel-body">
          <p className="hierarchy-note">
            16 个基础基团按簇规模分配圆周空间；物质围绕主归属基团分层排布，避免挤成对角线。
            灰线是共享两个及以上基础基团的派生关联，默认关闭且不参与定位。可缩放/拖拽查看局部。
          </p>
          <Space wrap style={{ marginBottom: 12 }}>
            <Checkbox checked={showStructure} onChange={(event) => setShowStructure(event.target.checked)}>显示基团组成关系</Checkbox>
            <Checkbox checked={showSimilarity} onChange={(event) => setShowSimilarity(event.target.checked)}>显示物质结构关联</Checkbox>
            <Tag color={usedCache ? "green" : "gold"}>{usedCache ? "已复用聚类布局缓存" : "已生成聚类布局并缓存"}</Tag>
          </Space>
          <ReactECharts
            ref={chartRef}
            option={option}
            style={{ height: 960 }}
            opts={{ renderer: "canvas" }}
            onEvents={{
              click: (event: any) => event.dataType === "node" && event.data?.relationship_status !== "controlled_root"
                ? navigate("/materials/" + event.data.id)
                : undefined,
            }}
          />
        </div>
      </section>
      <aside className="panel">
        <div className="panel-head"><h2>关系口径</h2><Tag color="cyan">全图</Tag></div>
        <div className="panel-body">
          <Statistic title="基础基团根节点" value={stats.functional_groups ?? 0} />
          <Statistic title="入图物质节点" value={plottedMaterialCount} style={{ marginTop: 18 }} />
          <Statistic title="基团组成边" value={stats.material_group_edges ?? 0} style={{ marginTop: 18 }} />
          <Statistic title="物质结构关联边" value={stats.material_similarity_edges ?? 0} style={{ marginTop: 18 }} />
          <Divider plain>待结构确认物质 · {unresolved.length}</Divider>
          <p className="hierarchy-note">未绘入图，避免游离节点拖慢布局；点击可进入物质详情。</p>
          <List
            size="small"
            dataSource={unresolved}
            pagination={{ pageSize: 8, size: "small", showSizeChanger: false }}
            renderItem={(node) => (
              <List.Item style={{ cursor: "pointer" }} onClick={() => navigate("/materials/" + node.id)}>
                <span>{node.label}</span>
                <Tag>待确认</Tag>
              </List.Item>
            )}
          />
        </div>
      </aside>
    </div>
  )
}
