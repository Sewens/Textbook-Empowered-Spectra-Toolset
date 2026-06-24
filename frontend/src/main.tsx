import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import './styles.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1976d2',
          borderRadius: 2,
          fontFamily: 'Segoe UI Variable Text, Aptos, Segoe UI, Microsoft YaHei, sans-serif',
          colorBgLayout: '#f7f8fa',
          colorBorder: '#d9dee7',
        },
        components: {
          Button: { controlHeight: 30 },
          Table: { headerBg: '#f1f3f6', borderColor: '#d9dee7' },
          Tabs: { horizontalMargin: '0' },
        },
      }}
    >
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  </React.StrictMode>,
)
