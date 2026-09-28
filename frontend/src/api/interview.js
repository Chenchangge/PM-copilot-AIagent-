// 模拟面试接口封装（统一走 service 层，页面不直接 axios）。
import http from './index'

export function createInterviewSession({ direction, difficulty, interview_type }) {
  return http.post('/interview/sessions', { direction, difficulty, interview_type })
}

export function getInterviewSession(sessionId) {
  return http.get(`/interview/sessions/${sessionId}`)
}

export function submitInterviewAnswer(sessionId, { answer, client_request_id }) {
  return http.post(`/interview/sessions/${sessionId}/answer`, { answer, client_request_id })
}

export function finishInterviewSession(sessionId) {
  return http.post(`/interview/sessions/${sessionId}/finish`)
}

export function createEvaluation(sessionId) {
  // 评价为同步长请求（LLM 一次调用 + 可能重试一次），超时放宽到 90s，避免被默认 15s 截断。
  return http.post(`/interview/sessions/${sessionId}/evaluation`, {}, { timeout: 90000 })
}

export function getEvaluation(sessionId) {
  return http.get(`/interview/sessions/${sessionId}/evaluation`)
}
