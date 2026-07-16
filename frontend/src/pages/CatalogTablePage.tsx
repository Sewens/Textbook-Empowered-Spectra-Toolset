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
  const [strength, setStrength] = useState<"all" | "high" | "medium">("all")
  const navigate = useNavigate()
  const request = useQuery<any[]>({
    queryKey: ["catalog", mode, query, scope, strength],
    queryFn: () => mode === "spectrum"
      ? fetchCatalogSpectra(scope === "all" ? undefined : scope, query || undefined)
      : mode === "evidence"
        ? fetchCatalogEvidence(query || undefined, strength === "all" ? undefined : strength)
        : fetchCatalogEntities(mode, query || undefined),
  })
  if (request.isLoading) return <LoadingBlock />
  if (request.error) return <ErrorBlock error={request.error} />
  const rows = request.data ?? []
  const spectrumColumns = [
    { title: "谱图 ID", dataIndex: "spectrum_id", ellipsis: true },
    { title: "物质", render: (_: unknown, row: any) => row.payload?.compound_name_zh || row.payload?.compound_name_en || row.material_id || "未关联物质", ellipsis: true },
    { title: "图题 / 说明", render: (_: unknown, row: any) => row.payload?.figure_caption || row.technique || "-", ellipsis: true },
    { title: "图片", render: (_: unknown, row: any) => row.image_url ? <Tag color="green">可显示</Tag> : <Tag>无图像</Tag>, width: 100 },
    { title: "数据分区", dataIndex: "source_scope", width: 130, render: (value: string) => <Tag color={value === "nist" ? "gold" : "blue"}>{value}</Tag> },
    { title: "状态", dataIndex: "review_status", width: 120 },
  ]
  const evidenceColumns = [
    { title: "物质", render: (_: unknown, row: any) => row.material_name || row.payload?.material_name || "-", width: 160, ellipsis: true },
    { title: "谱图", render: (_: unknown, row: any) => row.spectrum_id || row.payload?.spectrum_id || "-", width: 220, ellipsis: true },
    { title: "支撑强度", render: (_: unknown, row: any) => {
      const value = row.support_strength || row.payload?.support_strength
      return <Tag color={value === "high" ? "green" : value === "medium" ? "gold" : "default"}>{value || "-"}</Tag>
    }, width: 110 },
    { title: "证据类型", render: (_: unknown, row: any) => <Tag>{row.evidence_type || "-"}</Tag>, width: 110 },
    { title: "教材", render: (_: unknown, row: any) => row.book || row.payload?.book || "-", width: 220, ellipsis: true },
    { title: "页码", render: (_: unknown, row: any) => row.page ?? row.payload?.locator?.pdf_page ?? "-", width: 80 },
    { title: "图片", render: (_: unknown, row: any) => (row.image_paths?.length || row.payload?.image_paths?.length) ? <Tag color="green">有图</Tag> : <Tag>无图</Tag>, width: 80 },
    { title: "支撑原文", render: (_: unknown, row: any) => row.text || "-", ellipsis: true },
  ]
  const genericColumns = [
    { title: "实体", render: (_: unknown, row: any) => row.name || row.evidence_id, ellipsis: true },
    { title: "类别", render: (_: unknown, row: any) => <Tag>{row.entity_type || row.evidence_type}</Tag>, width: 120 },
    { title: "数据分区", dataIndex: "source_scope", width: 120, render: (value: string) => <Tag color={value === "nist" ? "gold" : "blue"}>{value}</Tag> },
    { title: "状态", dataIndex: "review_status", width: 150 },
    { title: "内容", render: (_: unknown, row: any) => row.text || JSON.stringify(row.payload || {}), ellipsis: true },
  ]
  const columns = mode === "spectrum" ? spectrumColumns : mode === "evidence" ? evidenceColumns : genericColumns
  return (
    <div className="panel full-panel">
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {mode === "evidence" ? <small>物质—谱图支撑证据 · 优先展示图/表中直接点名物质的教材原文</small> : null}
        </div>
        <div className="inline-actions">
          {mode === "evidence" ? (
            <Segmented
              value={strength}
              onChange={(value) => setStrength(value as "all" | "high" | "medium")}
              options={[
                { label: "全部强度", value: "all" },
                { label: "高置信", value: "high" },
                { label: "中置信", value: "medium" },
              ]}
            />
          ) : (
            <Segmented
              value={scope}
              onChange={(value) => setScope(value as "all" | "textbook" | "nist")}
              options={[
                { label: "全部", value: "all" },
                { label: "教材 accepted", value: "textbook" },
                { label: "NIST staging", value: "nist" },
              ]}
            />
          )}
          <Input.Search allowClear placeholder={mode === "evidence" ? "物质、谱图、教材或证据原文" : "ID、名称、字段或证据文本"} onSearch={setQuery} />
        </div>
      </div>
      <div className="panel-body flush">
        <Table<any>
          size="small"
          rowKey={(row) => row.entity_id || row.spectrum_id || row.evidence_id}
          dataSource={rows}
          pagination={{ pageSize: 20 }}
          onRow={(row) => {
            if (mode === "spectrum" && row.material_id) {
              return { onClick: () => navigate("/materials/" + row.material_id), style: { cursor: "pointer" } }
            }
            if (mode === "evidence" && row.material_id) {
              return { onClick: () => navigate("/materials/" + row.material_id), style: { cursor: "pointer" } }
            }
            return {}
          }}
          columns={columns}
        />
      </div>
    </div>
  )
}
