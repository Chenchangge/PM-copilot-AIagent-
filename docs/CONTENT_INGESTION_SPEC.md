# CONTENT_INGESTION_SPEC — 外部知识库与面试题资料整理规范

> 版本 v1 · 状态：设计规范（本阶段不落地数据） · 关联：`PRD.md`（§8 知识库/§9 RAG）、Step 12-2-1 产品体系、Step 12-2-2 数据模型
> 目的：定义一套可持续处理外部知识库、课程资料、Markdown、PDF 转文本、面试题资料等内容的统一整理规范，作为 **ChatGPT（内容分析）→ Claude Code（工程落地）** 之间的交接契约。

---

## 0. 已锁定的最终体系（本文档的输入前提）

- **一级 KnowledgeCategory（11）**：产品基础 / 用户研究 / 产品设计 / 数据分析 / 用户增长 / 商业化 / 策略产品 / B端企业产品 / AI产品 / 项目管理与协作 / 面试与求职
- **一级 ProductDirection（4）**：C端产品经理 / B端产品经理 / AI产品经理 / 数据产品经理
- **Specialization（3）**：策略 / 商业化 / 行业解决方案
- **InterviewType（10）**：产品基础 / 用户研究 / 需求分析 / 产品设计 / 数据分析 / 竞品分析 / 商业化与增长 / AI产品 / 项目复盘 / 行为面试
- **InterviewMode**：综合面试（组卷模式，非题型）
- **EvaluationDimension（5 + 权重）**：产品思维 30% / 需求分析 20% / 逻辑与表达 20% / AI知识 15% / 业务意识 15%
- **知识层级**：KnowledgeCategory →(1:N) KnowledgeTopic →(1:N) KnowledgePoint，加上 Tag 与 KnowledgeSource
- **工具不作为一级分类**，作为 Tag（Figma / Axure / SQL / Excel / XMind）

> 当前 45 个知识点与 30 道面试题仅为 MVP 临时数据，**不作为**本文档所定义最终体系的依据；本规范面向未来外部资料批量导入。

---

## 1. 外部知识资料处理流程

原始资料（Markdown / PDF 转文本 / 课程 / 网页 / 用户提供）→ 按以下流水线逐步处理，**禁止**「原始资料 → KnowledgePoint」直接跳转：

```
原始资料
  ↓  内容抽取（提取正文，剥离页眉页脚/广告/导航/目录）
  ↓  内容清洗（见 §3）
  ↓  去重（见 §4）
  ↓  质量筛选（见 §22 检查清单，不达标的丢弃或打 draft）
  ↓  知识粒度判断（见 §5，过大则拆，过小则并入）
  ↓  一级分类（见 §6，唯一 primary_category）
  ↓  Topic 分类（见 §7，唯一 secondary_topic）
  ↓  Tag（见 §8）
  ↓  Difficulty（见 §9）
  ↓  Dependencies（见 §10）
  ↓  Related Knowledge（见 §11）
  ↓  Source（见 §12）
  ↓  Quality Status（见 §13）
  ↓  Knowledge Dataset（见 §23）
```

每一环节产出可审计的中间结果（分类理由、去重依据、粒度判断），以便回看。

---

## 2. 外部面试题处理流程

```
原始题目（文字/截图转写/题库导出/用户提供）
  ↓  题目清洗（见 §3）
  ↓  去重（见 §18 去重）
  ↓  质量筛选（见 §22）
  ↓  InterviewType（见 §14，唯一主类型）
  ↓  Direction（见 §15，M:N）
  ↓  Specialization（见 §16，M:N，可空）
  ↓  Difficulty（见 §9，与知识难度独立）
  ↓  KnowledgePoint Mapping（见 §17，M:N + relation_type）
  ↓  Expected Points（见 §19）
  ↓  Evaluation Dimension（见 §18）
  ↓  Follow-up Hints（见 §21）
  ↓  Source（见 §12）
  ↓  Quality Status（见 §13）
  ↓  Interview Dataset（见 §24）
```

---

## 3. 内容清洗规则

**知识资料**：
- 剥离非正文：页眉页脚、版权、导航、目录、广告、二维码、外链列表。
- 去除重复段落与冗余铺垫；保留「定义、原理、方法、场景、案例」等有学习价值的正文。
- 统一术语与格式：中英文术语首次出现给中文 + 原文（如「检索增强生成（RAG）」）；代码/公式保留 Markdown 表达。
- 去除与产品经理学习无关的纯营销/软文内容。
- PDF 转文本：先修复断行（段内换行合并）、去除页码与孤立标题、修正乱码。

