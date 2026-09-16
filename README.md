# PM Copilot

面向产品经理求职者的 AI 学习与模拟面试助手。

核心闭环：**学习 → 模拟面试 → AI 评价 → 薄弱点 → 推荐学习 → 再面试**

> 当前为项目初始化阶段：已搭建前后端骨架、路由与页面占位，**尚未实现** RAG、AI 面试、AI 评价等具体业务逻辑，页面均使用 Mock 数据占位。

## 技术栈

| 层 | 技术 |
| --- | --- |
| Frontend | Vue 3 · Vite · Vue Router · Axios · Tailwind CSS |
| Backend | Python · FastAPI |
| AI | BYOK 多模型（DeepSeek / OpenAI / Claude / Gemini 等） |
| Database | SQLite |
| RAG | Chroma / FAISS（后续接入） |

## 目录结构

```
pm-copilot/
├── frontend/          # Vue 3 前端（移动端优先）
├── backend/           # FastAPI 后端
├── knowledge/         # RAG 知识库（数据 / 索引 / 脚本）
├── evaluation/        # AI 评价（提示词 / 评分 schema）
├── docs/              # 架构与接口文档
├── docker-compose.yml # 容器编排（占位）
└── .env.example       # 环境变量模板
```

## 快速开始

### 1. 前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：http://localhost:5173

### 2. 后端

```bash
# 在项目根目录准备环境变量
cp .env.example .env          # 然后填入 DEEPSEEK_API_KEY 等

cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端默认地址：http://localhost:8000 ，接口文档 http://localhost:8000/docs

### 3. 环境变量与 API Key

本项目采用 **BYOK（Bring Your Own Key）**：用户自行配置自己的模型 API，平台不提供统一额度，Key 由后端安全调用，前端代码不接触任何密钥。`.env.example` 中的 `DEEPSEEK_API_KEY` 仅作为本地开发示例。

## 当前状态与 TODO

- [x] 项目初始化、前后端骨架
- [x] 前端路由与页面占位（Mock 数据）
- [x] FastAPI 基础结构（健康检查、占位路由）
- [ ] 数据库模型（SQLite + SQLAlchemy）
- [ ] RAG 知识库（Chroma / FAISS 选型与接入）
- [ ] AI 问答 / 模拟面试 / 评价（BYOK 多模型路由）
- [ ] 前后端接口联调（替换 Mock 数据）
- [ ] 登录与用户体系
- [ ] Docker 容器化完善

## 约定

- Mobile First，优先适配 390×844 / 375×812，同时兼容 PC
- UI 简约、现代、干净、专业，不做传统后台管理风格
- 不提交 `.env` 及任何密钥
