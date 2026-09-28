"""面试评价服务：加载面试 → 组装上下文 → 调 LLM → 校验 → 计算总分 → 推荐 → 落库。

Route 保持薄层，本服务承载全部评价编排逻辑（对应 Step 9-2 §十七）。
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AIErrorCode
from app.interview.constants import (
    EVAL_STATUS_COMPLETED,
    EVAL_STATUS_FAILED,
    EVALUATION_WEIGHTS,
    STATUS_COMPLETED,
)
from app.interview.errors import InterviewError, InterviewErrorCode
from app.interview.evaluation import (
    EvaluationParseError,
    build_evaluation_messages,
    calculate_overall_score,
    parse_evaluation_output,
    recommend_knowledge,
)
from app.models.interview import InterviewEvaluation, InterviewSession, InterviewTurn
from app.rag.loader import MarkdownLoader
from app.schemas.evaluation import (
    DimensionReport,
    EvaluationReport,
    EvidenceItem,
    RecommendedKnowledge,
)
from app.services.interview_service import resolve_interview_adapter

_KNOWLEDGE_INDEX: dict[str, dict] | None = None


def build_knowledge_index() -> dict[str, dict]:
    """knowledge_id → {title, category} 的轻量索引（复用 MarkdownLoader 元数据，不做 RAG）。"""
    try:
        docs = MarkdownLoader().load()
    except Exception:  # noqa: BLE001 - 索引缺失不阻断评价主流程
        return {}
    return {d.id: {"title": d.title, "category": d.category} for d in docs}


def get_knowledge_index() -> dict[str, dict]:
    """进程内缓存的知识索引。"""
    global _KNOWLEDGE_INDEX
    if _KNOWLEDGE_INDEX is None:
        _KNOWLEDGE_INDEX = build_knowledge_index()
    return _KNOWLEDGE_INDEX


def _utcnow():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)


def _code_str(code) -> str:
    return code.value if hasattr(code, "value") else str(code)


class EvaluationService:
    def __init__(self, db: Session, llm_adapter=None, knowledge_index: dict[str, dict] | None = None) -> None:
        self.db = db
        self._llm_adapter = llm_adapter  # 测试注入的 Mock；生产为 None（懒解析）
        self._knowledge_index = knowledge_index if knowledge_index is not None else get_knowledge_index()

    # ---- 触发评价（同步，幂等）----
    def evaluate_session(self, user_id: str, session_id: str) -> EvaluationReport:
        session = self._get_session(user_id, session_id)
        if session.status != STATUS_COMPLETED:
            raise InterviewError(InterviewErrorCode.interview_invalid_state, "面试尚未完成，无法评价")

        existing = self._get_evaluation_row(session_id)
        if existing is not None and existing.status == EVAL_STATUS_COMPLETED:
            # 幂等：已有成功评价直接返回，不重复消耗 LLM（设计 §19）
            return self._build_report(existing, session)

        adapter = self._get_adapter(user_id)
        turns = self._load_turns(session_id)
        valid_turn_ids = {t.id for t in turns}
        messages = build_evaluation_messages(session, turns)

        try:
            output = self._call_and_parse(adapter, messages, valid_turn_ids)
        except InterviewError as exc:
            self._save_failed(existing, session, user_id, adapter, exc)
            raise

        overall = calculate_overall_score(output.dimensions)
        recommendations = recommend_knowledge(output.dimensions, turns, self._knowledge_index)

        evaluation = existing if existing is not None else self._new_evaluation(session, user_id)
        evaluation.status = EVAL_STATUS_COMPLETED
        evaluation.overall_score = overall
        evaluation.dimensions = [d.model_dump() for d in output.dimensions]
        evaluation.overall_strengths = output.overall_strengths
        evaluation.overall_weaknesses = output.overall_weaknesses
        evaluation.summary = output.summary
        evaluation.recommended_knowledge = recommendations
        evaluation.model = getattr(adapter, "model", None)
        evaluation.provider = getattr(adapter, "provider", None)
        evaluation.error_code = None
        evaluation.error_message = None
        evaluation.completed_at = _utcnow()
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)
        return self._build_report(evaluation, session)

    # ---- 获取评价 ----
    def get_evaluation(self, user_id: str, session_id: str):
        session = self._get_session(user_id, session_id)
        evaluation = self._get_evaluation_row(session_id)
        if evaluation is None:
            raise InterviewError(InterviewErrorCode.evaluation_not_found, "尚未生成评价报告")
        if evaluation.status == EVAL_STATUS_COMPLETED:
            return self._build_report(evaluation, session)
        # failed：返回失败状态 + 友好信息（不含敏感信息，设计 §21）
        return {
            "session_id": session_id,
            "status": EVAL_STATUS_FAILED,
            "error": evaluation.error_message or "评价失败，请重试",
        }

    # ---- 内部 ----
    def _get_session(self, user_id: str, session_id: str) -> InterviewSession:
        session = self.db.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
        ).scalars().first()
        if session is None:
            raise InterviewError(InterviewErrorCode.interview_session_not_found, "面试会话不存在")
        return session

    def _get_evaluation_row(self, session_id: str) -> InterviewEvaluation | None:
        return self.db.execute(
            select(InterviewEvaluation).where(InterviewEvaluation.session_id == session_id)
        ).scalars().first()

    def _load_turns(self, session_id: str) -> list[InterviewTurn]:
        return self.db.execute(
            select(InterviewTurn)
            .where(InterviewTurn.session_id == session_id)
            .order_by(InterviewTurn.id)
        ).scalars().all()

    def _get_adapter(self, user_id: str):
        if self._llm_adapter is not None:
            return self._llm_adapter
        return resolve_interview_adapter(user_id, self.db)

    def _new_evaluation(self, session: InterviewSession, user_id: str) -> InterviewEvaluation:
        return InterviewEvaluation(
            session_id=session.id,
            user_id=user_id,
            status=EVAL_STATUS_FAILED,
            dimensions=[],
            overall_strengths=[],
            overall_weaknesses=[],
            recommended_knowledge=[],
        )

    def _call_and_parse(self, adapter, messages, valid_turn_ids):
        """调用 LLM；Schema 校验失败最多重试一次，仍失败抛 EVALUATION_FAILED。

        上游模型错误（超时/限流等）直接透传为 InterviewError(AIErrorCode)，不重试（设计 §16）。
        """
        last_error: EvaluationParseError | None = None
        for attempt in range(2):
            content = self._generate(adapter, messages)
            try:
                return parse_evaluation_output(content, valid_turn_ids)
            except EvaluationParseError as exc:
                last_error = exc
                continue
        raise InterviewError(
            InterviewErrorCode.evaluation_failed,
            f"AI 评价输出多次无效，请稍后重试。（{last_error}）",
        )

    def _generate(self, adapter, messages) -> str:
        try:
            result = adapter.generate(
                messages,
                options={"temperature": 0, "response_format": {"type": "json_object"}},
            )
        except Exception as exc:  # noqa: BLE001 - 复用统一错误分类
            code_str, message = adapter.classify_error(exc)
            raise InterviewError(AIErrorCode(code_str), message) from exc
        return result.get("content") or ""

    def _save_failed(self, existing, session, user_id, adapter, exc: InterviewError) -> None:
        evaluation = existing if existing is not None else self._new_evaluation(session, user_id)
        evaluation.status = EVAL_STATUS_FAILED
        evaluation.overall_score = None
        evaluation.summary = None
        evaluation.model = getattr(adapter, "model", None)
        evaluation.provider = getattr(adapter, "provider", None)
        evaluation.error_code = _code_str(exc.code)
        evaluation.error_message = exc.message
        evaluation.completed_at = None
        self.db.add(evaluation)
        self.db.commit()

    # ---- 序列化 ----
    def _build_report(self, evaluation: InterviewEvaluation, session: InterviewSession) -> EvaluationReport:
        dims: list[DimensionReport] = []
        for d in evaluation.dimensions or []:
            name = d["dimension"]
            dims.append(DimensionReport(
                dimension=name,
                weight=EVALUATION_WEIGHTS[name],
                score=int(d["score"] + 0.5),
                strengths=d.get("strengths", []),
                weaknesses=d.get("weaknesses", []),
                evidence=[EvidenceItem(**e) for e in d.get("evidence", [])],
            ))
        return EvaluationReport(
            evaluation_id=evaluation.id,
            session_id=evaluation.session_id,
            status=evaluation.status,
            overall_score=evaluation.overall_score or 0,
            summary=evaluation.summary or "",
            direction=session.direction,
            difficulty=session.difficulty,
            interview_type=session.interview_type,
            dimensions=dims,
            overall_strengths=evaluation.overall_strengths or [],
            overall_weaknesses=evaluation.overall_weaknesses or [],
            recommended_knowledge=[RecommendedKnowledge(**r) for r in (evaluation.recommended_knowledge or [])],
            created_at=evaluation.created_at,
        )
