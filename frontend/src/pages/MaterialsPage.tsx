import { Input, Table, Tag } from "antd"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchReferenceMaterials } from "../api"
import type { CatalogEntity } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

export default function MaterialsPage() {
  const [query, setQuery] = useState("")
  const navigate = useNavigate()
  const data = useQuery({ queryKey: ["reference-materials", query], queryFn: () => fetchReferenceMaterials(query || undefined) })
  if (data.isLoading) return <LoadingBlock />
  if (data.error) return <ErrorBlock error={data.error} />
  const rows = data.data ?? []
  return <div className="panel full-panel"><div className="panel-head"><h2>物质信息主页</h2><Input.Search allowClear placeholder="物质名、分子式、SMILES 或编号" onSearch={setQuery} /></div><div className="panel-body flush"><Table<CatalogEntity> rowKey="entity_id" dataSource={rows} size="small" pagination={{ pageSize: 18 }} onRow={(row) => ({ onClick: () => navigate("/materials/" + row.entity_id) })} columns={[{ title: "物质", dataIndex: "name", width: 220 }, { title: "分子式", render: (_, row) => row.payload.formula || row.payload.molecular_formula || "-", width: 130 }, { title: "SMILES", render: (_, row) => row.payload.smiles || "-", ellipsis: true }, { title: "来源", dataIndex: "source_scope", width: 150, render: (value) => <Tag color="blue">{value === "legacy_reference" ? "基础参考库" : value}</Tag> }, { title: "操作", width: 100, render: (_, row) => <Tag color="green">查看情报</Tag> }]} /></div></div>
}
