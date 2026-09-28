"""SQLAlchemy 模型注册。"""
from app.models.ai_model import UserModelConfig
from app.models.interview import InterviewEvaluation, InterviewSession, InterviewTurn
from app.models.learning import KnowledgeLearningRecord, LearningPlan, LearningPlanDay, LearningPlanTask
from app.models.taxonomy import (
    DirectionInterviewType,
    DirectionKnowledge,
    InterviewType,
    KnowledgeCategory,
    KnowledgePoint,
    KnowledgePointDependency,
    KnowledgePointRelated,
    KnowledgePointTag,
    KnowledgeTopic,
    ProductDirection,
    QuestionKnowledge,
    Specialization,
    Tag,
)

__all__ = [
    "UserModelConfig",
    "InterviewSession",
    "InterviewTurn",
    "InterviewEvaluation",
    # 分类体系
    "ProductDirection",
    "Specialization",
    "KnowledgeCategory",
    "KnowledgeTopic",
    "Tag",
    "InterviewType",
    "DirectionKnowledge",
    "DirectionInterviewType",
    "KnowledgePoint",
    "KnowledgePointTag",
    "KnowledgePointDependency",
    "KnowledgePointRelated",
    "QuestionKnowledge",
    # 学习计划
    "LearningPlan",
    "LearningPlanDay",
    "LearningPlanTask",
    "KnowledgeLearningRecord",
]
