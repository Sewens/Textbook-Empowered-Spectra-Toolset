import { Alert, Descriptions, Empty, Table, Tag } from "antd"
import { useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogMaterial, fetchTextbookInventoryUnifiedDetail } from "../api"
import type { KnowledgeSpectrum, UnifiedEvidence, UnifiedImage, UnifiedSourceCard } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

type DetailMode = "material" | "spectrum"
const assetUrl = (image: UnifiedImage) => "/api/catalog/textbook-inventory/assets/" + encodeURIComponent(image.book) + "/" + image.path.split("/").map(encodeURIComponent).join("/")

function Evidence({ items }: { items: UnifiedEvidence[] }) {
  return items.length ? <section className="detail-section"><h3>教材证据</h3>{items.map((item) => <article className="evidence-card" key={item.id}><div><Tag>{item.type || "text"}</Tag>{item.page ? <span>第 {item.page} 页</span> : null}{item.content_list_index !== undefined ? <span> · MinerU #{item.content_list_index}</span> : null}</div><p>{item.text || "未提供原文"}</p></article>)}</section> : null
}

function Spectrum({ id, caption, peaks = [], images = [], evidence = [], imageUrl }: { id: string; caption?: string; peaks?: Array<Record<string, any>>; images?: UnifiedImage[]; evidence?: UnifiedEvidence[]; imageUrl?: string | null }) {
  const sources = images.map((image) => ({ src: assetUrl(image), alt: image.caption || image.id }))
  if (!sources.length && imageUrl) sources.push({ src: imageUrl, alt: id })
  return <article className="spectrum-card"><div className="spectrum-media">{sources.length ? sources.map((image) => <img key={image.src} src={image.src} alt={image.alt} loading="lazy" />) : <div className="image-empty">该条谱图没有可用图像资产</div>}</div><h3>{(caption ? caption.slice(0, 420) : id)}</h3><Table size="small" rowKey={(_, i) => String(i)} dataSource={peaks} pagination={false} locale={{ emptyText: "未抽取到峰特性" }} columns={[{ title: "峰位 / 文本", render: (_, row: any) => row.measured_wavenumber ?? row.raw_position_text ?? "-", width: 150 }, { title: "归属", render: (_, row: any) => row.peak_assignment ?? row.assignment ?? "-" }, { title: "单位", render: (_, row: any) => row.unit ?? "cm-1", width: 90 }]} /><Evidence items={evidence} /></article>
}

function TextbookSource({ source }: { source: UnifiedSourceCard }) {
  return <section className="panel"><div className="panel-head"><div><h2>{source.book}</h2><small>{source.page ? `第 ${source.page} 页` : ""}{source.content_list_index != null ? ` · MinerU #${source.content_list_index}` : ""}</small></div></div><div className="panel-body"><section className="detail-section"><h3>物质与关联基团</h3><div className="tag-row">{source.materials.map((item) => <Tag color="green" key={item.id}>{item.name || item.id}</Tag>)}{source.groups.map((item) => <Tag color="blue" key={item.id}>{item.name || item.id}</Tag>)}</div></section>{source.spectra.length ? <section className="detail-section"><h3>红外谱图</h3><div className="spectrum-grid">{source.spectra.map((item) => <Spectrum key={item.id} id={item.id} caption={item.caption} peaks={item.features} images={item.images} evidence={item.evidence} />)}</div></section> : null}<Evidence items={source.evidence} /></div></section>
}

function TextbookDetail({ detail }: { detail: import("../types").UnifiedTextbookDetail }) {
  return <div className="group-detail-v2"><section className="panel"><div className="panel-head"><div><h2>{detail.title}</h2><small>{detail.id}</small></div><Tag color="orange">{detail.review_status}</Tag></div><div className="panel-body"><Descriptions bordered size="small" column={1}><Descriptions.Item label="来源教材">{detail.books.join("；")}</Descriptions.Item><Descriptions.Item label="来源记录">{detail.source_count}</Descriptions.Item></Descriptions></div></section>{detail.source_cards.map((source, index) => <TextbookSource key={`${source.book}-${index}`} source={source} />)}</div>
}

function CatalogDetail({ material }: { material: import("../types").MaterialKnowledgeDetail }) {
  const payload: any = material.payload
  return <div className="group-detail-v2"><section className="panel"><div className="panel-head"><div><h2>{material.name}</h2><small>{material.entity_id}</small></div><Tag color="green">物质实体</Tag></div><div className="panel-body"><Descriptions bordered size="small" column={2}><Descriptions.Item label="分子式">{payload.formula || payload.molecular_formula || "-"}</Descriptions.Item><Descriptions.Item label="SMILES">{payload.smiles || "-"}</Descriptions.Item><Descriptions.Item label="关联基团" span={2}><div className="tag-row">{material.groups.map((group) => <Tag color="blue" key={group.group_id}>{group.name}</Tag>)}</div></Descriptions.Item></Descriptions></div></section><section className="panel"><div className="panel-head"><h2>红外谱图与峰特性</h2><small>{material.spectra.length} 条谱图</small></div><div className="panel-body"><div className="spectrum-grid">{material.spectra.map((item: KnowledgeSpectrum) => <Spectrum key={item.spectrum_id} id={item.spectrum_id} caption={item.payload.figure_caption} peaks={item.peaks} imageUrl={item.image_url} />)}</div>{!material.spectra.length ? <Empty description="尚无关联谱图" /> : null}</div></section></div>
}

export default function MaterialDetailPage({ mode = "material" }: { mode?: DetailMode }) {
  const { materialId = "", spectrumId = "" } = useParams()
  const id = mode === "spectrum" ? spectrumId : materialId
  const inventory = mode === "spectrum" || !id.startsWith("MAT_LEGACY_")
  const textbook = useQuery({ queryKey: ["unified-textbook-detail", mode, id], queryFn: () => fetchTextbookInventoryUnifiedDetail(mode === "spectrum" ? "spectra" : "materials", id), enabled: Boolean(id && inventory) })
  const catalog = useQuery({ queryKey: ["catalog-material", id], queryFn: () => fetchCatalogMaterial(id), enabled: Boolean(id && !inventory) })
  if (textbook.isLoading || catalog.isLoading) return <LoadingBlock />
  if (textbook.error || catalog.error) return <ErrorBlock error={textbook.error ?? catalog.error} />
  if (textbook.data) return <TextbookDetail detail={textbook.data} />
  if (catalog.data) return <CatalogDetail material={catalog.data} />
  return <Alert type="warning" message="未找到物质或谱图详情" />
}