**面试题资料**：
- 去除「面试官已问/候选已答」等对话噪声，只保留题面。
- 合并同一题的多处表述为单一清晰题面。
- 去除明确的答案前置/剧透（答案移至 reference_answer）。
- 区分「题面」与「参考答案」，二者分离存放。

---

## 4. 去重规则（知识）

候选重复条件（满足任一即进入人工判断）：
1. 标题标准化后高度一致（去除「什么是 / 是什么 / 基础介绍 / 入门 / 详解 / 总结」等修饰）；
2. 核心定义相同（definition 语义等价）；
3. 学习目标相同；
4. 正文高度重叠；
5. 同一 Category + Topic 下高度重合。

处理：
- **同一概念、内容等价** → 合并：保留质量更高版本，`source_refs` 合并，有效内容合并，旧记录置 `deprecated` 并建立 `related_knowledge: deprecated_by`。
- **同主题、深度不同**（如「RAG 入门」vs「RAG 进阶」）→ **不合并**：以 `difficulty` 区分，用 `related_knowledge: related` 或 `dependencies` 关联。
- **部分包含关系** → 若能独立学习（见 §5）则保留；否则并入父知识点。

---

## 5. 知识粒度判断规则

**标准**：一个 KnowledgePoint = 「能够在一次约 5～20 分钟的学习中完整理解，并能独立用于面试表达的最小学习单元」。

**判定口诀**：拆得够小能被一次学完并讲出来，但大到「有独立定义 + 独立面试价值」；若某段内容无法单独形成一道面试题，就不该独立成 Point。

- 合理：RAG、MVP、用户画像、AARRR、漏斗分析、SQL 基础查询
- 过大（应是一个 Category/Topic）：AI、数据分析、产品经理、LLM
- 过小（应是正文内的一段）：RAG 的 chunk_size 选择、SQL 的 GROUP BY 语法、Prompt 的 temperature 取值

---

## 6. Category 分类规则

- 每个 KnowledgePoint **必须且只能有一个 `primary_category`**。
- 判定依据：该知识点的主要**学习目标**落在哪个一级分类，而不是它「提到」了哪个领域。
- 跨领域知识点：选主要学习目标作主分类，其余领域通过 `tags` / `related_knowledge` / `QuestionKnowledge` 表达。
- **禁止**强行把同一知识点放入多个一级分类。
- 分类冲突或新分类需求 → 记录问题，交给 ChatGPT 决策；Claude Code 不自行新增一级分类。

---

## 7. Topic 分类规则

- 每个 KnowledgePoint **必须且只能有一个 `secondary_topic`**（二级主题）。
- Topic 是独立实体（slug + name + category_id + description + sort_order），使用受控词表，避免 `RAG`/`rag`/`检索增强` 漂移。
- 判定：先定 Category，再在该 Category 下选择/新建 Topic。
- 示例：AI产品 → {LLM基础、RAG、Agent、AI评测、模型选择、成本与延迟…}。
- 新建 Topic 需与现有 Topic 去重；跨 Category 的同名概念用不同 slug（如 `ai:rag` 与 `data:指标`）。

---

## 8. Tag 规则

- Tag 用于：跨领域关键词、工具、技术关键词、场景关键词。
- **工具必须优先走 Tag**：Figma / Axure / SQL / Excel / XMind。
- 受控词表：只收录「会被检索/筛选/推荐用到」的标签；**禁止**把正文所有关键词做成 Tag。
- 单个 KnowledgePoint 建议 **≤ 5 个核心 tags**。
- Tag 不是 Category/Topic 的替代品：如果一个词 ≈ 一个 Topic，就用 Topic 而非 Tag。

---

## 9. Difficulty 判断规则

统一 4 级词汇（知识与面试题共用，但为两个独立字段）：

| 级别 | 含义 | 判定 |
| --- | --- | --- |
| 入门 | 零基础可看懂的概念/术语 | 无前置，纯概念 |
| 基础 | 核心方法/框架 | 依赖 0–1 个前置 |
| 进阶 | 涉及权衡/边界/落地细节 | 依赖多个前置，含取舍/成本/风险 |
| 高级 | 专家级/前沿 | 涉及最新研究、复杂系统 |

