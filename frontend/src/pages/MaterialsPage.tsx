import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Alert, Input, Select, Statistic, Table, Tabs, Tag } from "antd"
import { useQuery } from "@tanstack/react-query"

import { fetchTextbookInventory, fetchTextbookInventoryBooks, fetchTextbookInventoryOverview } from "../api"
import type { TextbookInventoryKind, TextbookInventoryRow } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

const labels: Record<TextbookInventoryKind, string> = { groups: "关联基团", materials: "物质", spectra: "关联谱图" }

export default function MaterialsPage() {
  const [kind, setKind] = useState<TextbookInventoryKind>("materials")
  const [query, setQuery] = useState("")
  const [book, setBook] = useState<string | undefined>()
  const navigate = useNavigate()
  const overview = useQuery({ queryKey: ["textbook-inventory-overview"], queryFn: fetchTextbookInventoryOverview })
  const books = useQuery({ queryKey: ["textbook-inventory-books"], queryFn: fetchTextbookInventoryBooks })
  const rows = useQuery({ queryKey: ["textbook-inventory", kind, query, book], queryFn: () => fetchTextbookInventory(kind, query || undefined, book) })
  const columns = useMemo(() => {
    const common = [{ title: "候选名称", dataIndex: "name", ellipsis: true }, { title: "教材数", dataIndex: "book_count", width: 80 }, { title: "来源记录", dataIndex: "source_count", width: 90 }]
    if (kind === "groups") return [...common, { title: "提及数", dataIndex: "mention_count", width: 80 }, { title: "谱图", dataIndex: "spectrum_count", width: 70 }]
    if (kind === "materials") return [...common, { title: "提及数", dataIndex: "mention_count", width: 80 }, { title: "关联基团", dataIndex: "group_count", width: 90 }, { title: "谱图", dataIndex: "spectrum_count", width: 70 }]
    return [...common, { title: "材料", dataIndex: "material_count", width: 70 }, { title: "特征", dataIndex: "feature_count", width: 70 }, { title: "图片", dataIndex: "image_count", width: 70 }]
  }, [kind])
  if (overview.isLoading || rows.isLoading) return <LoadingBlock />
  if (overview.error || rows.error) return <ErrorBlock error={overview.error ?? rows.error} />
  const data = overview.data
  if (!data?.available) return <Alert type="warning" message="教材精筛物质目录不可用" description="请检查 0714谱构效数据/material_spectra_accepted 的配置路径。" />
  return <div className="panel full-panel">
    <div className="panel-head"><div><h2>物质谱图</h2><small>{data.run_id} · {data.book_count}本教材 · 精筛物质候选（图表直接命名证据）</small></div><Tag color="warning">precision_screened_needs_review</Tag></div>
    <div className="panel-body">
      <Alert type="info" showIcon message="本页以物质为中心展示关联基团、谱图和教材证据；候选状态和原始来源均保留。" />
      <div className="stat-grid" style={{ margin: "18px 0" }}>
        <Statistic title="教材" value={data.book_count} />
        <Statistic title="基团候选" value={data.unique_catalogs.groups} />
        <Statistic title="精筛物质" value={data.unique_catalogs.materials} />
        <Statistic title="谱图候选" value={data.unique_catalogs.spectra} />
      </div>
      <Tabs activeKey={kind} onChange={(key) => setKind(key as TextbookInventoryKind)} items={(Object.keys(labels) as TextbookInventoryKind[]).map((key) => ({ key, label: labels[key] }))} />
      <div className="panel-head" style={{ padding: "12px 0" }}><Input.Search allowClear placeholder="候选名称、教材或上下文" onSearch={setQuery} style={{ maxWidth: 420 }} /><Select allowClear showSearch placeholder="按教材筛选" value={book} onChange={setBook} options={(books.data ?? []).map((item) => ({ label: item, value: item }))} style={{ minWidth: 280 }} /></div>
      <Table<TextbookInventoryRow> rowKey="candidate_id" size="small" dataSource={rows.data ?? []} columns={[...columns, { title: "状态", dataIndex: "review_status", width: 150, render: () => <Tag color="orange">待审核</Tag> }]} pagination={{ pageSize: 18 }} onRow={(row) => kind === "groups" ? {} : { onClick: () => navigate(kind === "materials" ? "/materials/" + row.candidate_id : "/spectra/" + row.candidate_id), style: { cursor: "pointer" } }} />
    </div>
  </div>
}
