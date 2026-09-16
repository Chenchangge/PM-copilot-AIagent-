# PM Copilot 知识库

面向产品经理求职者的结构化知识库，是 PM Copilot「学习 → 模拟面试 → AI 评价 → 推荐学习」闭环中「学习」环节的内容底座。

> 当前阶段：知识库规范 + 第一批数据。**尚未接入 RAG / Embedding / 向量库**（见文末「未来接入 RAG」）。

## 1. 知识库用途

- 支撑「知识库 / 知识详情」页面的内容展示
- 支撑 AI 知识问答与推荐学习的知识来源
- 支撑面试评价的「薄弱点 → 知识点」映射

## 2. 分类体系

知识按 `category` 分为 6 类，目录与枚举一一对应：

| category | 目录 | 含义 |
| --- | --- | --- |
| `product` | `data/product/` | 产品基础知识（职责、需求、MVP、商业模式等） |
| `design` | `data/design/` | 产品设计知识（用户旅程、PRD、信息架构等） |
| `data` | `data/data/` | 数据分析知识（留存、漏斗、A/B Test 等） |
| `ai` | `data/ai/` | AI 产品知识（LLM、RAG、Agent 等） |
| `tools` | `data/tools/` | 工具与方法（强调「解决什么问题」，非软件教程） |
| `interview` | `data/interview/` | 面试方法与题型（自我介绍、产品设计题等） |

## 3. Markdown Schema

每个知识点是一个独立的 Markdown 文件，文件名 = `id`。

### 3.1 Front Matter（元数据）

```yaml
---
id: mvp
title: MVP
category: product
tags:
  - 产品基础
  - 产品设计
difficulty: beginner
---
```

### 3.2 正文结构

```markdown
# MVP

## 定义
## 核心内容
## 常见场景
## 产品经理关注点
## 面试问题
## 参考答案
```

> Front Matter 的 `id / title / category / difficulty` 必须与正文内容保持一致；`定义 / 核心内容 / 常见场景 / 产品经理关注点 / 面试问题 / 参考答案` 六个章节缺一不可。

完整空白模板见 [`_template.md`](./_template.md)。

## 4. 如何新增知识点

1. 确定分类，选择对应目录（如产品基础 → `data/product/`）
2. 以英文 kebab-case 命名文件（如 `user-persona.md`）
3. 复制 [`_template.md`](./_template.md) 并填写内容
4. 保证 `id` 全局唯一
5. 运行校验：`python knowledge/scripts/validate_knowledge.py`

## 5. id 命名规则

- 英文、小写、kebab-case（`user-persona`、`funnel-analysis`、`rag`）
- 全局唯一、稳定（后续页面/推荐学习会引用 id）
- 不使用中文、空格、下划线

## 6. category / difficulty 枚举

**category**（固定，不可自定义）：

```
product | design | data | ai | tools | interview
```

**difficulty**（固定三档）：

```
beginner（入门） | intermediate（进阶） | advanced（高级）
```

## 7. 内容质量要求

每个知识点都应回答一条主线：

```
它是什么？ → 为什么重要？ → 什么时候用？ → PM 该关注什么？ → 面试怎么问？ → 该怎么答？
```

具体原则：

- **不复制互联网文章**，需重新组织内容
- **不堆术语**，避免空洞的「增长飞轮 / 全链路闭环」式表达
- **面试答案要能真正说出口**，口语化、有结构、体现产品思维，避免教科书与明显 AI 味
- **技术知识要讲产品意义**（如 Embedding 不能只讲向量，还要讲「AI 产品经理为什么需要懂」）
- **RAG / Agent 等高级知识**重点写「PM 需要理解什么、能设计什么、有哪些产品风险」，不写成后端开发教程

## 8. 当前知识点数量

见 [`index/index.json`](./index/index.json) 的 `total` 字段（由人工维护，与 `data/` 内容保持一致）。

## 9. 后续如何扩充

- 按第 4 步流程新增文件，再更新 `index/index.json`
- 先保证质量再追求数量，不合并重复主题凑数
- 未来可通过「页面 → 新增知识点 → 统一 Schema → 保存 → 知识库」流程管理，数据与前端代码解耦

## 10. 未来如何接入 RAG（规划，未实现）

知识库当前是**纯 Markdown + 元数据**，未来技术方案（产品层面见 `docs/PRD.md` 第 9 章）：

```
Markdown → 文本切分 → Embedding → Chroma / FAISS → Top-K 检索 → 生成回答 + 来源
```

> 本阶段**尚未进入 RAG**：未实现 Embedding、向量库、Retriever、Top-K 检索、切分流水线、向量索引、RAG API。当前 `scripts/` 仅含 Markdown 元数据校验脚本，不含任何向量化逻辑。
