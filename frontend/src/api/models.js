// AI 模型 / API 相关的接口封装（统一走 service 层，页面不直接 axios）。
import http from './index'

export function listModels() {
  return http.get('/models')
}

export function createModel(data) {
  return http.post('/models', data)
}

export function getModel(id) {
  return http.get(`/models/${id}`)
}

export function updateModel(id, data) {
  return http.put(`/models/${id}`, data)
}

export function deleteModel(id) {
  return http.delete(`/models/${id}`)
}

export function testModel(id) {
  return http.post(`/models/${id}/test`)
}

export function resolveModel(requiredCapabilities) {
  return http.post('/models/resolve', { required_capabilities: requiredCapabilities })
}
