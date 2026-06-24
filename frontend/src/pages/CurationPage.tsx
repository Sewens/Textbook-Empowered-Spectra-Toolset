import { Alert, Button, Steps, Table, Tag } from 'antd'
import { useMutation } from '@tanstack/react-query'

import { api } from '../api'

const rows = [
  { key: 'import', name: 'Import FG_*.json', target: 'raw_data/basic_groups_v07_20260619', state: 'done' },
  { key: 'normalize', name: 'Normalize entities', target: 'cards / spectra / peaks / assignments', state: 'active' },
  { key: 'evidence', name: 'Join evidence links', target: 'evidence_ids -> evidence_spans', state: 'active' },
  { key: 'review', name: 'Review and publish', target: 'requires data_admin / site_admin', state: 'rbac' },
]

export default function CurationPage() {
  const mutation = useMutation({ mutationFn: async () => (await api.post('/analysis', { wavenumber: 1715, tolerance: 5 })).data })
  return <div className="page-grid curation-layout"><section className="panel"><div className="panel-head"><h2>标注流转 / RBAC 准备</h2><Button type="primary" onClick={() => mutation.mutate()}>以当前角色提交分析任务</Button></div><div className="panel-body"><Alert type="info" showIcon message="后端 RBAC 已接入" description="普通用户会被 POST /analysis 拒绝；数据管理员和网站管理员可提交。后续正式登录后只需替换当前 X-User-Role 开发头。" /><Steps className="curation-steps" direction="vertical" current={1} items={rows.map((row) => ({ title: row.name, description: row.target }))} />{mutation.error && <Alert type="error" showIcon message="提交被拒绝或失败" description={mutation.error instanceof Error ? mutation.error.message : 'Forbidden'} />}{mutation.data && <Alert type="success" showIcon message="提交成功" description={mutation.data.summary} />}</div></section><aside className="panel"><div className="panel-head"><h2>流程表</h2><small>prototype</small></div><div className="panel-body flush"><Table size="small" pagination={false} dataSource={rows} columns={[{ title: '阶段', dataIndex: 'name' }, { title: '状态', dataIndex: 'state', width: 90, render: (v) => <Tag color={v === 'done' ? 'green' : v === 'active' ? 'blue' : 'orange'}>{v}</Tag> }]} /></div></aside></div>
}
