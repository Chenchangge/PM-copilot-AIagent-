# 架构概览

> 产品需求见 [PRD.md](./PRD.md)；接口约定见 [api.md](./api.md)。

> **当前实现状态**：知识库 / RAG（真实 Embedding + Chroma）/ AI 问答 / 模拟面试（题库 + LLM 动态追问）/ AI 评价（后端加权总分 + 知识推荐）/ BYOK 多模型均已真实实现。下文「Step 7-x」为分步实现记录，完整 RAG（Indexing + Retriever + Pipeline + API + 前端 QA UI）现已全部落地。

## 分层

```
Frontend (Vue 3 + Vite + Tailwind，移动端优先)
   ↓ HTTP (Axios / /api)
FastAPI（api/routes → services → db，SQLAlchemy + SQLite）
   ↓
Service → Model Service / Provider Adapter
   ↓
用户自配置模型（BYOK：DeepSeek / OpenAI 兼容 / Custom）

RAG 链路（已实现）：
Markdown → Chunking → Embedding（Custom OpenAI-compatible）
         → Chroma（本地持久化） → Retriever → Prompt → LLM → 回答 + 来源
```

## AI Model Architecture（BYOK）

MVP 采用 **BYOK**：用户自行提供 API Key 并承担第三方模型调用费用，平台不统一提供额度。

```
Vue
 ↓
FastAPI（/api/models）
 ↓
Model Service（CRUD / 连通性测试 / 能力解析）
 ↓
Model Router（能力匹配）
 ↓
Provider Adapter（BaseModelAdapter → DeepSeek / OpenAI 兼容）
 ↓
用户自配置的模型 API
```

- **Provider Adapter 抽象**：`BaseModelAdapter` 定义统一接口（`test_connection` / `generate`），
  `OpenAICompatibleAdapter` 覆盖 OpenAI 兼容协议（DeepSeek / OpenAI / custom）。
- **Capability Registry**：能力（text_generation / reasoning / structured_output /
  multimodal_understanding / image_generation / embedding）由系统按 provider 推导，
  用户不可手工勾选；无法确认的标记为 unknown。
- **Model Router**：`find_models_by_capabilities(required)` 按能力筛选可用模型，
  暂不做成本优化 / 负载均衡 / fallback 等复杂路由。

## RAG Data Pipeline（Step 7-1：Indexing）

```
Markdown
  ↓
MarkdownLoader（扫描 knowledge/data/，解析 front matter → KnowledgeDocument）
  ↓
KnowledgeChunker（按 ## section 切分，过长再按长度切分）
  ↓
Embedding Adapter（BaseEmbeddingAdapter，复用 BYOK / Capability 体系）
  ↓
Chroma（本地 Persistent，collection: pm_copilot_knowledge）
```

- **Step 7-1 只做 Indexing**：把知识建立成可检索的向量索引；Retriever 在 Step 7-2，完整 RAG Pipeline 在 Step 7-3。
- **Embedding 复用 BYOK**：Embedding Model 需 `capabilities.embedding == supported`（模型名含 embedding 时判定），
  经 `get_embedding_adapter()` 接入，不写死某个 Provider；DeepSeek 不提供 Embedding，故不作为 Embedding Provider。
- **幂等与重建**：`build()` 按 chunk_id upsert 幂等；`rebuild()` 清空 collection 重建；Embedding Model 变化时要求 rebuild。
- **索引元数据**：`backend/data/chroma/index_meta.json` 记录 knowledge_hash / embedding_provider / embedding_model / chunking 版本。

## RAG Retriever Layer（Step 7-2）

```
Query
  ↓
Retriever（校验 query / top_k / index 存在性 / embedding model 一致性）
  ↓
Query Embedding（复用 BaseEmbeddingAdapter，与 Index 同 model）
  ↓
Chroma similarity search（Top-K）
  ↓
RetrieverResult（chunk / knowledge / source / distance / score）
```

- **Step 7-2 只实现 Retriever**：本步未实现 LLM Generation / RAG Prompt / RAG Chat / Knowledge QA API（后续步骤已补全）。
- **Model 一致性**：Query Embedding 必须与 Index 的 embedding model 一致（对比 `index_meta.json`），不一致抛 `INDEX_MODEL_MISMATCH`。
- **Top-K / 阈值**：`1 <= top_k <= 20`；可选 `similarity_threshold` / `max_distance` 过滤；空结果返回 `results: []`（不报 500）。
- **相似度语义**：collection 采用 cosine 距离，`score = 1 - distance`；非 cosine 时 score 返回 null，不强行制造分数。

## RAG Pipeline Layer（Step 7-3）

```
Query
  ↓
Retriever（Step 7-2）
  ↓
Context Builder（chunks → LLM Context + sources）
  ↓
Prompt Builder（System / User Query / Knowledge Context 边界清晰）
  ↓
Model Service → BaseModelAdapter.generate()（LLM，复用 BYOK）
  ↓
RAGResult（answer + sources + retrieval_count + usage）
```

