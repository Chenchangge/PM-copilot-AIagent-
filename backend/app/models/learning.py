"""学习计划（Learning Plan）数据模型：LearningPlan / LearningPlanDay /
LearningPlanTask / KnowledgeLearningRecord（Step 12-3 Part B）。

进度一致性原则（§35）：progress 一律由后端按 task 状态重算，前端只提交 task 完成。
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    target_type: Mapped[str] = mapped_column(String, nullable=False)  # category | topic | tag
    target_id: Mapped[str] = mapped_column(String, nullable=False)
    target_name: Mapped[str] = mapped_column(String, nullable=False)
    direction_id: Mapped[str | None] = mapped_column(String, nullable=True)
    current_level: Mapped[str] = mapped_column(String, nullable=False)
    daily_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    intensity: Mapped[str] = mapped_column(String, nullable=False)
    recommended_days: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_days: Mapped[int] = mapped_column(Integer, nullable=False)
    total_knowledge_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_knowledge_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, index=True, nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class LearningPlanDay(Base):
    __tablename__ = "learning_plan_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("learning_plans.id"), index=True, nullable=False
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="locked")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LearningPlanTask(Base):
    __tablename__ = "learning_plan_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_day_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("learning_plan_days.id"), index=True, nullable=False
    )
    knowledge_point_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class KnowledgeLearningRecord(Base):
    """最小学习记录闭环（§26）。started / completed；可扩展 reviewed。"""

    __tablename__ = "knowledge_learning_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    knowledge_point_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plan_task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="started")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
