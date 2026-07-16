import { useState } from 'react'
import { Input, Table } from 'antd'
import { useQuery } from '@tanstack/react-query'

import { fetchNistStats, fetchSpectra, resolveSpectraUrl } from '../api'
import type { SpectraRecord } from '../types'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'

export default function SpectraPage() {
  const [query, setQuery] = useState('')
  const spectraQuery = useQuery({ queryKey: ['spectra'], queryFn: fetchSpectra })
  const nistQuery = useQuery({ queryKey: ['nist-stats'], queryFn: fetchNistStats })
  if (spectraQuery.isLoading) return <LoadingBlock />
  if (spectraQuery.error) return <ErrorBlock error={spectraQuery.error} />
  const rows = (spectraQuery.data ?? []).filter((item) => !query || JSON.stringify(item).toLowerCase().includes(query.toLowerCase()))
  const selected = rows[0]
  return <div className="page-grid spectra-layout">
    <section className="panel"><div className="panel-head"><h2>谱图索引</h2><small>{nistQuery.data ? `NIST ${(nistQuery.data.counts as Record<string, number>)?.spectra ?? 0} 条` : 'NIST 索引构建中'}</small><Input.Search allowClear placeholder="搜索 spectrum / compound / group" onSearch={setQuery} /></div><div className="panel-body flush"><Table<SpectraRecord> size="small" rowKey="spectrum_id" dataSource={rows} pagination={{ pageSize: 14 }} columns={[{ title: '谱图', dataIndex: 'spectrum_id', ellipsis: true }, { title: '化合物', dataIndex: 'compound_name_zh', width: 130 }, { title: '基团', dataIndex: 'group_name_zh', width: 110 }, { title: '峰', dataIndex: 'annotated_peak_count', width: 64 }]} /></div></section>
    <aside className="panel"><div className="panel-head"><h2>快速预览</h2><small>{rows.length} spectra</small></div><div className="panel-body">{selected && <><div className="asset-preview">{resolveSpectraUrl(selected.image_path) ? <img src={resolveSpectraUrl(selected.image_path)!} alt={selected.figure_id || selected.spectrum_id} /> : <span>文本/表格证据</span>}</div><h3>{selected.compound_name_zh || selected.compound_name_en || selected.compound_id}</h3><p>{selected.figure_caption}</p><div className="chip-row"><span>{selected.group_id}</span><span>{selected.spectrum_id}</span><span>{selected.annotated_peak_count} peaks</span></div></>}</div></aside>
  </div>
}