- **Step 7-3 只实现 Pipeline**：Retriever + Context Builder + Prompt + LLM Adapter + RAGResult；本步未实现的 RAG API / Knowledge QA UI 已由 Step 7-4 与前端补全（流式 Streaming 仍未实现）。
- **Sources 由 Backend 维护**：sources 来自 Retriever / ContextBuilder，不由 LLM 生成，避免伪造来源。
- **无知识不调用 LLM**：Retriever 返回空时直接返回「知识不足」，不浪费 LLM API、不伪装成 RAG。
- **LLM Model 选择**：需 text_generation 能力，无模型时返回 LLM_MODEL_NOT_FOUND，不 fallback 到 Mock。

## RAG API Layer（Step 7-4）

```
Frontend
  ↓
POST /api/knowledge/qa（KnowledgeQARequest → 校验）
  ↓
RAGPipeline（按 X-User-Id 解析 Embedding + LLM，复用 BYOK）
  ↓
RAGResult → KnowledgeQAResponse（JSON）
```

- **Step 7-4 只做后端 API**：把 RAGPipeline 暴露为 HTTP 端点；前端知识问答 UI 与面试模块均已实现（流式 Streaming 未实现）。
- **Route 保持薄层**：Route 只做「HTTP → 校验 → pipeline.run() → 序列化」，不直接操作 Retriever / Prompt / LLM / Chroma。
- **统一错误映射**：`RAGError` 经全局异常处理器映射为 `{error: {code, message}}` + HTTP 状态（400/404/409/429/502/504/500），不泄漏 Key / traceback / 内部路径。
- **匿名用户**：沿用 `X-User-Id`（缺省 anonymous）隔离模型配置，不新增认证系统。

## Interview Module（Step 8-2，已实现）

```
SetupView（配置）
  ↓
POST /api/interview/sessions（Backend 权威状态源）
  ↓
题库主问题（interview/data/，静态 JSON，不含 LLM 出题）
  ↓
SessionView（聊天式，只渲染不持有状态）
  ↓
POST /api/interview/sessions/{id}/answer（提交回答）
  ↓
InterviewService → Model Adapter（text_generation + reasoning + structured_output）
  ↓
FollowUpDecision（结构化输出：追问 / 换题 / 结束）
  ↓
（Step 10）Evaluation Service → 报告 / 薄弱点 / 推荐学习
```

- **Backend 权威状态**：Session / 当前问题 / 历史 / 追问决策全部由后端维护；Frontend 只渲染。
- **题库 + LLM 追问**：主问题来自静态题库（稳定、带 `knowledge_ids`/`evaluation_points` 元数据）；追问由 LLM 动态生成。
- **状态机**：持久状态 `created / waiting_answer / completed / aborted / failed`；`asking / evaluating` 折叠进一次原子请求，避免刷新后卡死。
- **Step 8-2 已实现**：`InterviewSession` / `InterviewTurn` 数据模型、题库 + `QuestionSelector`、提交回答 → LLM 追问决策（结构化输出 + 重试 + fallback）、4 个 REST 端点、幂等与用户隔离。评分 / 报告 / 推荐留待 Step 10。详见 [interview-design.md](./interview-design.md)。

## Interview Evaluation（Step 9-2，已实现）

- 面试完成后，整场数据 → LLM 结构化评价（5 维度 score + evidence + strengths/weaknesses）→ 后端按固定权重计算总分 → 报告 / 弱项 / 知识推荐。
- 总分由后端计算；Evaluation 独立于 Interview Session（失败不回退面试状态）；MVP 同步评价（无后台队列）。
- **Step 9-2 已实现**：`InterviewEvaluation` 单表（`session_id` UNIQUE）、`EvaluationService`（加载 → 组装 → LLM → 校验重试 → 加权总分 → 知识推荐 → 落库）、`POST/GET /sessions/{id}/evaluation` 两个端点、幂等（completed 不重复调用 LLM）。详见 [interview-evaluation-design.md](./interview-evaluation-design.md)。

## 关键决策

- **BYOK**：用户自配 API Key；Key 由服务端 Secret Storage 抽象持有，绝不明文返回前端、不写日志、不进 Git。
- **RAG 位置**：知识源为 `knowledge/data/*/*.md`，RAG 实现位于 `backend/app/rag/`（loader / chunker / indexer / retriever / pipeline），索引（Chroma）与原始文档分离。
- **评价逻辑**：评价提示词与评分 schema 位于 `backend/app/interview/evaluation.py`（权重常量在 `interview/constants.py`），由 `EvaluationService` 调用；前端只展示结果、不实现评分逻辑。
- **移动端优先**：前端以 `max-width` 容器居中，390×844 / 375×812 优先，PC 下居中显示。

## 数据流（当前）

1. 用户学习 → 浏览知识库 / AI 问答（学习记录历史列表当前为空态占位）
2. 用户发起模拟面试 → 后端从题库选择主问题（去重），LLM 生成动态追问
3. 面试回答 → 后端调用评价服务（`backend/app/services/evaluation_service.py`）产出 5 维评分 + 后端加权总分
4. 评价得到薄弱点 → 规则驱动推荐知识 → 知识详情
5. 回到学习，形成闭环
