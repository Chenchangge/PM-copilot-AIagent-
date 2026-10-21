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
    """单个维度的评分结果（LLM 输出）。

    score=None 表示本场没有该维度的有效回答/证据（未考察），不得用 50 之类中位分填充。
    """

    dimension: str
    score: float | None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class PointResult(BaseModel):
    """评分点达成情况：met=✓ / partial=△ / missed=✗ / unknown=未判定。"""

    point: str
    status: str = "unknown"
    comment: str = ""


class QuestionReview(BaseModel):
    """LLM 对单条 turn 的逐题复盘。"""

    turn_id: int
    score: float | None = None
    point_results: list[PointResult] = Field(default_factory=list)
    comment: str = ""


class EvaluationOutput(BaseModel):
    """LLM 评价结构化输出的完整模型（不含总分，总分由后端计算）。"""

    dimensions: list[DimensionEvaluation]
    question_reviews: list[QuestionReview] = Field(default_factory=list)
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
    """报告中的单个维度（带权重 + 整型分数；score=None 表示本场未考察）。"""

    dimension: str
    weight: float
    score: int | None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class TurnReviewReport(BaseModel):
    """逐题复盘：题号 + 题干 + 我的回答 + 该题得分 + 评分点 + 参考答案。"""

    turn_id: int
    round_number: int
    question_type: str  # main | follow_up
    follow_up_type: str | None = None
    question: str
    answer: str = ""
    answer_length: int | None = None
    score: int | None = None
    point_results: list[PointResult] = Field(default_factory=list)
    reference_answer: str = ""
    knowledge_ids: list[str] = Field(default_factory=list)
    comment: str = ""


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
    turn_reviews: list[TurnReviewReport] = Field(default_factory=list)
    overall_strengths: list[str] = Field(default_factory=list)
    overall_weaknesses: list[str] = Field(default_factory=list)
    recommended_knowledge: list[RecommendedKnowledge] = Field(default_factory=list)
    created_at: datetime
