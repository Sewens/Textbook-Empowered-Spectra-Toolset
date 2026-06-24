import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactECharts from 'echarts-for-react'
import { Button, Descriptions, Input, Table, Tag, Tabs } from 'antd'
import { useQuery } from '@tanstack/react-query'

import { fetchGroup, fetchGroups, fetchManifest, resolveSpectraUrl } from '../api'
import type { AnnotatedPeak, GroupIndexItem, InherentVibration, SpectralGalleryItem } from '../types'
import MarkdownLite from '../components/MarkdownLite'
import { EmptyBlock, ErrorBlock, LoadingBlock } from '../components/StateBlock'

function rangeText(vib: InherentVibration) {
  if (vib.base_wavenumber_range?.length === 2) return vib.base_wavenumber_range.join(' - ') + ' cm-1'
  const first = vib.wavenumber_ranges?.[0]
  if (!first) return 'N/A'
  if (first.peak_cm_1) return first.peak_cm_1 + ' cm-1'
  if (first.min_cm_1 && first.max_cm_1) return first.min_cm_1 + ' - ' + first.max_cm_1 + ' cm-1'
  return first.range_text_original || 'N/A'
}

function peakText(peak: AnnotatedPeak) {
  if (peak.measured_wavenumber || peak.wavenumber_cm_1) return String(peak.measured_wavenumber ?? peak.wavenumber_cm_1) + ' cm-1'
  if (peak.wavenumber_min_cm_1 && peak.wavenumber_max_cm_1) return peak.wavenumber_min_cm_1 + ' - ' + peak.wavenumber_max_cm_1 + ' cm-1'
  return 'N/A'
}

