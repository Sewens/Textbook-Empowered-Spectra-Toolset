import { Alert, Skeleton } from 'antd'
import type { ReactNode } from 'react'

export function LoadingBlock() {
  return <div className="panel"><div className="panel-body"><Skeleton active paragraph={{ rows: 8 }} /></div></div>
}

export function ErrorBlock({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : 'API 请求失败'
  return <Alert type="error" showIcon message="加载失败" description={message} />
}

export function EmptyBlock({ children = '当前筛选没有数据。' }: { children?: ReactNode }) {
  return <div className="state-panel"><h2>Empty</h2><p>{children}</p></div>
}
