import axios from 'axios'

// 统一请求实例：开发环境由 Vite 代理 /api 到后端 8000 端口
const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => Promise.reject(err)
)

export default http
