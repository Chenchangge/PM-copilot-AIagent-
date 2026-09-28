# evaluation — AI 面试评价

> **当前定位**：本目录是早期设计阶段遗留的产物（提示词 / schema 草案），已**不再承载运行时业务代码**。
> 真正的评价实现位于：
> - 提示词 + 结构化解析 + 校验 + 总分计算 + 知识推荐：`backend/app/interview/evaluation.py`
> - 评价编排 + 落库 + 幂等：`backend/app/services/evaluation_service.py`
> - 评分权重 / 维度常量：`backend/app/interview/constants.py`
> - 报告 / 推荐 Schema：`backend/app/schemas/evaluation.py`

## 已实现的评价体系

- **5 个固定维度（权重合计 100%）**：

| 维度 | 权重 |
| --- | --- |
| 产品思维 | 30% |
| 需求分析 | 20% |
| 逻辑与表达 | 20% |
| AI 知识 | 15% |
| 业务意识 | 15% |

- **流程**：

```
Structured Output（LLM 输出 JSON）
 ↓
Schema Validation（维度 / 分数 / evidence.turn_id 真实性校验）
 ↓
Retry（校验失败最多重试一次）
 ↓
Backend Weighted Score（后端按固定权重计算总分，非 LLM 自由生成）
 ↓
Evidence（可追溯的评价依据）
 ↓
Weakness（弱项判定，score < 70）
 ↓
Knowledge Recommendation（规则驱动，弱维度 → 真实 knowledge_id）
```

## 目录（遗留草案）

- `prompts/` — 早期评价提示词草案（已由 `backend/app/interview/evaluation.py` 内联 prompt 取代）
- `schemas/` — 早期评分 schema 草案（已由 `backend/app/schemas/evaluation.py` Pydantic 模型取代）
