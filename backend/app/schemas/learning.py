"""学习计划 API 的请求 / 响应 Schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.learning.constants import (
    CURRENT_LEVELS,
    DAILY_MINUTES_OPTIONS,
    DIRECTIONS,
    INTENSITIES,
    TARGET_TYPES,
)


# ---- 请求 ----

class EstimateRequest(BaseModel):
    target_type: str
    target_id: str
    current_level: str
    daily_minutes: int
    intensity: str
    direction_id: str | None = None

    @field_validator("target_type")
    @classmethod
    def _check_target_type(cls, v: str) -> str:
        if v not in TARGET_TYPES:
            raise ValueError(f"非法的目标类型：{v}")
        return v

    @field_validator("current_level")
    @classmethod
    def _check_level(cls, v: str) -> str:
        if v not in CURRENT_LEVELS:
            raise ValueError(f"非法的当前水平：{v}")
        return v

    @field_validator("daily_minutes")
    @classmethod
    def _check_minutes(cls, v: int) -> int:
        if v not in DAILY_MINUTES_OPTIONS:
            raise ValueError(f"非法的每日学习时间：{v}")
        return v

    @field_validator("intensity")
    @classmethod
    def _check_intensity(cls, v: str) -> str:
        if v not in INTENSITIES:
            raise ValueError(f"非法的学习强度：{v}")
        return v

    @field_validator("direction_id")
    @classmethod
    def _check_direction(cls, v: str | None) -> str | None:
        if v is not None and v not in DIRECTIONS:
            raise ValueError(f"非法的面试方向：{v}")
        return v


class CreatePlanRequest(EstimateRequest):
    selected_days: int = 0  # 0 = 接受推荐
    title: str | None = None

    @field_validator("selected_days")
    @classmethod
    def _check_days(cls, v: int) -> int:
        if v < 0 or v > 1000:
            raise ValueError("非法的学习周期")
        return v


class UpdatePlanRequest(BaseModel):
    daily_minutes: int | None = None
    selected_days: int | None = None
    intensity: str | None = None

    @field_validator("daily_minutes")
    @classmethod
    def _check_minutes(cls, v: int | None) -> int | None:
        if v is not None and v not in DAILY_MINUTES_OPTIONS:
            raise ValueError(f"非法的每日学习时间：{v}")
        return v

    @field_validator("intensity")
    @classmethod
    def _check_intensity(cls, v: str | None) -> str | None:
        if v is not None and v not in INTENSITIES:
            raise ValueError(f"非法的学习强度：{v}")
        return v

    @field_validator("selected_days")
    @classmethod
    def _check_days(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 1000):
            raise ValueError("非法的学习周期")
        return v


# ---- 分类体系（供学习计划 UI 选择目标）----

class CategoryOut(BaseModel):
    id: str
    name: str


class TopicOut(BaseModel):
    id: str
    name: str
    category_id: str


class TaxonomyOut(BaseModel):
    directions: list[str] = Field(default_factory=list)
    categories: list[CategoryOut] = Field(default_factory=list)
    topics: list[TopicOut] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    levels: list[str] = Field(default_factory=list)
    daily_minutes: list[int] = Field(default_factory=list)
    intensities: list[str] = Field(default_factory=list)
    day_choices: list[int] = Field(default_factory=list)


# ---- estimate ----

class TargetInfo(BaseModel):
    type: str
    id: str
    name: str


class PrerequisiteInfo(BaseModel):
    id: str
    title: str


class EstimateResult(BaseModel):
    target: TargetInfo
    knowledge_count: int
    total_minutes: int
    recommended_days: int
    recommended_daily_minutes: int
    key_topics: list[str] = Field(default_factory=list)
    prerequisites: list[PrerequisiteInfo] = Field(default_factory=list)
    explanation: str = ""
    day_choices: list[int] = Field(default_factory=list)


# ---- 任务 / Day / 计划 ----

class TaskOut(BaseModel):
    id: int
    knowledge_point_id: str
    title: str
    category: str = ""
    difficulty: str = ""
    estimated_minutes: int
    status: str
    completed_at: datetime | None = None


class DayOut(BaseModel):
    id: int
    day_number: int
    planned_minutes: int
    completed_minutes: int
    progress_percent: int
    status: str
    tasks: list[TaskOut] = Field(default_factory=list)


class RecommendedInterview(BaseModel):
    eligible: bool
    ratio: float
    direction: str | None = None
    interview_type: str | None = None
    knowledge_ids: list[str] = Field(default_factory=list)


class PlanDetailOut(BaseModel):
    id: int
    title: str
    target_type: str
    target_id: str
    target_name: str
    direction_id: str | None = None
    direction_name: str | None = None
    current_level: str
    daily_minutes: int
    intensity: str
    recommended_days: int
    selected_days: int
    total_knowledge_points: int
    total_estimated_minutes: int
    completed_knowledge_points: int
    completed_minutes: int
    progress_percent: int
    status: str
    current_day_number: int = 1
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    days: list[DayOut] = Field(default_factory=list)
    recommended_interview: RecommendedInterview | None = None


class PlanListItem(BaseModel):
    id: int
    title: str
    target_name: str
    status: str
    progress_percent: int
    selected_days: int
    total_knowledge_points: int
    completed_knowledge_points: int
    current_day_number: int
    created_at: datetime


class TodayProgress(BaseModel):
    done: int
    total: int
    minutes: int


class HomeSummaryOut(BaseModel):
    active_plan: PlanListItem | None = None
    today_tasks: list[TaskOut] = Field(default_factory=list)
    overall_progress: int = 0
    today_progress: TodayProgress = TodayProgress(done=0, total=0, minutes=0)
    recommended_next_action: str = ""


class PlanListResponse(BaseModel):
    items: list[PlanListItem] = Field(default_factory=list)
