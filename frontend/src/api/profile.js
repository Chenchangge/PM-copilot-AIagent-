// 用户中心接口封装（学习记录 / 面试记录，分页）。
import http from './index'

export function getLearningHistory(params = {}) {
  return http.get('/profile/learning-history', { params })
}

export function getInterviewHistory(params = {}) {
  return http.get('/profile/interview-history', { params })
}
