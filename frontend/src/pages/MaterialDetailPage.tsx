import { Alert, Button, Descriptions, Empty, Space, Table, Tag } from "antd"
import { useEffect, useMemo, useState } from "react"
import { useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogMaterial, fetchTextbookInventoryUnifiedDetail } from "../api"
import type { KnowledgeSpectrum, UnifiedEvidence, UnifiedImage, UnifiedStreamItem, UnifiedTextbookDetail } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

type DetailMode = "material" | "spectrum"
const PAGE_SIZE = 12
const STREAM_THRESHOLD = 12

const assetUrl = (image: UnifiedImage) => "/api/catalog/textbook-inventory/assets/" + encodeURIComponent(image.book) + "/" + image.path.split("/").map(encodeURIComponent).join("/")
const cleanText = (value?: string | null, max = 280) => {
  if (!value) return ""
  const text = value.replace(/text\n/g, " ").replace(/equation_inline\n?/g, " ").replace(/\n/g, " ").replace(/\s+/g, " ").trim()
  return text.length > max ? text.slice(0, max) + "..." : text
}

function Evidence({ items }: { items: UnifiedEvidence[] }) {
  if (!items.length) return null
  return (
    <section className="detail-section">
      <h3>教材证据</h3>
      {items.map((item) => (
        <article className="evidence-card" key={item.id}>
          <div>
            <Tag>{item.type || "text"}</Tag>
            {item.page ? <span>{"第 " + item.page + " 页"}</span> : null}
            {item.content_list_index !== undefined ? <span>{" · MinerU #" + item.content_list_index}</span> : null}
          </div>
          <p>{cleanText(item.text, 360) || "未提供原文"}</p>
        </article>
      ))}
    </section>
  )
}

function SpectrumCard({ id, caption, peaks = [], images = [], evidence = [], imageUrl, book, page }: { id: string; caption?: string; peaks?: Array<Record<string, any>>; images?: UnifiedImage[]; evidence?: UnifiedEvidence[]; imageUrl?: string | null; book?: string; page?: number }) {
  const sources = images.map((image) => ({ src: assetUrl(image), alt: image.caption || image.id }))
  if (!sources.length && imageUrl) sources.push({ src: imageUrl, alt: id })
  return (
    <article className="spectrum-card">
      <div className="spectrum-media">
        {sources.length ? sources.map((image) => <img key={image.src} src={image.src} alt={image.alt} loading="lazy" />) : <div className="image-empty">该条谱图没有可用图像资产</div>}
      </div>
      <h3 title={caption || id}>{cleanText(caption, 180) || id}</h3>
      <div className="tag-row" style={{ marginBottom: 8 }}>
        {book ? <Tag color="blue">{book}</Tag> : null}
        {page ? <Tag>{"第 " + page + " 页"}</Tag> : null}
        <Tag>{id}</Tag>
      </div>
      <Table
        size="small"
        rowKey={(_, i) => String(i)}
        dataSource={(peaks || []).slice(0, 12)}
        pagination={false}
        locale={{ emptyText: "未抽取到峰特性" }}
        columns={[
          { title: "峰位 / 文本", render: (_: any, row: any) => row.measured_wavenumber ?? cleanText(row.raw_position_text, 40) ?? "-", width: 150 },
          { title: "归属", render: (_: any, row: any) => cleanText(row.peak_assignment ?? row.assignment, 80) || "-" },
          { title: "单位", render: (_: any, row: any) => row.unit ?? "cm-1", width: 90 },
        ]}
      />
      <Evidence items={(evidence || []).slice(0, 3)} />
    </article>
  )
}

