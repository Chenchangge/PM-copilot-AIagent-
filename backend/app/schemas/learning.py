"""学习计划 API 的请求 / 响应 Schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.learning.constants import (
    CURRENT_LEVELS,
    DAILY_MINUTES_OPTIONS,
    DIRECTIONS,
    INTENSITIES,
    TARGET_TYPES,
)


# ---- 请求 ----

class EstimateRequest(BaseModel):
    # 二选一：path_id（学习路径）或 target_type + target_id（自定义目标）。
    target_type: str | None = None
    target_id: str | None = None
    path_id: str | None = None
    current_level: str = "基础"
    daily_minutes: int = 30
    intensity: str = "标准"
    direction_id: str | None = None

    @model_validator(mode="after")
    def _check_target(self):
        if self.path_id:
            if self.target_type or self.target_id:
                raise ValueError("path_id 与 target_type/target_id 只能二选一")
            return self
        if not self.target_type or not self.target_id:
            raise ValueError("必须提供 path_id 或 target_type/target_id")
        return self

    @field_validator("target_type")
    @classmethod
    def _check_target_type(cls, v: str | None) -> str | None:
        if v is not None and v not in TARGET_TYPES:
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


# ---- 学习计划专用分类体系（scope=plan）----

class PlanPathOut(BaseModel):
    id: str
    name: str
    subtitle: str
    days: int
    target_days: int
    knowledge_count: int
    question_count: int = 0
    effective_daily_minutes: int = 30
    difficulty_counts: dict[str, int] = Field(default_factory=dict)
    target_type: str
    target_ids: list[str] = Field(default_factory=list)


class PlanCategoryOut(BaseModel):
    id: str
    name: str
    knowledge_count: int = 0
    topic_count: int = 0
    featured: bool = False


class PlanTopicOut(BaseModel):
    id: str
    name: str
    category_id: str
    knowledge_count: int = 0


class PlanTaxonomyOut(BaseModel):
    """`GET /api/learning/taxonomy?scope=plan` 的精简结构。

    不返回 640 个 tag 全量；recommended_tags 最多 3 个（来自最近一次面试评价）。
    """

    paths: list[PlanPathOut] = Field(default_factory=list)
    categories: list[PlanCategoryOut] = Field(default_factory=list)
    topics: dict[str, list[PlanTopicOut]] = Field(default_factory=dict)
    directions: list[str] = Field(default_factory=list)
    levels: list[str] = Field(default_factory=list)
    daily_minutes: list[int] = Field(default_factory=list)
    intensities: list[str] = Field(default_factory=list)
    recommended_tags: list[str] = Field(default_factory=list)
    current_level: str = "基础"
    selected_daily_minutes: int = 30
    selected_intensity: str = "标准"


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
    path_id: str | None = None
    target_days: int | None = None
    knowledge_count: int
    total_minutes: int
    recommended_days: int
    recommended_daily_minutes: int
    effective_daily_minutes: int
    recommended_tasks_per_day: int = 0
    difficulty_counts: dict[str, int] = Field(default_factory=dict)
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
