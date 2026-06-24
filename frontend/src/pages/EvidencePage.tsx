import { useMemo } from 'react'
import { Table } from 'antd'
import { useQuery } from '@tanstack/react-query'

import { fetchGroup, fetchGroups } from '../api'
import MarkdownLite from '../components/MarkdownLite'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'

type EvidenceRow = { group_id: string; group_name: string; evidence_id: string; source_book?: string; text?: string; image_path?: string | null }

export default function EvidencePage() {
  const groupsQuery = useQuery({ queryKey: ['groups', 'evidence-seed'], queryFn: () => fetchGroups() })
  const firstIds = (groupsQuery.data ?? []).slice(0, 8).map((g) => g.group_id)
  const detailQueries = useQuery({ queryKey: ['evidence-sample', firstIds.join(',')], queryFn: async () => Promise.all(firstIds.map((id) => fetchGroup(id))), enabled: firstIds.length > 0 })
  const rows = useMemo<EvidenceRow[]>(() => (detailQueries.data ?? []).flatMap((group) => group.evidence_spans.map((row) => ({ group_id: group.group_id, group_name: group.name_zh, evidence_id: row.evidence_id, source_book: row.source_book, text: row.text || row.evidence_text || row.quote, image_path: row.image_path }))).slice(0, 160), [detailQueries.data])
  if (groupsQuery.isLoading || detailQueries.isLoading) return <LoadingBlock />
  if (groupsQuery.error || detailQueries.error) return <ErrorBlock error={groupsQuery.error || detailQueries.error} />
  return <div className="panel full-panel"><div className="panel-head"><h2>证据追踪</h2><small>sample from first 8 group cards · 后续可接 /evidence 独立端点</small></div><div className="panel-body flush"><Table<EvidenceRow> size="small" rowKey={(r) => r.evidence_id} dataSource={rows} pagination={{ pageSize: 12 }} columns={[{ title: 'Evidence ID', dataIndex: 'evidence_id', width: 230, ellipsis: true }, { title: '基团', dataIndex: 'group_name', width: 110 }, { title: '来源', dataIndex: 'source_book', width: 220, ellipsis: true }, { title: '文本', render: (_, row) => <MarkdownLite source={row.text} compact /> }]} /></div></div>
}
