# 接口约定

Base URL: `http://localhost:8010`

> 已实现：健康检查、AI 模型配置（BYOK）、知识库（列表 / 详情）、知识库 AI 问答（RAG）、模拟面试（会话 / 追问 / 结束）、面试评价（报告 / 推荐）。仅 `profile` 三个接口仍为占位（学习 / 面试历史列表待接线）。

| 方法 | 路径 | 说明 | 状态 |
| --- | --- | --- | --- |
| GET | `/` | 服务信息 | 可用 |
| GET | `/api/health` | 健康检查 | 可用 |
| GET | `/api/models` | 模型配置列表 / 增删改 / 连接测试 / 能力解析 | 可用 |
| POST | `/api/knowledge/qa` | 知识库 AI 问答（RAG） | 可用 |
| GET | `/api/knowledge` | 知识列表（Markdown 数据源，支持 `?category=`） | 可用（Step 10-2） |
| GET | `/api/knowledge/{knowledge_id}` | 知识详情（slug） | 可用（Step 10-2） |
| POST | `/api/interview/sessions` | 创建面试会话（返回首题） | 可用 |
| GET | `/api/interview/sessions/{id}` | 会话详情与历史（恢复） | 可用 |
| POST | `/api/interview/sessions/{id}/answer` | 提交回答（返回追问/下一题/结束） | 可用 |
| POST | `/api/interview/sessions/{id}/finish` | 主动结束面试 | 可用 |
| POST | `/api/interview/sessions/{id}/evaluation` | 触发面试评价（同步返回报告） | 可用（Step 9-2） |
| GET | `/api/interview/sessions/{id}/evaluation` | 获取面试评价/报告 | 可用（Step 9-2） |
| GET | `/api/profile/` | 用户信息 | 占位 |
| GET | `/api/profile/learning-history` | 学习记录 | 占位 |
| GET | `/api/profile/interview-history` | 面试记录 | 占位 |

## 约定

- 请求 / 响应统一 JSON。
- 业务错误统一返回 `{ "error": { "code": "...", "message": "..." } }`；`code` 为机器可读错误码，`message` 为友好中文提示。
- 认证：MVP 无登录，采用匿名用户标识（`X-User-Id` 请求头），缺省回退为 `anonymous`。

---

## 知识库 AI 问答（RAG QA）

### Purpose

基于 PM Copilot 知识库回答用户问题。后端执行「检索 → 上下文 → 提示词 → 文本生成模型」完整 RAG 链路，并将答案与知识来源一并返回。

### Header

| 头 | 说明 | 缺省 |
| --- | --- | --- |
| `X-User-Id` | 匿名用户 ID，用于隔离模型配置（BYOK） | `anonymous` |

### Request

`POST /api/knowledge/qa`

```json
{
  "query": "什么是 MVP？",
  "top_k": 5,
  "similarity_threshold": null,
  "max_distance": null
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `query` | string | 是 | 用户问题，trim 后非空，≤ 2000 字符 |
| `top_k` | int | 否 | 检索条数，1～20，默认 5 |
| `similarity_threshold` | float \| null | 否 | cosine 相似度阈值，0.0～1.0 |
| `max_distance` | float \| null | 否 | cosine 距离阈值，0.0～2.0 |

`similarity_threshold` 与 `max_distance` 表达同一过滤概念，**不可同时传入**，否则返回 400 `RETRIEVAL_THRESHOLD_CONFLICT`。

### Response

`200 OK`

```json
{
  "query": "什么是 MVP？",
  "answer": "MVP 是最小可行产品……",
  "sources": [
    {
      "knowledge_id": "mvp",
      "chunk_id": "mvp:0:0",
      "title": "MVP",
      "category": "product",
      "section": "定义",
      "source_path": "knowledge/data/product/mvp.md",
      "score": 0.91
    }
  ],
  "retrieval_count": 1,
  "provider": "deepseek",
  "model": "deepseek-flash",
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50,
    "total_tokens": 150
  }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `query` | string | 回显用户问题（trim 后） |
