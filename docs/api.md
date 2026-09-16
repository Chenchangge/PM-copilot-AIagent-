# 接口约定（占位）

Base URL: `http://localhost:8000`

> 当前阶段仅提供健康检查与占位路由，具体业务接口后续实现。

| 方法 | 路径 | 说明 | 状态 |
| --- | --- | --- | --- |
| GET | `/` | 服务信息 | 可用 |
| GET | `/api/health` | 健康检查 | 可用 |
| GET | `/api/knowledge/` | 知识列表 | 占位（返回空列表） |
| GET | `/api/knowledge/{id}` | 知识详情 | 占位 |
| POST | `/api/interview/sessions` | 创建面试会话 | 占位 |
| GET | `/api/interview/sessions/{id}` | 会话详情 | 占位 |
| POST | `/api/interview/sessions/{id}/report` | 生成评价报告 | 占位 |
| GET | `/api/profile/` | 用户信息 | 占位 |
| GET | `/api/profile/learning-history` | 学习记录 | 占位 |
| GET | `/api/profile/interview-history` | 面试记录 | 占位 |

## 约定

- 请求/响应统一 JSON
- 错误统一返回 `{ "detail": "..." }`（FastAPI 默认）
- 认证鉴权方案待定（后续补充）