- **Knowledge difficulty**（学习深度）与 **InterviewQuestion difficulty**（作答难度）是**两个独立概念**，允许不一致：「进阶」知识可被「入门」题考察理解。
- 落地时把当前题目难度「基础/中等/困难」映射为「入门/基础/进阶」（基础→基础、中等→进阶、困难→高级）。

---

## 10. Dependency 判断规则

- `dependencies[]` = 「硬前置知识」，**有向、可多个、AND 语义、不允许循环**。
- 判定：学 B 是否必须先懂 A？是 → A 是 B 的 dependency。
- 例：Embedding → Vector Database → RAG → RAG Evaluation。
- **禁止循环**：落地时拓扑排序校验，检测到环则拒绝（标记 draft + 错误）。
- 不存储「依赖等级」：深度由拓扑排序实时推导。
- 只建立「真正必须」的前置，避免把「相关」误标为「前置」。

---

## 11. Related Knowledge 规则

- `related_knowledge[]` = 「软关联/另见」，双向语义，不参与学习计划排序。
- `relation_type`：`related`（相关延伸）/ `similar`（相似）/ `supersedes`（取代）/ `deprecated_by`（已被取代）。
- 与 `dependencies` 严格区分：dependency = 必须先学；related = 学完可延伸。
- 例：`RAG --related--> Fine-tuning`（相关，非前置）。

---

## 12. Source / Provenance 规则

- `KnowledgeSource` 独立建模：`{id, title, source_type, url, author, published_at, retrieved_at}`。
- KnowledgePoint 与 KnowledgeSource 为 **M:N**：一个知识点可综合多个来源，一个来源可支撑多个知识点。
- **禁止**因多个知识点来自同一来源而合并知识点。
- `source_type` 受控枚举建议：`official_doc / paper / tech_article / book / course / user_provided / internal_original / other`。
- `verified` 状态的知识点 **必须 ≥ 1 条 source_refs**；无来源只能停留 `draft`。

---

## 13. Quality Status 规则

```
draft → reviewed → verified
                      ↓
                 deprecated（保留追溯，不进默认推荐）
```

| 状态 | 含义 | 进入条件 |
| --- | --- | --- |
| draft | 刚导入/刚整理，允许部分字段暂缺 | 任何新导入 |
| reviewed | 结构完整 + 无明显事实错误 | 通过准确性/完整性/可理解性 |
| verified | 学习就绪，可用于面试与推荐 | 通过七维审核 + ≥1 source |
| deprecated | 已合并/替代/过时 | 保留追溯，不推荐 |

**七维审核**（§22 检查清单展开）：准确性 / 完整性 / 可理解性 / PM 相关性 / 面试价值 / 学习价值 / 时效性。

---

## 14. Interview Type 分类规则

- 每道题**必须有且只有一个主 `interview_type_id`**。
- 跨型题用 `secondary_types[]`（M:N）表达，不制造「半主半副」的模糊主类型。
- 10 个专项类型为受控词表；「综合面试」是 `InterviewMode`（组卷规则），**不是** InterviewType，不可赋给某道题。
- 分类判定：看该题**核心考察能力**（如「设计一个功能」→产品设计；「拆解指标」→数据分析）。

---

## 15. Direction 分类规则

- 一道题可属于**多个**方向（`directions[]`，M:N），因为同一个问题对多个方向的面试都成立。
- 例：「如何设计一个用户增长方案？」可同时属于 C端 / AI。
- 判定：该题在该方向的真实面试中是否会被问到。
- 方向与 KnowledgeCategory 是 M:N（`DirectionKnowledge`），与 InterviewType 是 M:N（`DirectionInterviewType`）。

---

## 16. Specialization 分类规则

- Specialization（策略 / 商业化 / 行业解决方案）是**专项标签**，不是新一级方向。
- 一道题可选挂 `specializations[]`（M:N，可空）。
- 判定：题目是否具有明显的策略/商业化/行业纵深属性。
- 实现约束：`DirectionSpecialization` 当前 specialization 数量少，概念模型保留，**落地不搞复杂化**（见附录 C4）。

---

## 17. Question → KnowledgePoint Mapping 规则

- KnowledgePoint 与 InterviewQuestion 为 **M:N**。
- 通过 `QuestionKnowledge` 关联，`relation_type` ∈ **`core` / `related` / `prerequisite`**：
  - `core`：该题**直接考察**该知识点；
  - `related`：与题目相关，但非主要考察点；
  - `prerequisite`：回答该题**需要先具备**该知识。
