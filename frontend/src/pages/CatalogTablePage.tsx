import { Input, Segmented, Table, Tag } from "antd"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogEntities, fetchCatalogEvidence, fetchCatalogSpectra } from "../api"
import type { CatalogEntityType } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

type Mode = CatalogEntityType | "spectrum" | "evidence"

export default function CatalogTablePage({ mode, title }: { mode: Mode; title: string }) {
  const [query, setQuery] = useState("")
  const [scope, setScope] = useState<"all" | "textbook" | "nist">("all")
  const navigate = useNavigate()
  const request = useQuery<any[]>({ queryKey: ["catalog", mode, query, scope], queryFn: () => mode === "spectrum" ? fetchCatalogSpectra(scope === "all" ? undefined : scope, query || undefined) : mode === "evidence" ? fetchCatalogEvidence(query || undefined) : fetchCatalogEntities(mode, query || undefined) })
  if (request.isLoading) return <LoadingBlock />
  if (request.error) return <ErrorBlock error={request.error} />
  const rows = request.data ?? []
  const spectrumColumns = [{ title: "谱图 ID", dataIndex: "spectrum_id", ellipsis: true }, { title: "物质", render: (_: unknown, row: any) => row.payload?.compound_name_zh || row.payload?.compound_name_en || row.material_id || "未关联物质", ellipsis: true }, { title: "图题 / 说明", render: (_: unknown, row: any) => row.payload?.figure_caption || row.technique || "-", ellipsis: true }, { title: "图片", render: (_: unknown, row: any) => row.image_url ? <Tag color="green">可显示</Tag> : <Tag>无图像</Tag>, width: 100 }, { title: "数据分区", dataIndex: "source_scope", width: 130, render: (value: string) => <Tag color={value === "nist" ? "gold" : "blue"}>{value}</Tag> }, { title: "状态", dataIndex: "review_status", width: 120 }]
  const genericColumns = [{ title: "实体", render: (_: unknown, row: any) => row.name || row.evidence_id, ellipsis: true }, { title: "类别", render: (_: unknown, row: any) => <Tag>{row.entity_type || row.evidence_type}</Tag>, width: 120 }, { title: "数据分区", dataIndex: "source_scope", width: 120, render: (value: string) => <Tag color={value === "nist" ? "gold" : "blue"}>{value}</Tag> }, { title: "状态", dataIndex: "review_status", width: 150 }, { title: "内容", render: (_: unknown, row: any) => row.text || JSON.stringify(row.payload || {}), ellipsis: true }]
  return <div className="panel full-panel"><div className="panel-head"><h2>{title}</h2><div className="inline-actions"><Segmented value={scope} onChange={(value) => setScope(value as "all" | "textbook" | "nist")} options={[{ label: "全部", value: "all" }, { label: "教材 accepted", value: "textbook" }, { label: "NIST staging", value: "nist" }]} /><Input.Search allowClear placeholder="ID、名称、字段或证据文本" onSearch={setQuery} /></div></div><div className="panel-body flush"><Table<any> size="small" rowKey={(row) => row.entity_id || row.spectrum_id || row.evidence_id} dataSource={rows} pagination={{ pageSize: 20 }} onRow={(row) => mode === "spectrum" && row.material_id ? { onClick: () => navigate("/materials/" + row.material_id), style: { cursor: "pointer" } } : {}} columns={mode === "spectrum" ? spectrumColumns : genericColumns} /></div></div>
}
