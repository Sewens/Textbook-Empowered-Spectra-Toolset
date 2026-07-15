import ReactECharts from 'echarts-for-react'
import { Table, Tag } from 'antd'
import { useQuery } from '@tanstack/react-query'

import { fetchCatalogGraph } from '../api'
import type { GraphNode } from '../types'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'

export default function GraphPage() {
  const graphQuery = useQuery({ queryKey: ['graph'], queryFn: fetchCatalogGraph })
  if (graphQuery.isLoading) return <LoadingBlock />
  if (graphQuery.error) return <ErrorBlock error={graphQuery.error} />
  const graph = graphQuery.data
  const option = {
    tooltip: {},
    series: [{
      type: 'graph', layout: 'force', roam: true, symbolSize: 12,
      data: (graph?.nodes ?? []).slice(0, 180).map((node) => ({ id: node.id, name: node.label, category: node.type })),
      links: (graph?.edges ?? []).slice(0, 280).map((edge) => ({ source: edge.source, target: edge.target, name: edge.label })),
      categories: Array.from(new Set((graph?.nodes ?? []).map((node) => node.type))).map((name) => ({ name })),
      force: { repulsion: 80, edgeLength: 60 },
      label: { show: false },
    }],
  }
  return <div className="page-grid graph-layout"><section className="panel"><div className="panel-head"><h2>知识图谱</h2><small>{graph?.nodes.length ?? 0} nodes · {graph?.edges.length ?? 0} edges</small></div><div className="panel-body"><ReactECharts option={option} style={{ height: 620 }} /></div></section><aside className="panel"><div className="panel-head"><h2>节点抽样</h2><small>top 80</small></div><div className="panel-body flush"><Table<GraphNode> size="small" rowKey="id" dataSource={(graph?.nodes ?? []).slice(0, 80)} pagination={false} columns={[{ title: '类型', dataIndex: 'type', width: 96, render: (v) => <Tag>{v}</Tag> }, { title: 'Label', dataIndex: 'label', ellipsis: true }]} /></div></aside></div>
}