- 反向查询必须成立：`KnowledgePoint → 有哪些 InterviewQuestion 可考察它`（由 join 派生，不复制数据）。
- 用途：知识学习 → 面试练习（正向）；面试薄弱点 → 知识推荐（反向，`core` 优先）。

---

## 18. Question → EvaluationDimension Mapping 规则

- 一道题可触及多个评价维度（M:N），通过 `evaluation_dimensions[]`（可带本题权重）表达。
- 缺省 = 全局 5 维默认权重；有明确侧重时按题覆盖。
- 判定：回答该题时，哪个维度最能区分好/差。
- 该映射同时服务「AI 评价打维度分」与「薄弱维度 → 知识推荐」。

**两阶段推荐**（与数据模型一致）：
1. 精确级：弱维度 → 当前面试题的 `QuestionKnowledge(core)` → 精确知识点；
2. 兜底级：证据不足时 → `EvaluationKnowledge`（dimension ↔ category 权重）→ Category → KnowledgePoint。

---

## 19. Expected Points 提取规则

- `expected_points[]` = 机器可识别的**关键考察点清单**（评价依据），不是完整答案。
- 提取标准：回答中若「覆盖/体现」了某点，即认为该点达成（非关键词机械匹配）。
- 数量建议：每题 3～6 个，覆盖核心考察点；避免过细（变成逐句 checklist）或过粗（失去区分度）。
- 示例（「设计 RAG 客服产品」）：`[考虑检索质量、考虑成本与延迟、考虑兜底与可解释、考虑数据/知识库准备]`。

---

## 20. Reference Answer 规则

- `reference_answer` = 一份**合理作答示范**，**不代表唯一正确答案**。
- 写法：口语化、有结构、体现产品思维；帮助用户学习「该怎么思考和表达」。
- 与 `expected_points` / `evaluation_rubric` **严格分离**，不合成一个字段：
  - reference_answer = 示范答案（给人看）
  - expected_points = 考察点（给机器判断）
  - evaluation_rubric = 评分细则（给评分标准）

---

## 21. Follow-up Hint 规则

- `follow_up_enabled`：该题是否允许 AI 追问（bool）。
- `follow_up_hints[]`：建议追问角度，供 AI 动态追问参考（非硬性必须逐条执行）。
- 判定：该题是否存在「可深挖」空间（如追问「检索失败怎么办」「成本怎么控制」）。
- 无追问空间的概念题可 `follow_up_enabled=false`。

---

## 22. 数据质量检查清单

**知识**（逐条勾选，全部通过才能 `reviewed`；七维全通过 + 来源才能 `verified`）：
- [ ] 准确性：无事实错误、术语正确
- [ ] 完整性：definition + core_content + pm_focus 齐全
- [ ] 可理解性：适合应届/初级用户，术语有解释
- [ ] PM 相关性：pm_focus 非空，说明对 PM 工作/面试的价值
- [ ] 面试价值：能被 ≥1 道 InterviewQuestion 关联
- [ ] 学习价值：粒度合适（§5）、estimated_minutes 落在 5/10/15/20/30/45/60
- [ ] 时效性：AI 模型/工具/技术类记录 updated_at + last_verified_at，超期标记待复核
- [ ] 来源：verified 必须有 source_refs
- [ ] 唯一性：无重复（§4）、无循环依赖（§10）

**面试题**：
- [ ] 题面清晰、无歧义
- [ ] 有产品经理面试价值
- [ ] 有标准考察点（expected_points 非空）
- [ ] 可追问（或明确 follow_up_enabled=false）
- [ ] 可结构化评价（evaluation_dimensions 明确）
- [ ] 有关联知识点（knowledge_point_ids 非空）
- [ ] 方向/类型/难度合理
- [ ] 无重复题（§18 去重）
- [ ] 不依赖唯一标准答案（reference_answer 仅作参考）

---

## 23. 最终 Knowledge Dataset 格式

**物理载体**：每个 KnowledgePoint = 一个 Markdown 文件（延续现有 `knowledge/data/` 约定），扩展 front matter 承载结构化字段，正文承载内容模板（§3 清洗后）。

**扩展 front matter 示例**：

