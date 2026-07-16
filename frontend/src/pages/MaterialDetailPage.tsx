import { Descriptions, Table, Tag } from "antd"
import { useNavigate, useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogMaterial } from "../api"
import type { KnowledgeSpectrum } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

export default function MaterialDetailPage() {
  const { materialId = "" } = useParams()
  const navigate = useNavigate()
  const query = useQuery({ queryKey: ["catalog-material", materialId], queryFn: () => fetchCatalogMaterial(materialId), enabled: Boolean(materialId) })
  if (query.isLoading) return <LoadingBlock />
  if (query.error || !query.data) return <ErrorBlock error={query.error ?? new Error("物质不存在")} />
  const material = query.data
  const payload: any = material.payload
  return <div className="group-detail-v2"><section className="panel"><div className="panel-head"><div><h2>{material.name}</h2><small>{material.entity_id}</small></div><Tag color="green">物质实体</Tag></div><div className="panel-body"><Descriptions bordered size="small" column={2}><Descriptions.Item label="分子式">{payload.formula || payload.molecular_formula || "-"}</Descriptions.Item><Descriptions.Item label="SMILES">{payload.smiles || "-"}</Descriptions.Item><Descriptions.Item label="关联基团" span={2}>{material.groups.map((group) => <Tag key={group.group_id} color="blue" onClick={() => navigate("/groups/" + group.group_id)}>{group.name}</Tag>)}</Descriptions.Item></Descriptions></div></section><section className="panel"><div className="panel-head"><h2>红外谱图与峰特性</h2><small>{material.spectra.length} 条谱图</small></div><div className="panel-body"><div className="spectrum-grid">{material.spectra.map((spectrum: KnowledgeSpectrum) => <article className="spectrum-card" key={spectrum.spectrum_id}>{spectrum.image_url ? <img src={spectrum.image_url} alt={spectrum.spectrum_id} /> : <div className="image-empty">NIST/参考记录无可显示图像</div>}<h3>{spectrum.payload.figure_caption || spectrum.spectrum_id}</h3><Table size="small" rowKey={(peak, index) => index ?? 0} dataSource={spectrum.peaks} pagination={false} columns={[{ title: "峰位 / cm-1", dataIndex: "measured_wavenumber", width: 140 }, { title: "归属", dataIndex: "peak_assignment" }]} /></article>)}</div></div></section></div>
}
