import { Input, Table, Tag } from "antd"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogTerms } from "../api"
import type { KnowledgeTerm } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

export default function TermsPage({ groupsOnly = false }: { groupsOnly?: boolean }) {
  const [query, setQuery] = useState("")
  const navigate = useNavigate()
  const termsQuery = useQuery({ queryKey: ["catalog-terms", query], queryFn: () => fetchCatalogTerms(query || undefined) })
  if (termsQuery.isLoading) return <LoadingBlock />
  if (termsQuery.error) return <ErrorBlock error={termsQuery.error} />
  const rows = (termsQuery.data ?? []).filter((term) => !groupsOnly || term.term_type === "group")
  return <div className="panel full-panel"><div className="panel-head"><h2>{groupsOnly ? "基础基团与谱学卡片" : "基础术语库"}</h2><Input.Search allowClear placeholder="术语、官能团、振动或效应关键词" onSearch={setQuery} /></div><div className="panel-body flush"><Table<KnowledgeTerm> size="small" rowKey="term_id" dataSource={rows} pagination={{ pageSize: 18 }} onRow={(row) => ({ onClick: () => row.term_type === "group" && navigate("/groups/" + row.term_id) })} columns={[{ title: "术语", dataIndex: "name", width: 220 }, { title: "类型", dataIndex: "term_type", width: 120, render: (value) => <Tag color={value === "group" ? "blue" : "cyan"}>{value === "group" ? "基础基团" : "抽取概念"}</Tag> }, { title: "英文 / 别名", render: (_, row) => row.payload.name_en || row.payload.names?.en || row.payload.mention || "-", width: 240, ellipsis: true }, { title: "分类", render: (_, row) => <Tag>{row.payload.concept_type || row.payload.group?.group_class || "functional_group"}</Tag>, width: 160 }, { title: "定义或说明", render: (_, row) => row.payload.definition || row.payload.textbook_definitions?.[0]?.original_quote || row.payload.textbook_description || "历史参考卡片；点击可查看关联物质和谱图。", ellipsis: true }]} /></div></div>
}
