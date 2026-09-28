"""模拟面试的数据模型：InterviewSession + InterviewTurn。"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    interview_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True, nullable=False)
    config_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("interview_sessions.id"), index=True, nullable=False
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_id: Mapped[str | None] = mapped_column(String, nullable=True)
    question_content: Mapped[str] = mapped_column(String, nullable=False)
    question_type: Mapped[str] = mapped_column(String, nullable=False)  # main | follow_up
    follow_up_type: Mapped[str | None] = mapped_column(String, nullable=True)
    knowledge_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    evaluation_points: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    reference_answer: Mapped[str | None] = mapped_column(String, nullable=True)
    answer_content: Mapped[str | None] = mapped_column(String, nullable=True)
    answer_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class InterviewEvaluation(Base):
    """面试评价（一个 Session 最多一条，unique session_id）。"""

    __tablename__ = "interview_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("interview_sessions.id"), unique=True, index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True, nullable=False)  # pending | completed | failed
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dimensions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    overall_strengths: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    overall_weaknesses: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    recommended_knowledge: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
