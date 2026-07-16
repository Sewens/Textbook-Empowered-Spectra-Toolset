import { Descriptions, Table, Tabs, Tag } from "antd"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogGroup } from "../api"
import type { CatalogEntity, KnowledgeSpectrum } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

export default function GroupDetailPage() {
  const { groupId = "" } = useParams()
  const navigate = useNavigate()
  const query = useQuery({ queryKey: ["catalog-group", groupId], queryFn: () => fetchCatalogGroup(groupId), enabled: Boolean(groupId) })
  if (query.isLoading) return <LoadingBlock />
  if (query.error || !query.data) return <ErrorBlock error={query.error ?? new Error("基团不存在")} />
  const group = query.data
  const payload: any = group.payload
  return <div className="group-detail-v2"><section className="panel"><div className="panel-head"><div><h2>{group.name}</h2><small>{groupId} · historical reference card</small></div><Tag color="blue">基础基团</Tag></div><div className="panel-body"><Descriptions bordered size="small" column={2}><Descriptions.Item label="English">{payload.name_en || payload.group?.canonical_name_en || "-"}</Descriptions.Item><Descriptions.Item label="Formula">{payload.chemical_formula || payload.group?.formula_fragment || "-"}</Descriptions.Item><Descriptions.Item label="SMARTS">{payload.smarts || "-"}</Descriptions.Item><Descriptions.Item label="关联物质">{group.materials.length}</Descriptions.Item></Descriptions></div></section><section className="panel"><div className="panel-head"><h2>基团知识与实例证据</h2><small>{group.spectra.length} 条参考谱图</small></div><div className="panel-body"><Tabs items={[{ key: "materials", label: "关联物质", children: <Table<CatalogEntity> rowKey="entity_id" dataSource={group.materials} size="small" pagination={{ pageSize: 10 }} onRow={(row) => ({ onClick: () => navigate("/materials/" + row.entity_id) })} columns={[{ title: "物质", dataIndex: "name" }, { title: "分子式", render: (_, row) => row.payload.formula || "-" }, { title: "SMILES", render: (_, row) => row.payload.smiles || "-", ellipsis: true }]} /> }, { key: "spectra", label: "谱图与峰特性", children: <div className="spectrum-grid">{group.spectra.map((spectrum: KnowledgeSpectrum) => <article className="spectrum-card" key={spectrum.spectrum_id}>{spectrum.image_url ? <img src={spectrum.image_url} alt={spectrum.spectrum_id} /> : <div className="image-empty">无可公开图像</div>}<h3>{spectrum.payload.figure_caption || spectrum.spectrum_id}</h3><Table size="small" pagination={false} rowKey={(peak, index) => index ?? 0} dataSource={spectrum.peaks} columns={[{ title: "峰位 / cm-1", dataIndex: "measured_wavenumber", width: 130 }, { title: "归属", dataIndex: "peak_assignment" }]} /></article>)}</div> }, { key: "vibration", label: "振动模板", children: <Table size="small" rowKey="vibration_id" dataSource={group.vibrations} pagination={{ pageSize: 12 }} columns={[{ title: "模式", dataIndex: "symbol" }, { title: "范围 / cm-1", render: (_, row) => row.base_wavenumber_range?.join(" - ") || "-" }, { title: "说明", dataIndex: "textbook_description", ellipsis: true }]} /> }]} /></div></section></div>
}