| `answer` | string | AI 基于知识库生成的回答 |
| `sources` | array | 检索到的知识来源（见下） |
| `retrieval_count` | int | 命中来源数量 |
| `provider` / `model` | string \| null | 实际使用的文本生成模型 |
| `usage` | object \| null | token 用量（无 LLM 调用时为 null） |

### Sources

`sources` 由 **RAGPipeline → Retriever** 生成，**不是 LLM 自己生成的**——避免模型伪造来源。API 仅做序列化，前端无需猜测来源。`source_path` 为项目相对路径（`knowledge/data/...`），不含服务器绝对路径。

### Empty Retrieval

知识库没有足够相关内容时，**不调用 LLM**，返回正常业务响应（HTTP 200）：

```json
{
  "query": "什么是 RAG",
  "answer": "当前知识库中没有找到足够相关的信息，暂时无法基于知识库回答该问题。",
  "sources": [],
  "retrieval_count": 0,
  "provider": "deepseek",
  "model": "deepseek-flash",
  "usage": null
}
```

这不是服务器错误，故返回 200 而非 500。

### Errors

统一格式：`{ "error": { "code": "...", "message": "..." } }`

| HTTP | code | 说明 |
| --- | --- | --- |
| 400 | `RETRIEVAL_INVALID_QUERY` | query 为空 / 超长 |
| 400 | `RETRIEVAL_INVALID_TOP_K` | top_k 超出 1～20 |
| 400 | `RETRIEVAL_INVALID_THRESHOLD` | threshold 超出合理范围或非有限数字 |
| 400 | `RETRIEVAL_THRESHOLD_CONFLICT` | 同时传入两种 threshold |
| 400 | `EMBEDDING_MODEL_NOT_FOUND` | 未配置 Embedding 模型 |
| 400 | `LLM_MODEL_NOT_FOUND` | 未配置文本生成模型 |
| 404 | `INDEX_NOT_FOUND` | 知识库索引不存在，需先构建 |
| 409 | `INDEX_MODEL_MISMATCH` | 索引与当前 Embedding 模型不一致，需重建 |
| 429 | `RATE_LIMITED` | 上游模型服务限流 |
| 502 | `INVALID_API_KEY` | 上游模型服务拒绝 API Key |
| 502 | `MODEL_NOT_FOUND` / `INVALID_BASE_URL` / `NETWORK_ERROR` / `PROVIDER_ERROR` | 上游模型服务错误 |
| 504 | `TIMEOUT` | 上游模型服务超时 |
| 500 | `UNKNOWN` | 服务端内部错误 |

---

## 模拟面试（Interview）

### Purpose

多轮「主问题 + 动态追问」的 AI 模拟面试。主问题来自题库（`interview/data/questions.json`），追问由 LLM 基于回答动态生成。

### Header

| 头 | 说明 | 缺省 |
| --- | --- | --- |
| `X-User-Id` | 匿名用户 ID，用于隔离 Session | `anonymous` |

### 创建 Session

`POST /api/interview/sessions`

```json
{ "direction": "AI产品经理", "difficulty": "中等", "interview_type": "AI产品" }
```

- 方向：`C端产品经理 / B端产品经理 / AI产品经理 / 数据产品经理`
- 难度：`基础 / 中等 / 困难`
- 类型：`产品基础 / 产品设计 / 需求分析 / 数据分析 / AI产品 / 综合面试`

响应（201）：

```json
{
  "session_id": "intv-xxx",
  "status": "waiting_answer",
  "current_round": 1,
  "question": { "turn_id": 1, "content": "……", "type": "main", "round": 1 }
}
```

### 获取 Session（刷新/恢复）

`GET /api/interview/sessions/{id}` → `{ "session": {...}, "current_question": {...} | null, "turns": [...] }`

### 提交回答

`POST /api/interview/sessions/{id}/answer`

