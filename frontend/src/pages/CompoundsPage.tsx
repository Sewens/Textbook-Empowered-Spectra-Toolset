import { useState } from 'react'
import { Button, Input, Table, Tag } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { fetchCompounds } from '../api'
import type { CompoundRecord } from '../types'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'

export default function CompoundsPage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const compoundsQuery = useQuery({ queryKey: ['compounds', query], queryFn: () => fetchCompounds(query || undefined) })
  if (compoundsQuery.isLoading) return <LoadingBlock />
  if (compoundsQuery.error) return <ErrorBlock error={compoundsQuery.error} />
  return <div className="panel full-panel"><div className="panel-head"><h2>化合物实例索引</h2><Input.Search allowClear placeholder="compound id / 中英文名 / 分子式" onSearch={setQuery} /></div><div className="panel-body flush"><Table<CompoundRecord> size="small" rowKey="compound_id" dataSource={compoundsQuery.data ?? []} pagination={{ pageSize: 15 }} columns={[{ title: '中文名', dataIndex: 'name_zh', width: 150 }, { title: 'English', dataIndex: 'name_en', width: 200, ellipsis: true }, { title: '分子式', dataIndex: 'molecular_formula', width: 110 }, { title: '类别', dataIndex: 'compound_class', width: 180, ellipsis: true }, { title: '关联基团', render: (_, row) => <div className="tag-list">{row.group_ids.map((id) => <Tag key={id} onClick={() => navigate('/groups/' + id)}>{id}</Tag>)}</div> }, { title: '谱图', dataIndex: 'spectrum_count', width: 72 }, { title: '峰', dataIndex: 'peak_count', width: 64 }, { title: '操作', width: 90, render: (_, row) => <Button size="small" onClick={() => row.group_ids[0] && navigate('/groups/' + row.group_ids[0])}>卡片</Button> }]} /></div></div>
}