export default function GroupsPage() {
  const navigate = useNavigate()
  const { groupId } = useParams()
  const [query, setQuery] = useState('')
  const groupsQuery = useQuery({ queryKey: ['groups', query], queryFn: () => fetchGroups(query || undefined) })
  const manifestQuery = useQuery({ queryKey: ['manifest'], queryFn: fetchManifest })
  const selectedId = groupId || groupsQuery.data?.[0]?.group_id
  const groupQuery = useQuery({ queryKey: ['group', selectedId], queryFn: () => fetchGroup(selectedId as string), enabled: Boolean(selectedId) })
  const chart = useMemo(() => ({
    grid: { left: 42, right: 12, top: 24, bottom: 62 },
    tooltip: {},
    xAxis: { type: 'category', data: (groupsQuery.data ?? []).slice(0, 14).map((g) => g.name_zh), axisLabel: { rotate: 34, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: (groupsQuery.data ?? []).slice(0, 14).map((g) => g.peak_count), itemStyle: { color: '#1976d2' } }],
  }), [groupsQuery.data])

  if (groupsQuery.isLoading) return <LoadingBlock />
  if (groupsQuery.error) return <ErrorBlock error={groupsQuery.error} />
  const groups = groupsQuery.data ?? []
  const group = groupQuery.data

  return <div className="page-grid groups-layout">
    <section className="panel group-index-panel">
      <div className="panel-head"><h2>功能基团卡片</h2><Input.Search placeholder="搜索 group id / 中英文名 / SMARTS" allowClear onSearch={setQuery} /></div>
      <div className="panel-body flush">
        <div className="metric-row compact">
          <div className="metric"><strong>{manifestQuery.data?.stats.functional_groups ?? groups.length}</strong><span>基团卡片</span></div>
          <div className="metric"><strong>{manifestQuery.data?.stats.evidence_spans ?? '-'}</strong><span>证据片段</span></div>
          <div className="metric"><strong>{manifestQuery.data?.stats.spectra ?? '-'}</strong><span>谱图记录</span></div>
          <div className="metric"><strong>{manifestQuery.data?.stats.peaks ?? '-'}</strong><span>峰归属</span></div>
        </div>
        <Table<GroupIndexItem>
          rowKey="group_id"
          size="small"
          pagination={{ pageSize: 12 }}
          dataSource={groups}
          rowClassName={(row) => row.group_id === selectedId ? 'active-row' : ''}
          onRow={(row) => ({ onClick: () => navigate('/groups/' + row.group_id) })}
          columns={[
            { title: '中文名', dataIndex: 'name_zh', width: 130 },
            { title: '英文名', dataIndex: 'name_en', ellipsis: true },
            { title: '模板', dataIndex: 'vibration_count', width: 72, sorter: (a, b) => a.vibration_count - b.vibration_count },
            { title: '峰', dataIndex: 'peak_count', width: 64, sorter: (a, b) => a.peak_count - b.peak_count },
            { title: '证据', dataIndex: 'evidence_count', width: 72 },
          ]}
        />
      </div>
    </section>
    <section className="panel group-detail-panel">
      <div className="panel-head"><h2>{group?.name_zh || selectedId || '卡片详情'}</h2><small>{group?.schema_version || 'schema v0.7'}</small></div>
      <div className="panel-body detail-scroll">
        {groupQuery.isLoading && <LoadingBlock />}
        {!groupQuery.isLoading && !group && <EmptyBlock>请选择左侧基团卡片。</EmptyBlock>}
        {group && <>
          <Descriptions size="small" bordered column={2}>
            <Descriptions.Item label="Group ID">{group.group_id}</Descriptions.Item>
            <Descriptions.Item label="English">{group.name_en}</Descriptions.Item>
            <Descriptions.Item label="Formula">{group.chemical_formula || group.group?.formula_fragment}</Descriptions.Item>
            <Descriptions.Item label="SMARTS">{group.smarts}</Descriptions.Item>
          </Descriptions>
          <ReactECharts option={chart} style={{ height: 230, marginTop: 12 }} />
          <Tabs items={[
            { key: 'spectra', label: '谱图/实例', children: <div className="spectrum-grid">{group.spectral_gallery.map((item: SpectralGalleryItem) => <article className="spectrum-card" key={item.spectrum_id || item.figure_id || item.compound_id}>
              {resolveSpectraUrl(item.mineru_crop_image_path || item.image_path) ? <img src={resolveSpectraUrl(item.mineru_crop_image_path || item.image_path)!} alt={item.figure_caption || ''} /> : <div className="image-empty">text evidence</div>}
              <h3>{item.compound_name_zh || item.compound_name_en || item.compound_id}</h3>
              <p>{item.figure_caption}</p>
              <Table size="small" pagination={false} dataSource={item.annotated_peaks || item.peaks || []} rowKey={(p: AnnotatedPeak) => p.peak_id || peakText(p)} columns={[{ title: '峰位', render: (_, row) => peakText(row), width: 110 }, { title: '归属', render: (_, row) => row.peak_assignment || row.assignments?.map((a) => a.assignment_text).filter(Boolean).join('; ') || row.notes, ellipsis: true }]} />
            </article>)}</div> },
            { key: 'vibrations', label: '振动模板', children: <Table size="small" pagination={{ pageSize: 8 }} rowKey="vibration_id" dataSource={group.vibration_templates} columns={[{ title: 'ID', dataIndex: 'vibration_id', ellipsis: true }, { title: '模式', dataIndex: 'mode', width: 90 }, { title: '波数', render: (_, row) => rangeText(row), width: 150 }, { title: '描述', dataIndex: 'textbook_description', ellipsis: true }]} /> },
            { key: 'evidence', label: '证据片段', children: <Table size="small" pagination={{ pageSize: 8 }} rowKey={(r) => r.evidence_id} dataSource={group.evidence_spans} columns={[{ title: 'Evidence ID', dataIndex: 'evidence_id', width: 230, ellipsis: true }, { title: '来源', dataIndex: 'source_book', width: 180, ellipsis: true }, { title: '文本', render: (_, row) => <MarkdownLite source={row.text || row.evidence_text || row.quote} compact /> }]} /> },
            { key: 'claims', label: '来源声明', children: <Table size="small" pagination={{ pageSize: 8 }} rowKey={(r) => r.claim_id} dataSource={group.source_claims} columns={[{ title: 'Claim ID', dataIndex: 'claim_id', width: 220, ellipsis: true }, { title: '谓词', dataIndex: 'predicate', width: 160 }, { title: '对象', render: (_, row) => JSON.stringify(row.object), ellipsis: true }]} /> },
          ]} />
        </>}
      </div>
    </section>
  </div>
}