```json
{ "answer": "……", "client_request_id": "req-xxx" }
```

响应：

```json
{
  "session_id": "intv-xxx",
  "status": "waiting_answer",
  "current_round": 1,
  "action": "follow_up",
  "question": { "turn_id": 2, "content": "追问……", "type": "follow_up", "round": 1 }
}
```

`action`：`follow_up`（追问）/ `next_question`（下一主问题）/ `completed`（面试结束）。`client_request_id` 用于幂等去重，重复提交不会产生重复 Turn / 重复 LLM 调用。

### 结束面试

`POST /api/interview/sessions/{id}/finish` → Session，`status=completed`、`end_reason=manual`（幂等）。

### Errors

| HTTP | code | 说明 |
| --- | --- | --- |
| 400 | `INTERVIEW_MODEL_NOT_FOUND` | 未配置满足 text_generation+reasoning+structured_output 的模型 |
| 400 | `INTERVIEW_INVALID_ANSWER` | 回答为空 / 超长 |
| 404 | `INTERVIEW_SESSION_NOT_FOUND` | Session 不存在 / 不属于该用户 |
| 409 | `INTERVIEW_SESSION_COMPLETED` / `INTERVIEW_INVALID_STATE` | 已结束 / 状态不允许 |
| 429 / 502 / 504 | `RATE_LIMITED` / `PROVIDER_ERROR` / `TIMEOUT` 等 | 上游模型错误（复用 Step 6） |

---

## 模拟面试评价（Interview Evaluation）

面试结束后（Session `completed`），把整场面试（主问题 + 追问 + 候选回答）交给 LLM 输出 5 个维度的结构化评价，由后端加权计算总分并生成报告。详见 [interview-evaluation-design.md](./interview-evaluation-design.md)。

### 触发评价（同步）

`POST /api/interview/sessions/{id}/evaluation`

- 前提：Session 必须 `completed`，否则 `409 INTERVIEW_INVALID_STATE`。
- 幂等：已有 `completed` 评价时直接返回既有报告，不重复调用 LLM。
- 成功返回完整评价报告（`status=completed`）。

### 获取评价

`GET /api/interview/sessions/{id}/evaluation`

- 已生成评价 → 200 返回报告（`status=completed`）。
- 评价 `failed` → 200 返回 `{ "session_id": "...", "status": "failed", "error": "..." }`。
- 无评价记录 → `404 EVALUATION_NOT_FOUND`。

### 报告结构

```json
{
  "evaluation_id": 1,
  "session_id": "intv-xxx",
  "status": "completed",
  "overall_score": 82,
  "summary": "一句话总结",
  "direction": "AI产品经理",
  "difficulty": "中等",
  "interview_type": "AI产品",
  "dimensions": [
    { "dimension": "产品思维", "weight": 0.30, "score": 84, "strengths": ["..."], "weaknesses": ["..."], "evidence": [{ "turn_id": 1, "observation": "...", "impact": "..." }] }
  ],
  "overall_strengths": ["..."],
  "overall_weaknesses": ["..."],
  "recommended_knowledge": [{ "knowledge_id": "rag", "title": "RAG", "category": "ai", "reason": "..." }],
  "created_at": "..."
}
```

### Errors

| HTTP | code | 说明 |
| --- | --- | --- |
| 400 | `INTERVIEW_MODEL_NOT_FOUND` | 未配置满足 text_generation+reasoning+structured_output 的模型 |
| 404 | `INTERVIEW_SESSION_NOT_FOUND` | Session 不存在 / 不属于该用户 |
| 404 | `EVALUATION_NOT_FOUND` | 尚无评价记录（GET） |
| 409 | `INTERVIEW_INVALID_STATE` | Session 未完成 |
| 502 | `EVALUATION_FAILED` | LLM 结构化输出多次无效 |
| 429 / 502 / 504 | `RATE_LIMITED` / `PROVIDER_ERROR` / `TIMEOUT` 等 | 上游模型错误（复用 Step 6） |
