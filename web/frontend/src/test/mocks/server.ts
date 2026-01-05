import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// 建立 MSW server 用於 Node.js 環境（測試）
export const server = setupServer(...handlers)
