import { useState } from 'react'
import { Button, InputNumber, Table } from 'antd'
import { useQuery } from '@tanstack/react-query'

import { searchWavenumber } from '../api'
import type { WavenumberSearchResult } from '../types'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'

export default function SearchPage() {
  const [value, setValue] = useState(1715)
  const [tolerance, setTolerance] = useState(10)
  const [submitted, setSubmitted] = useState({ value: 1715, tolerance: 10 })
  const query = useQuery({ queryKey: ['wavenumber', submitted], queryFn: () => searchWavenumber(submitted.value, submitted.tolerance) })
  return <div className="panel full-panel"><div className="panel-head"><h2>波数检索</h2><div className="inline-actions"><InputNumber min={400} max={4000} value={value} onChange={(v) => setValue(Number(v || 1715))} addonAfter="cm-1" /><InputNumber min={0} max={80} value={tolerance} onChange={(v) => setTolerance(Number(v || 0))} addonAfter="±" /><Button type="primary" onClick={() => setSubmitted({ value, tolerance })}>检索</Button></div></div><div className="panel-body flush">{query.isLoading ? <LoadingBlock /> : query.error ? <ErrorBlock error={query.error} /> : <Table<WavenumberSearchResult> size="small" rowKey={(r) => r.spectrum_id + ':' + r.group_id + ':' + String(r.wavenumber)} dataSource={query.data ?? []} pagination={{ pageSize: 15 }} columns={[{ title: '基团', dataIndex: 'group_name_zh', width: 120 }, { title: '峰位', dataIndex: 'wavenumber', width: 100, render: (v) => Array.isArray(v) ? v.join('-') : v }, { title: '距离', dataIndex: 'distance', width: 80 }, { title: '归属', dataIndex: 'assignment', ellipsis: true }, { title: '证据', dataIndex: 'source_book', width: 180, ellipsis: true }]} />}</div></div>
}
