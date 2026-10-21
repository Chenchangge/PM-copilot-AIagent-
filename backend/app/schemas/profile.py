"""用户中心：学习记录 / 面试记录响应 Schema。"""
from datetime import datetime

from pydantic import BaseModel, Field


class LearningHistoryItem(BaseModel):
    id: int
    knowledge_point_id: str
    title: str
    category: str = ""
    topic: str = ""
    status: str
    duration_minutes: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class LearningHistoryResponse(BaseModel):
    items: list[LearningHistoryItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class InterviewHistoryItem(BaseModel):
    session_id: str
    direction: str
    difficulty: str
    interview_type: str
    status: str
    overall_score: int | None = None
    evaluation_status: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    can_continue: bool = False
    can_view_evaluation: bool = False


class InterviewHistoryResponse(BaseModel):
    items: list[InterviewHistoryItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
