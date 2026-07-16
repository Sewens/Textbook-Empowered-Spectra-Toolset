import { useMemo, useState } from "react"
import { Alert, Descriptions, Drawer, Input, Select, Statistic, Table, Tabs, Tag } from "antd"
import { useQuery } from "@tanstack/react-query"

import { fetchTextbookInventory, fetchTextbookInventoryBooks, fetchTextbookInventoryDetail, fetchTextbookInventoryOverview } from "../api"
import type { TextbookInventoryDetail, TextbookInventoryKind, TextbookInventoryRow } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

const labels: Record<TextbookInventoryKind, string> = { groups: "关联基团", materials: "物质", spectra: "关联谱图" }

function assetUrl(book: string, path: string) {
  return "/api/catalog/textbook-inventory/assets/" + encodeURIComponent(book) + "/" + path.split("/").map(encodeURIComponent).join("/")
}

export default function MaterialsPage() {
  const [kind, setKind] = useState<TextbookInventoryKind>("materials")
  const [query, setQuery] = useState("")
  const [book, setBook] = useState<string | undefined>()
  const [selected, setSelected] = useState<TextbookInventoryDetail | null>(null)
  const overview = useQuery({ queryKey: ["textbook-inventory-overview"], queryFn: fetchTextbookInventoryOverview })
  const books = useQuery({ queryKey: ["textbook-inventory-books"], queryFn: fetchTextbookInventoryBooks })
  const rows = useQuery({ queryKey: ["textbook-inventory", kind, query, book], queryFn: () => fetchTextbookInventory(kind, query || undefined, book) })
  const detail = useQuery({ queryKey: ["textbook-inventory-detail", kind, selected?.candidate_id], queryFn: () => fetchTextbookInventoryDetail(kind, selected!.candidate_id), enabled: Boolean(selected) })
  const columns = useMemo(() => {
    const common = [{ title: "候选名称", dataIndex: "name", ellipsis: true }, { title: "教材数", dataIndex: "book_count", width: 80 }, { title: "来源记录", dataIndex: "source_count", width: 90 }]
    if (kind === "groups") return [...common, { title: "提及数", dataIndex: "mention_count", width: 80 }, { title: "谱图", dataIndex: "spectrum_count", width: 70 }]
    if (kind === "materials") return [...common, { title: "提及数", dataIndex: "mention_count", width: 80 }, { title: "关联基团", dataIndex: "group_count", width: 90 }, { title: "谱图", dataIndex: "spectrum_count", width: 70 }]
    return [...common, { title: "材料", dataIndex: "material_count", width: 70 }, { title: "特征", dataIndex: "feature_count", width: 70 }, { title: "图片", dataIndex: "image_count", width: 70 }]
  }, [kind])
  if (overview.isLoading || rows.isLoading) return <LoadingBlock />
  if (overview.error || rows.error) return <ErrorBlock error={overview.error ?? rows.error} />
  const data = overview.data
  if (!data?.available) return <Alert type="warning" message="教材 staging 目录不可用" description="请检查 0714谱构效数据/material_spectra 的配置路径。" />
  return <div className="panel full-panel">
    <div className="panel-head"><div><h2>物质谱图</h2><small>{data.run_id} · {data.book_count}本教材 · 精筛候选</small></div><Tag color="warning">candidate_needs_review</Tag></div>
    <div className="panel-body">
      <Alert type="info" showIcon message="本页以物质为中心展示基团、特性、谱图和教材证据；候选仍保留审核状态，原始来源和图片路径可在详情中查看。" />
      <div className="stat-grid" style={{ margin: "18px 0" }}>
        <Statistic title="教材" value={data.book_count} />
        <Statistic title="基团候选" value={data.unique_catalogs.groups} />
        <Statistic title="化合物候选" value={data.unique_catalogs.materials} />
        <Statistic title="谱图候选" value={data.unique_catalogs.spectra} />
      </div>
      <Tabs activeKey={kind} onChange={(key) => { setKind(key as TextbookInventoryKind); setSelected(null) }} items={(Object.keys(labels) as TextbookInventoryKind[]).map((key) => ({ key, label: labels[key] }))} />
      <div className="panel-head" style={{ padding: "12px 0" }}><Input.Search allowClear placeholder="候选名称、教材或上下文" onSearch={setQuery} style={{ maxWidth: 420 }} /><Select allowClear showSearch placeholder="按教材筛选" value={book} onChange={setBook} options={(books.data ?? []).map((item) => ({ label: item, value: item }))} style={{ minWidth: 280 }} /></div>
      <Table<TextbookInventoryRow> rowKey="candidate_id" size="small" dataSource={rows.data ?? []} columns={[...columns, { title: "状态", dataIndex: "review_status", width: 150, render: () => <Tag color="orange">待审核</Tag> }]} pagination={{ pageSize: 18 }} onRow={(row) => ({ onClick: () => setSelected(row as TextbookInventoryDetail) })} />
    </div>
    <Drawer title={selected ? `${labels[kind]} · ${selected.name}` : "候选详情"} width={720} open={Boolean(selected)} onClose={() => setSelected(null)}>
      {detail.isLoading && <LoadingBlock />}
      {detail.data && <><Descriptions bordered size="small" column={1}><Descriptions.Item label="候选 ID">{detail.data.candidate_id}</Descriptions.Item><Descriptions.Item label="审核状态"><Tag color="orange">{detail.data.review_status}</Tag></Descriptions.Item><Descriptions.Item label="来源教材">{detail.data.books.join("；")}</Descriptions.Item><Descriptions.Item label="来源记录数">{detail.data.source_count}</Descriptions.Item></Descriptions><h3 style={{ marginTop: 20 }}>教材来源与原始候选</h3>{detail.data.source_records.map((source, index) => <div key={index}><pre style={{ whiteSpace: "pre-wrap", background: "#f7f4ed", padding: 12, marginBottom: 10 }}>{JSON.stringify(source, null, 2)}</pre>{(source.image_candidates ?? []).map((image: any) => image.source_image_path && <img key={image.image_candidate_id} src={assetUrl(source.book ?? "", image.source_image_path)} alt={image.caption_or_nearby_context ?? image.image_candidate_id} style={{ maxWidth: "100%", marginBottom: 16 }} />)}</div>)}</>}
    </Drawer>
  </div>
}