```yaml
---
id: rag
title: RAG
primary_category: ai-product            # 一级分类 slug
secondary_topic: rag                     # 二级主题 slug
tags: [Embedding, 检索, LLM]              # ≤5，工具/跨领域关键词
difficulty: 进阶                          # 入门/基础/进阶/高级
estimated_minutes: 15                     # 5/10/15/20/30/45/60
dependencies: [embedding, vector-database] # 硬前置，AND，无环
related_knowledge:                        # 软关联
  - id: fine-tuning
    type: related
source_refs: [src-langchain-rag]          # KnowledgeSource slug
quality_status: verified                   # draft/reviewed/verified/deprecated
version: 1
---

# RAG

## 定义
...

## 核心内容
...

## 常见场景
...

## 产品经理关注点
...

## 常见误区
...

## 案例
...
```

**KnowledgeSource 注册表**（共享，`sources.json` 或 `sources/` 目录）：

```json
{
  "src-langchain-rag": {
    "title": "LangChain — Retrieval-Augmented Generation",
    "source_type": "official_doc",
    "url": "https://...",
    "author": "LangChain",
    "published_at": "2024-01-01",
    "retrieved_at": "2026-09-20"
  }
}
```

> 注：现有 `MarkdownLoader` 只解析扁平 front matter（id/title/category/tags/difficulty）；落地时需扩展以解析列表型字段（tags/dependencies/related_knowledge/source_refs）。该扩展属后续工程落地（Claude Code），本阶段不实现。

---

## 24. 最终 Interview Dataset 格式

**物理载体**：延续现有 `interview/data/questions.json`（JSON 数组），扩展字段对齐 InterviewQuestion Schema：

```json
{
  "id": "rag-customer-service-design",
  "question": "设计一个 RAG 客服产品，你会怎么做？",
  "interview_type_id": "product-design",
  "secondary_types": ["ai-product"],
  "directions": ["ai-product", "c-end"],
  "specializations": [],
  "difficulty": "进阶",
  "knowledge_point_ids": [
    { "id": "rag", "relation_type": "core" },
    { "id": "product-design-ia", "relation_type": "related" }
  ],
  "evaluation_dimensions": [
    { "dimension": "AI知识", "weight": 0.4 }
  ],
  "expected_points": [
    "考虑检索质量",
    "考虑成本与延迟",
    "考虑兜底与可解释性",
    "考虑知识库准备"
  ],
  "reference_answer": "先明确用户问题与场景，再判断检索质量如何保证……（示范，非标准答案）",
  "evaluation_rubric": "……（可选，本题评分细则）",
  "follow_up_enabled": true,
  "follow_up_hints": ["检索失败怎么办", "成本如何控制"],
  "tags": ["RAG", "客服"],
  "source_refs": ["src-user-provided-interview-01"],
  "quality_status": "verified",
  "version": 1
}
```

---

## 25. ChatGPT 人工整理 与 Claude Code 落地 的职责边界

**ChatGPT（产品/内容决策）负责**：
- 外部资料理解、知识抽取、概念判断
- 去重判断、粒度判断
- 一级分类、Topic 判断、Tag 判断
- Difficulty、Dependency、Related 关系判断
- 面试题分类、题↔知识点映射、题↔评价维度映射
- 知识缺口分析
- 输出内容（按 §23/§24 格式或等价结构）

**Claude Code（工程落地）负责**：
- 按已确认的数据结构落地（创建/修改 Markdown / JSON / DB）
- 数据校验、Schema validation、import script、migration、测试
- API / repository / service 实现

**Claude Code 不应自行决定**：
- 新增一级知识分类、修改产品方向体系、修改面试类型体系
- 大规模合并知识点、自行判断最终知识体系

**冲突处理**：发现分类冲突 → 记录问题并暂停相关落地，交回 ChatGPT 决策。

---

## 附录：4 个后续实现约束（现在不实现，仅记录）

1. **draft 与 verified 字段完整性不同**：`draft` 允许部分字段暂缺；`verified` 必须满足完整学习就绪要求（含 source_refs）。
2. **QuestionKnowledge relation_type 增加 `prerequisite`**：最终为 `core / related / prerequisite`。
3. **CategoryInterviewType 更适合作为 derived view / cache**，而非核心事实表，避免维护重复关系造成数据不一致。
4. **DirectionSpecialization 当前 specialization 数量少**：概念模型保留 `Direction ↔ Specialization`，实现时不过度工程化。
