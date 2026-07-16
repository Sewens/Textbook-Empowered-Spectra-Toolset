import { Drawer, Input, List, Table, Tag, Typography } from "antd"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogTerm, fetchCatalogTerms } from "../api"
import type { KnowledgeTerm, TerminologyDetail } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

const statusLabels: Record<string, string> = { candidate_needs_review: "待人工审核", accepted: "已确认", rejected: "已排除" }

export default function TermsPage({ groupsOnly = false }: { groupsOnly?: boolean }) {
  const [query, setQuery] = useState("")
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const navigate = useNavigate()
  const termsQuery = useQuery({ queryKey: ["catalog-terms", query], queryFn: () => fetchCatalogTerms(query || undefined) })
  const detailQuery = useQuery({ queryKey: ["catalog-term", selectedId], queryFn: () => fetchCatalogTerm(selectedId!), enabled: Boolean(selectedId) })
  if (termsQuery.isLoading) return <LoadingBlock />
  if (termsQuery.error) return <ErrorBlock error={termsQuery.error} />
  const rows = (termsQuery.data ?? []).filter((term) => !groupsOnly || term.term_type === "group")
  return <div className="panel full-panel">
    <div className="panel-head"><div><h2>{groupsOnly ? "基础基团与谱学卡片" : "基础术语库"}</h2><small>唯一术语实体；教材来源、原始表述与证据分别保留</small></div><Input.Search allowClear placeholder="术语、别名、概念类别或教材表述" onSearch={setQuery} /></div>
    <div className="panel-body flush"><Table<KnowledgeTerm> size="small" rowKey="term_id" dataSource={rows} pagination={{ pageSize: 18 }} onRow={(row) => ({ onClick: () => row.term_type === "group" ? navigate("/groups/" + row.term_id) : setSelectedId(row.term_id) })} columns={[
      { title: "术语", dataIndex: "name", width: 220 },
      { title: "类型", dataIndex: "term_type", width: 110, render: (value) => <Tag color={value === "group" ? "blue" : "cyan"}>{value === "group" ? "基础基团" : "基础术语"}</Tag> },
      { title: "英文 / 原始表述", render: (_, row) => row.payload.preferred_name?.en || row.payload.all_source_forms?.slice(0, 2).join("；") || "-", width: 260, ellipsis: true },
      { title: "概念类别", render: (_, row) => <Tag>{row.payload.concept_type || "-"}</Tag>, width: 170 },
      { title: "教材来源", render: (_, row) => <Tag color="geekblue">{row.payload.source_book_count ?? 0} 本</Tag>, width: 110 },
      { title: "状态", render: (_, row) => <Tag color={row.payload.status === "accepted" ? "green" : "orange"}>{statusLabels[row.payload.status ?? ""] || row.payload.status || "待审核"}</Tag>, width: 120 },
      { title: "证据", render: (_, row) => row.payload.evidence_count ?? 0, width: 80 },
    ]} /></div>
    <Drawer title={detailQuery.data?.name || "术语来源详情"} open={Boolean(selectedId)} onClose={() => setSelectedId(null)} width={620}>
      {detailQuery.isLoading ? <LoadingBlock /> : detailQuery.error ? <ErrorBlock error={detailQuery.error} /> : detailQuery.data ? <TermDetail detail={detailQuery.data} /> : null}
    </Drawer>
  </div>
}

function TermDetail({ detail }: { detail: TerminologyDetail }) {
  return <div className="term-detail"><Typography.Paragraph type="secondary">该术语已去重为一个实体；以下教材来源、断言和证据不做跨书合并。</Typography.Paragraph><List size="small" header={<strong>教材来源（{detail.source_records?.length ?? 0}）</strong>} dataSource={detail.source_records ?? []} renderItem={(source) => <List.Item><div><strong>{source.book || source.source_id}</strong><br /><Typography.Text type="secondary">{(source.source_forms ?? []).join("；")}</Typography.Text><br /><Typography.Text type="secondary">出现 {source.mention_count ?? 0} 次 · 证据 {source.evidence_ids?.length ?? 0} 条</Typography.Text></div></List.Item>} /><List size="small" header={<strong>来源断言（{detail.source_specific_claims?.length ?? 0}）</strong>} dataSource={detail.source_specific_claims ?? []} renderItem={(claim) => <List.Item><div><Tag>{claim.book || claim.source_id}</Tag>{claim.predicate}<br /><Typography.Text>{claim.object_text || claim.object?.text || "-"}</Typography.Text></div></List.Item>} /><List size="small" header={<strong>证据片段（{detail.evidence_spans?.length ?? 0}）</strong>} dataSource={(detail.evidence_spans ?? []).slice(0, 30)} renderItem={(evidence) => <List.Item><Typography.Paragraph ellipsis={{ rows: 3, expandable: true }}>{evidence.text_original || evidence.text || "-"}</Typography.Paragraph></List.Item>} /></div>
}