function StreamDetail({ detail, items, loadingMore, onLoadMore }: { detail: UnifiedTextbookDetail; items: UnifiedStreamItem[]; loadingMore: boolean; onLoadMore: () => void }) {
  const counts = detail.counts
  const page = detail.page
  const stream = Boolean(counts?.stream)
  return (
    <div className="group-detail-v2">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>{detail.title}</h2>
            <small>{detail.id}</small>
          </div>
          <Space>
            <Tag color="orange">{detail.review_status}</Tag>
            {stream ? <Tag color="gold">瀑布加载</Tag> : <Tag color="blue">全量可直出</Tag>}
          </Space>
        </div>
        <div className="panel-body">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="来源教材">{detail.books.join("；")}</Descriptions.Item>
            <Descriptions.Item label="来源记录">{detail.source_count}</Descriptions.Item>
            <Descriptions.Item label="谱图总数">{counts?.spectra_total ?? "-"}</Descriptions.Item>
            <Descriptions.Item label="证据总数">{counts?.evidence_total ?? "-"}</Descriptions.Item>
            <Descriptions.Item label="当前已加载">{items.length + " / " + (counts?.spectra_total ?? 0)}</Descriptions.Item>
          </Descriptions>
          {(detail.materials?.length || detail.groups?.length) ? (
            <section className="detail-section" style={{ marginTop: 12 }}>
              <h3>物质与关联基团</h3>
              <div className="tag-row">
                {(detail.materials || []).map((item) => <Tag color="green" key={item.id}>{item.name || item.id}</Tag>)}
                {(detail.groups || []).map((item) => <Tag color="blue" key={item.id}>{item.name || item.id}</Tag>)}
              </div>
            </section>
          ) : null}
          {stream ? (
            <Alert
              style={{ marginTop: 12 }}
              type="info"
              showIcon
              message={"谱图数量超过阈值 " + (counts?.threshold ?? STREAM_THRESHOLD) + "，已启用瀑布式加载"}
              description="首屏只渲染一页，继续下滑或点击按钮可追加下一页，避免一次渲染导致页面卡死。"
            />
          ) : null}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>红外谱图流</h2>
          <small>{items.length + " 条已加载"}</small>
        </div>
        <div className="panel-body">
          <div className="spectrum-grid">
            {items.map((item) => (
              <SpectrumCard
                key={item.spectrum.id + "@" + item.book}
                id={item.spectrum.id}
                caption={item.spectrum.caption}
                peaks={item.spectrum.features}
                images={item.spectrum.images}
                evidence={item.spectrum.evidence}
                book={item.book}
                page={item.page}
              />
            ))}
          </div>
          {!items.length ? <Empty description="尚无关联谱图" /> : null}
          {page?.has_more ? (
            <div style={{ display: "flex", justifyContent: "center", marginTop: 16 }}>
              <Button type="primary" loading={loadingMore} onClick={onLoadMore}>加载更多谱图</Button>
            </div>
          ) : items.length ? (
            <div style={{ textAlign: "center", marginTop: 16, color: "#64748b" }}>已加载全部谱图</div>
          ) : null}
        </div>
      </section>
    </div>
  )
}

