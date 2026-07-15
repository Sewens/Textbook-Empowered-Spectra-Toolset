import { Alert, Card, Descriptions, Tag } from "antd"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogOverview } from "../api"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

export default function CatalogDashboardPage() {
  const query = useQuery({ queryKey: ["catalog-overview"], queryFn: fetchCatalogOverview })
  if (query.isLoading) return <LoadingBlock />
  if (query.error) return <ErrorBlock error={query.error} />
  const overview = query.data!
  return <div className="catalog-dashboard">
    <section className="catalog-hero"><div><span>SCHEMA-NATIVE CATALOG</span><h1>谱-构-效知识图谱</h1><p>教材 accepted 证据与 NIST staging 数据分区索引；所有实体、谱特征、归属与声明均保留可追溯来源。</p></div><Tag color="processing">{overview.schema_release ?? "schema pending"}</Tag></section>
    <div className="metric-row catalog-metrics">{Object.entries(overview.counts).map(([name, value]) => <Card key={name} size="small"><strong>{value.toLocaleString()}</strong><span>{name}</span></Card>)}</div>
    <Alert type="warning" showIcon message="NIST 数据为独立 staging 层" description="NIST 记录可用于元数据、资产状态和后续对齐；当前不等同于已验证教材结论，受限谱图也不在本站重新分发。" />
    <Descriptions className="catalog-provenance" bordered size="small" column={2}><Descriptions.Item label="Release">{overview.release_id}</Descriptions.Item><Descriptions.Item label="Packet schema">{overview.packet_schema ?? "-"}</Descriptions.Item><Descriptions.Item label="Accepted textbook packets">{overview.data_partitions.accepted_textbook_packets}</Descriptions.Item><Descriptions.Item label="NIST metadata">{overview.data_partitions.nist_metadata_records.toLocaleString()}</Descriptions.Item><Descriptions.Item label="Quarantine">excluded</Descriptions.Item><Descriptions.Item label="NIST">staging only</Descriptions.Item></Descriptions>
  </div>
}
