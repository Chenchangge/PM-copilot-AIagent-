import axios from 'axios'

import { getUserId } from '@/utils/userId'

// 统一请求实例：开发环境由 Vite 代理 /api 到后端 8000 端口
const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 匿名用户身份：所有请求自动附带 X-User-Id（后端按此隔离数据）
http.interceptors.request.use((config) => {
  config.headers['X-User-Id'] = getUserId()
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => Promise.reject(err)
)

export default http
