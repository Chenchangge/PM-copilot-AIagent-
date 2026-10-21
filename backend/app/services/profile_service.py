"""用户中心：学习记录 / 面试记录查询服务。"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.interview.constants import STATUS_COMPLETED
from app.learning.constants import LEGACY_KNOWLEDGE_TITLES
from app.models.interview import InterviewEvaluation, InterviewSession
from app.models.learning import KnowledgeLearningRecord
from app.rag.loader import MarkdownLoader
from app.schemas.profile import (
    InterviewHistoryItem,
    InterviewHistoryResponse,
    LearningHistoryItem,
    LearningHistoryResponse,
)

_DOCS: dict[str, object] | None = None


def _doc_index() -> dict[str, object]:
    global _DOCS
    if _DOCS is None:
        try:
            _DOCS = {d.id: d for d in MarkdownLoader().load()}
        except Exception:  # noqa: BLE001 - 知识库缺失不应阻断记录页
            _DOCS = {}
    return _DOCS


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def learning_history(self, user_id: str, page: int = 1, page_size: int = 20) -> LearningHistoryResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        total = self.db.execute(
            select(func.count(KnowledgeLearningRecord.id)).where(
                KnowledgeLearningRecord.user_id == user_id
            )
        ).scalar() or 0
        rows = self.db.execute(
            select(KnowledgeLearningRecord)
            .where(KnowledgeLearningRecord.user_id == user_id)
            .order_by(KnowledgeLearningRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        docs = _doc_index()
        items: list[LearningHistoryItem] = []
        for row in rows:
            doc = docs.get(row.knowledge_point_id)
            items.append(
                LearningHistoryItem(
                    id=row.id,
                    knowledge_point_id=row.knowledge_point_id,
                    title=getattr(doc, "title", None)
                    or LEGACY_KNOWLEDGE_TITLES.get(row.knowledge_point_id, row.knowledge_point_id),
                    category=getattr(doc, "category", "") or "",
                    topic=getattr(doc, "topic", "") or "",
                    status=row.status,
                    duration_minutes=row.actual_minutes
                    if row.actual_minutes is not None
                    else (getattr(doc, "estimated_minutes", None) or 0),
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                )
            )
        return LearningHistoryResponse(items=items, total=total, page=page, page_size=page_size)

    def interview_history(self, user_id: str, page: int = 1, page_size: int = 20) -> InterviewHistoryResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        total = self.db.execute(
            select(func.count(InterviewSession.id)).where(InterviewSession.user_id == user_id)
        ).scalar() or 0
        rows = self.db.execute(
            select(InterviewSession, InterviewEvaluation)
            .outerjoin(InterviewEvaluation, InterviewEvaluation.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.created_at.desc(), InterviewSession.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        items: list[InterviewHistoryItem] = []
        for session, evaluation in rows:
            items.append(
                InterviewHistoryItem(
                    session_id=session.id,
                    direction=session.direction,
                    difficulty=session.difficulty,
                    interview_type=session.interview_type,
                    status=session.status,
                    overall_score=evaluation.overall_score if evaluation is not None else None,
                    evaluation_status=evaluation.status if evaluation is not None else None,
                    created_at=session.created_at,
                    completed_at=session.completed_at,
                    can_continue=session.status in ("created", "waiting_answer"),
                    can_view_evaluation=session.status == STATUS_COMPLETED,
                )
            )
        return InterviewHistoryResponse(items=items, total=total, page=page, page_size=page_size)
