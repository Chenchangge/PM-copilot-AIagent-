# PM Copilot

面向产品经理求职者的 AI 学习与模拟面试助手。

## 核心问题

> 看过知识 ≠ 真正理解 ≠ 能够在面试中表达出来。

产品经理求职者普遍「看懂了」知识，却难以在面试中「讲清楚」，知识与表达之间缺乏反馈闭环。PM Copilot 通过一条真实可运行的学习闭环解决这个问题：

```
学习 → AI 问答 → 模拟面试 → AI 动态追问 → AI 评价 → 发现薄弱点 → 推荐知识 → 再学习
```

---

## 已实现能力

- **知识库**：45 个 Markdown 知识点（`knowledge/data/`），提供 `GET /api/knowledge`（列表 / 分类）与 `GET /api/knowledge/{slug}`（结构化详情：定义 / 核心内容 / 场景 / 关注点 / 面试题+参考答案）。
- **AI 知识问答（RAG）**：Markdown → 分块 → Embedding → Chroma → 检索 → LLM 生成回答（带来源引用）。
- **AI 模拟面试**：静态题库（30 题）+ LLM 动态追问 + 结构化输出，多轮主问题 + 追问。
- **AI 面试评价**：五维评分（产品思维/需求分析/逻辑与表达/AI知识/业务意识）+ 可追溯 Evidence + 后端加权总分 + 规则驱动的知识推荐（与评价推荐点形成学习闭环）。
- **多模型 / BYOK**：用户自行配置模型 API Key（平台不提供统一额度），支持 DeepSeek 与 Custom OpenAI-compatible Provider；模型能力由 Capability Registry 推导（文本生成 / 推理 / 结构化输出 / 多模态 / 图像生成 / Embedding），按功能路由。Embedding 当前使用 Custom OpenAI-compatible（`custom / text-embedding-v4`），非 Qwen 专属 Provider。Key 全程由后端安全处理，不落前端 / 日志 / Git。

## 技术栈

| 层 | 技术 |
| --- | --- |
| Frontend | Vue 3 · Vite · Vue Router · Axios · Tailwind CSS · markdown-it |
| Backend | Python · FastAPI · SQLAlchemy · SQLite |
| AI | BYOK 多模型（能力注册 + 路由 + Provider Adapter） |
| RAG | Chroma + Markdown 加载 / 分块 / 检索 / Prompt |
| 面试/评价 | 题库 JSON + LLM 结构化输出 + 校验 + 重试 + 加权评分 |

## 架构

```
Frontend (Vue 3, Mobile First)
   ↓ /api
FastAPI（api/routes → services → db / Model Router）
   ↓
Provider Adapter（DeepSeek / OpenAI 兼容）── 用户自配置模型（BYOK）
```

```
Markdown 知识库 → Chunking → Embedding → Chroma → Retriever → LLM → 知识问答
```

## AI Evaluation

面试结束后，整场问答（主问题 + 追问 + 候选回答）交给 LLM 输出 5 个维度的结构化评价，最终总分由后端按固定 Rubric 加权计算：

| 维度 | 权重 |
| --- | --- |
| 产品思维 | 30% |
| 需求分析 | 20% |
| 逻辑与表达 | 20% |
| AI 知识 | 15% |
| 业务意识 | 15% |

```
LLM 结构化输出
 ↓
Schema 校验（维度 / 分数 / evidence.turn_id 真实性）
 ↓
Evidence（可追溯的评价依据）
 ↓
Weakness（弱项判定）
 ↓
后端加权总分（calculate_overall_score，非 LLM 自由生成）
 ↓
知识推荐（弱维度 → 真实 knowledge_id）
```

**关键设计**：最终总分由后端按固定 Rubric 计算，而不是直接使用 LLM 自由生成的总分，保证评分可复现、可解释。

## RAG Evaluation

真实数据（截至当前）：

| 项 | 值 |
| --- | --- |
| 知识文档 | 45 |
| 分块 | 270 |
| Embedding 模型 | text-embedding-v4 |
| Provider | custom（OpenAI-compatible） |
| 维度 | 1024 |
| 批大小 | 10 |
| 向量库 | Chroma（本地持久化，cosine） |

**Mock → Real 对比**（真实测试现象，非系统化指标）：

- **Mock Embedding**：查询「什么是 RAG？」时，Top-K 容易检索到与问题语义无关的内容。
- **Real Embedding**：同样查询下，Top-K 集中于 `RAG / 定义 / 核心内容 / 产品经理关注点 / 应用场景` 等语义相关内容。

> 仅记录真实测试现象，不编造准确率 / Recall / Precision / 用户满意度等指标。

## 快速开始

### 1. 前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：http://localhost:5173（通过 Vite 代理 `/api` 到后端 8010）。

### 2. 后端

```bash
# 在项目根目录准备环境变量（可选）
cp .env.example .env

cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate  |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
```

后端地址：http://localhost:8010 · 接口文档：http://localhost:8010/docs

### 3. 配置 AI 模型（BYOK）

启动后进入「我的 → AI 模型 / API」，添加你自己的模型（DeepSeek / OpenAI / OpenAI 兼容）。模拟面试、AI 评价、知识问答都需要先配置模型。API Key 仅保存在后端，前端代码不接触任何密钥，请勿把 Key 提交进 Git。

## 当前状态

- 核心闭环（学习 → 面试 → 评价 → 推荐知识 → 再学习）已端到端可用。
- 学习记录 / 面试记录 / 学习计划目前为**诚实空态**（未实现持久化），不展示任何伪造数据。

## 已知限制

- **知识问答需要 Embedding 模型**：当前默认演示环境通常只配置 DeepSeek（提供文本生成，**不提供 Embedding**），因此 RAG 知识问答需额外配置一个 OpenAI 兼容的 Embedding 模型后才能完成端到端演示；其余能力（面试 / 评价）仅需文本生成模型即可。
- **npm audit** 存在 Vite 相关传递依赖告警（非运行阻断，未强制升级）。
- 匿名使用：MVP 无登录，用户身份由浏览器本地生成的匿名 ID 标识，数据按该 ID 隔离。

## 安全约定

- Mobile First，优先适配 390×844 / 375×812，同时兼容 PC。
- 不提交 `.env` 及任何密钥；API Key 不出现在响应 / localStorage / URL / 日志。
