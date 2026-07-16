import { Card, Empty, Table, Tag } from "antd"
import { useQuery } from "@tanstack/react-query"

import { fetchCatalogEntities } from "../api"
import type { CatalogEntity } from "../types"
import { ErrorBlock, LoadingBlock } from "../components/StateBlock"

function claimPayload(row: CatalogEntity): any { return row.payload }

function objectLabel(payload: Record<string, any>) {
  const object = payload.object ?? {}
  return object.entity_ref || object.literal?.raw_text || object.literal?.value || "-"
}

export default function ClaimsPage() {
  const query = useQuery({ queryKey: ["catalog-claims"], queryFn: () => fetchCatalogEntities("claim") })
  if (query.isLoading) return <LoadingBlock />
  if (query.error) return <ErrorBlock error={query.error} />
  const claims = query.data ?? []
  return <div className="claims-page"><section className="panel"><div className="panel-head"><div><h2>声明与效应</h2><small>仅展示教材抽取的可追溯声明；NIST staging 不会被提升为教材事实。</small></div><Tag color="blue">{claims.length} asserted claims</Tag></div><div className="panel-body flush">{claims.length === 0 ? <Empty description="当前发布包未提供可浏览声明" /> : <Table<CatalogEntity> size="small" rowKey="entity_id" dataSource={claims} pagination={false} expandable={{ expandedRowRender: (row) => <Card size="small" className="claim-note"><b>原文语义：</b>{claimPayload(row).qualifiers?.note || "-"}<br /><b>证据：</b>{(claimPayload(row).evidence_ids || []).join(", ") || "-"}</Card> }} columns={[{ title: "主体概念", render: (_, row) => claimPayload(row).subject_ref || "-", width: 250 }, { title: "关系", render: (_, row) => <Tag color="cyan">{claimPayload(row).predicate || row.name}</Tag>, width: 170 }, { title: "对象 / 效应", render: (_, row) => objectLabel(row.payload), minWidth: 300, ellipsis: true }, { title: "条件", render: (_, row) => claimPayload(row).qualifiers?.phase || claimPayload(row).qualifiers?.direction || "-", width: 180 }, { title: "置信度", render: (_, row) => claimPayload(row).extraction_confidence ?? "-", width: 100 }, { title: "状态", render: (_, row) => <Tag color={claimPayload(row).assertion_status === "asserted" ? "green" : "gold"}>{claimPayload(row).assertion_status || row.review_status}</Tag>, width: 110 }]} />}</div></section></div>
}