function CatalogDetail({ material }: { material: import("../types").MaterialKnowledgeDetail }) {
  const payload: any = material.payload
  const scope = material.source_scope as string
  const provenance = payload.provenance || {}
  const source = provenance.book || (scope === "legacy_reference" ? "原始教材待补录（legacy reference 聚合卡）" : scope === "nist" ? "NIST IR Metadata Inventory（staging）" : "教材 accepted packet")
  const locator = provenance.mineru_locator
  const [visible, setVisible] = useState(PAGE_SIZE)
  const spectra = useMemo(() => material.spectra.slice(0, visible), [material.spectra, visible])
  const hasMore = visible < material.spectra.length
  return (
    <div className="group-detail-v2">
      <section className="panel">
        <div className="panel-head"><div><h2>{material.name}</h2><small>{material.entity_id}</small></div><Tag color="green">物质实体</Tag></div>
        <div className="panel-body">
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="来源教材 / 数据库" span={2}>{source}</Descriptions.Item>
            {provenance.figure ? <Descriptions.Item label="图号">{provenance.figure}</Descriptions.Item> : null}
            {locator ? <Descriptions.Item label="MinerU 定位">{"页组 " + locator.page_group_index + " · 条目 " + locator.content_item_index}</Descriptions.Item> : null}
            <Descriptions.Item label="数据分区">{material.source_scope}</Descriptions.Item>
            <Descriptions.Item label="审核状态">{material.review_status}</Descriptions.Item>
            <Descriptions.Item label="分子式">{payload.formula || payload.molecular_formula || "-"}</Descriptions.Item>
            <Descriptions.Item label="SMILES">{payload.smiles || "-"}</Descriptions.Item>
            <Descriptions.Item label="关联基团" span={2}><div className="tag-row">{material.groups.map((group) => <Tag color="blue" key={group.group_id}>{group.name}</Tag>)}</div></Descriptions.Item>
          </Descriptions>
        </div>
      </section>
      <section className="panel">
        <div className="panel-head"><h2>红外谱图与峰特性</h2><small>{spectra.length + "/" + material.spectra.length + " 条谱图"}</small></div>
        <div className="panel-body">
          <div className="spectrum-grid">
            {spectra.map((item: KnowledgeSpectrum) => <SpectrumCard key={item.spectrum_id} id={item.spectrum_id} caption={item.payload.figure_caption} peaks={item.peaks} imageUrl={item.image_url} />)}
          </div>
          {!material.spectra.length ? <Empty description="尚无关联谱图" /> : null}
          {hasMore ? (
            <div style={{ display: "flex", justifyContent: "center", marginTop: 16 }}>
              <Button onClick={() => setVisible((n) => n + PAGE_SIZE)}>加载更多谱图</Button>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  )
}

export default function MaterialDetailPage({ mode = "material" }: { mode?: DetailMode }) {
  const { materialId = "", spectrumId = "" } = useParams()
  const id = mode === "spectrum" ? spectrumId : materialId
  const inventory = mode === "spectrum" || !id.startsWith("MAT_LEGACY_")
  const [items, setItems] = useState<UnifiedStreamItem[]>([])
  const [header, setHeader] = useState<UnifiedTextbookDetail | null>(null)
  const [nextOffset, setNextOffset] = useState<number | null>(0)
  const [loadingMore, setLoadingMore] = useState(false)

  const firstPage = useQuery({
    queryKey: ["unified-textbook-detail-stream", mode, id, 0, PAGE_SIZE, STREAM_THRESHOLD],
    queryFn: () => fetchTextbookInventoryUnifiedDetail(mode === "spectrum" ? "spectra" : "materials", id, {
      offset: 0,
      limit: PAGE_SIZE,
      threshold: STREAM_THRESHOLD,
    }),
    enabled: Boolean(id && inventory),
  })
  const catalog = useQuery({ queryKey: ["catalog-material", id], queryFn: () => fetchCatalogMaterial(id), enabled: Boolean(id && !inventory) })

  useEffect(() => {
    setItems([])
    setHeader(null)
    setNextOffset(0)
  }, [id, mode])

  useEffect(() => {
    if (!firstPage.data) return
    setHeader(firstPage.data)
    setItems(firstPage.data.items || [])
    setNextOffset(firstPage.data.page?.next_offset ?? null)
  }, [firstPage.data])

  const loadMore = async () => {
    if (nextOffset == null || loadingMore) return
    setLoadingMore(true)
    try {
      const page = await fetchTextbookInventoryUnifiedDetail(mode === "spectrum" ? "spectra" : "materials", id, {
        offset: nextOffset,
        limit: PAGE_SIZE,
        threshold: STREAM_THRESHOLD,
      })
      setHeader(page)
      setItems((prev) => prev.concat(page.items || []))
      setNextOffset(page.page?.next_offset ?? null)
    } finally {
      setLoadingMore(false)
    }
  }

  if (firstPage.isLoading || catalog.isLoading) return <LoadingBlock />
  if (firstPage.error || catalog.error) return <ErrorBlock error={firstPage.error ?? catalog.error} />
  if (header) {
    return (
      <StreamDetail
        detail={{ ...header, page: { offset: header.page?.offset ?? 0, limit: header.page?.limit ?? PAGE_SIZE, returned: items.length, has_more: nextOffset != null, next_offset: nextOffset } }}
        items={items}
        loadingMore={loadingMore}
        onLoadMore={loadMore}
      />
    )
  }
  if (catalog.data) return <CatalogDetail material={catalog.data} />
  return <Alert type="warning" message="未找到物质或谱图详情" />
}
