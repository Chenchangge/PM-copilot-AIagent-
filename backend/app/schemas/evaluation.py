"""面试评价 API 的请求 / 响应 Schema 与 LLM 结构化输出模型。

区分两类模型：
- LLM 结构化输出模型（EvidenceItem / DimensionEvaluation / EvaluationOutput）：LLM 返回的原始评价结构，
  由 `interview/evaluation.py` 校验后构造。
- 报告模型（DimensionReport / EvaluationReport / RecommendedKnowledge）：`GET/POST /evaluation` 的响应契约。
"""
from datetime import datetime

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """单条证据：引用某条真实 turn 的客观观察。"""

    turn_id: int
    observation: str
    impact: str


class DimensionEvaluation(BaseModel):
    """单个维度的评分结果（LLM 输出）。"""

    dimension: str
    score: float
    evidence: list[EvidenceItem] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class EvaluationOutput(BaseModel):
    """LLM 评价结构化输出的完整模型（不含总分，总分由后端计算）。"""

    dimensions: list[DimensionEvaluation]
    overall_strengths: list[str] = Field(default_factory=list)
    overall_weaknesses: list[str] = Field(default_factory=list)
    summary: str = ""


class RecommendedKnowledge(BaseModel):
    """一条知识点推荐。"""

    knowledge_id: str
    title: str
    category: str
    reason: str


class DimensionReport(BaseModel):
    """报告中的单个维度（带权重 + 整型分数）。"""

    dimension: str
    weight: float
    score: int
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    """评价报告响应契约（对应设计 §19）。"""

    evaluation_id: int
    session_id: str
    status: str
    overall_score: int
    summary: str
    direction: str
    difficulty: str
    interview_type: str
    dimensions: list[DimensionReport]
    overall_strengths: list[str] = Field(default_factory=list)
    overall_weaknesses: list[str] = Field(default_factory=list)
    recommended_knowledge: list[RecommendedKnowledge] = Field(default_factory=list)
    created_at: datetime
