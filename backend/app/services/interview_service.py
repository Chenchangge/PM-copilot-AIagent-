"""模拟面试核心服务：创建 / 恢复 / 提交回答 / 结束。"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.interview.constants import (
    DEFAULT_MAX_FOLLOWUPS_PER_QUESTION,
    DEFAULT_MAX_MAIN_QUESTIONS,
    END_REASON_MANUAL,
    END_REASON_MAX_MAIN,
    MAX_ANSWER_LENGTH,
    QUESTION_TYPE_FOLLOW_UP,
    QUESTION_TYPE_MAIN,
    STATUS_COMPLETED,
    STATUS_CREATED,
    STATUS_WAITING_ANSWER,
)
from app.interview.errors import InterviewError, InterviewErrorCode
from app.interview.followup import FollowUpDecider
from app.interview.question_bank import QuestionBank
from app.interview.selector import QuestionSelector
from app.models.interview import InterviewSession, InterviewTurn
from app.schemas.interview import (
    AnswerResponse,
    CreateSessionResponse,
    QuestionOut,
    SessionDetailResponse,
    SessionOut,
    TurnOut,
)
from app.services.model_service import ModelService
from app.services.providers import get_adapter
from app.services.secret_storage import secret_storage

_BANK: QuestionBank | None = None


def get_question_bank() -> QuestionBank:
    """进程内缓存的题库单例（静态 JSON，无需每次读盘）。"""
    global _BANK
    if _BANK is None:
        _BANK = QuestionBank()
        _BANK.load()
    return _BANK


def resolve_interview_adapter(user_id: str, db: Session):
    """按 user_id 解析模拟面试 LLM Adapter（复用 BYOK）。

    无满足 text_generation + reasoning + structured_output 的模型时抛
    INTERVIEW_MODEL_NOT_FOUND。测试可通过 patch 本函数注入 Mock Adapter。
    """
    model = ModelService(db).find_interview_model(user_id)
    if model is None:
        raise InterviewError(
            InterviewErrorCode.interview_model_not_found,
            "尚未配置可用于模拟面试的 AI 模型，请先配置。",
        )
    return get_adapter(
        model.provider,
        model.base_url or "",
        secret_storage.unseal(model.api_key_secret),
        model.model,
    )


class InterviewService:
    def __init__(self, db: Session, llm_adapter=None, bank: QuestionBank | None = None) -> None:
        self.db = db
        self._llm_adapter = llm_adapter  # 测试注入的 Mock；生产为 None（懒解析）
        self.bank = bank if bank is not None else get_question_bank()
        self.selector = QuestionSelector(self.bank)

    # ---- 创建 ----
    def create_session(self, user_id: str, direction: str, difficulty: str, interview_type: str) -> CreateSessionResponse:
        config = {
            "direction": direction,
            "difficulty": difficulty,
            "interview_type": interview_type,
            "max_main_questions": DEFAULT_MAX_MAIN_QUESTIONS,
            "max_followups_per_question": DEFAULT_MAX_FOLLOWUPS_PER_QUESTION,
        }
        session = InterviewSession(
            id=f"intv-{uuid.uuid4().hex[:16]}",
            user_id=user_id,
            direction=direction,
            difficulty=difficulty,
            interview_type=interview_type,
            status=STATUS_CREATED,
            config_snapshot=config,
            current_round=0,
        )
        self.db.add(session)

        q = self.selector.select(direction, difficulty, interview_type, exclude_ids=set())
        turn = self._new_main_turn(session, q, round_number=1)
        self.db.add(turn)

        session.status = STATUS_WAITING_ANSWER
        session.current_round = 1
        self.db.commit()
        self.db.refresh(session)
        self.db.refresh(turn)
        return CreateSessionResponse(
            session_id=session.id,
            status=session.status,
            current_round=session.current_round,
            question=self._build_question_out(turn),
        )

    # ---- 恢复 ----
    def get_session(self, user_id: str, session_id: str) -> SessionDetailResponse:
        session = self._get_session(user_id, session_id)
        turns = self.db.execute(
            select(InterviewTurn)
            .where(InterviewTurn.session_id == session.id)
            .order_by(InterviewTurn.id)
        ).scalars().all()
        current = None
        for t in turns:
            if t.answer_content is None:
                current = t
        return SessionDetailResponse(
            session=self._build_session_out(session),
            current_question=self._build_question_out(current) if current else None,
            turns=[self._build_turn_out(t) for t in turns],
        )

    # ---- 提交回答 ----
    def submit_answer(self, user_id: str, session_id: str, answer: str, client_request_id: str | None = None) -> AnswerResponse:
        answer = answer.strip()
        if not answer:
            raise InterviewError(InterviewErrorCode.interview_invalid_answer, "回答不能为空")
        if len(answer) > MAX_ANSWER_LENGTH:
            raise InterviewError(
                InterviewErrorCode.interview_invalid_answer,
                f"回答超过最大长度 {MAX_ANSWER_LENGTH}",
            )

        session = self._get_session(user_id, session_id)
        if session.status == STATUS_COMPLETED:
            raise InterviewError(InterviewErrorCode.interview_session_completed, "面试已结束")
        if session.status != STATUS_WAITING_ANSWER:
            raise InterviewError(InterviewErrorCode.interview_invalid_state, "当前状态不允许提交回答")

        # 幂等：同一 client_request_id 已处理过 → 直接返回当前状态，不重复落库 / 不重复调用 LLM
        if client_request_id:
            exists = self.db.execute(
                select(InterviewTurn.id).where(
                    InterviewTurn.session_id == session.id,
                    InterviewTurn.client_request_id == client_request_id,
                )
            ).scalars().first()
            if exists is not None:
                current = self._get_unanswered_turn(session)
                return self._build_answer_response(session, current)

        unanswered = self._get_unanswered_turn(session)
        if unanswered is None:
            raise InterviewError(InterviewErrorCode.interview_invalid_state, "没有待回答的问题")

        # 保存回答 + LLM 追问决策 + 推进，在同一事务内完成；
        # 任何失败（模型/解析等）整体回滚，Session 保持 waiting_answer，不产生半写入。
        try:
            unanswered.answer_content = answer
            unanswered.answer_length = len(answer)
            unanswered.client_request_id = client_request_id

            adapter = self._get_adapter(user_id)
            decider = FollowUpDecider(adapter)
            config = session.config_snapshot or {}
            max_main = config.get("max_main_questions", DEFAULT_MAX_MAIN_QUESTIONS)
            max_followups = config.get("max_followups_per_question", DEFAULT_MAX_FOLLOWUPS_PER_QUESTION)
            remaining = max(0, max_followups - self._followup_count(session))

            decision = decider.decide(
                direction=session.direction,
                difficulty=session.difficulty,
                interview_type=session.interview_type,
                round_number=session.current_round,
                question_content=unanswered.question_content,
                answer=answer,
                remaining_followups=remaining,
            )

            if decision.should_follow_up and remaining > 0:
                turn = self._new_followup_turn(session, decision)
                self.db.add(turn)
                self.db.commit()
                self.db.refresh(session)
                self.db.refresh(turn)
                return self._build_answer_response(session, turn, action="follow_up")

            if session.current_round < max_main:
                asked = self._asked_question_ids(session)
                q = self.selector.select(
                    session.direction, session.difficulty, session.interview_type, exclude_ids=asked
                )
                turn = self._new_main_turn(session, q, round_number=session.current_round + 1)
                self.db.add(turn)
                session.current_round += 1
                self.db.commit()
                self.db.refresh(session)
                self.db.refresh(turn)
                return self._build_answer_response(session, turn, action="next_question")

            session.status = STATUS_COMPLETED
            session.end_reason = END_REASON_MAX_MAIN
            session.completed_at = _utcnow()
            self.db.commit()
            self.db.refresh(session)
            return self._build_answer_response(session, None, action="completed")
        except Exception:
            self.db.rollback()
            raise

    # ---- 结束 ----
    def finish(self, user_id: str, session_id: str) -> SessionOut:
        session = self._get_session(user_id, session_id)
        if session.status == STATUS_COMPLETED:
            return self._build_session_out(session)  # 幂等
        if session.status in (STATUS_WAITING_ANSWER, STATUS_CREATED):
            session.status = STATUS_COMPLETED
            session.end_reason = END_REASON_MANUAL
            session.completed_at = _utcnow()
            self.db.commit()
            self.db.refresh(session)
            return self._build_session_out(session)
        raise InterviewError(InterviewErrorCode.interview_invalid_state, "当前状态不允许结束面试")

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

    def _get_adapter(self, user_id: str):
        if self._llm_adapter is not None:
            return self._llm_adapter
        return resolve_interview_adapter(user_id, self.db)

    def _get_unanswered_turn(self, session: InterviewSession) -> InterviewTurn | None:
        return self.db.execute(
            select(InterviewTurn)
            .where(
                InterviewTurn.session_id == session.id,
                InterviewTurn.answer_content.is_(None),
            )
            .order_by(InterviewTurn.id.desc())
        ).scalars().first()

    def _followup_count(self, session: InterviewSession) -> int:
        return self.db.execute(
            select(func.count(InterviewTurn.id)).where(
                InterviewTurn.session_id == session.id,
                InterviewTurn.round_number == session.current_round,
                InterviewTurn.question_type == QUESTION_TYPE_FOLLOW_UP,
            )
        ).scalar() or 0

    def _asked_question_ids(self, session: InterviewSession) -> set[str]:
        rows = self.db.execute(
            select(InterviewTurn.question_id).where(
                InterviewTurn.session_id == session.id,
                InterviewTurn.question_id.isnot(None),
            )
        ).scalars().all()
        return set(rows)

    def _get_main_turn(self, session: InterviewSession, round_number: int) -> InterviewTurn | None:
        return self.db.execute(
            select(InterviewTurn).where(
                InterviewTurn.session_id == session.id,
                InterviewTurn.round_number == round_number,
                InterviewTurn.question_type == QUESTION_TYPE_MAIN,
            )
        ).scalars().first()

    def _new_main_turn(self, session: InterviewSession, q: dict, round_number: int) -> InterviewTurn:
        return InterviewTurn(
            session_id=session.id,
            round_number=round_number,
            question_id=q["id"],
            question_content=q["content"],
            question_type=QUESTION_TYPE_MAIN,
            knowledge_ids=q.get("knowledge_ids", []),
            evaluation_points=q.get("evaluation_points", []),
            reference_answer=q.get("reference_answer"),
        )

    def _new_followup_turn(self, session: InterviewSession, decision) -> InterviewTurn:
        main = self._get_main_turn(session, session.current_round)
        return InterviewTurn(
            session_id=session.id,
            round_number=session.current_round,
            question_id=None,
            question_content=decision.follow_up_question or "",
            question_type=QUESTION_TYPE_FOLLOW_UP,
            follow_up_type=decision.follow_up_type,
            knowledge_ids=main.knowledge_ids if main else [],
            evaluation_points=main.evaluation_points if main else [],
            reference_answer=main.reference_answer if main else None,
        )

    # ---- 序列化 ----
    def _build_session_out(self, s: InterviewSession) -> SessionOut:
        config = s.config_snapshot or {}
        return SessionOut(
            id=s.id,
            status=s.status,
            direction=s.direction,
            difficulty=s.difficulty,
            interview_type=s.interview_type,
            current_round=s.current_round,
            max_main_questions=config.get("max_main_questions", DEFAULT_MAX_MAIN_QUESTIONS),
            end_reason=s.end_reason,
            created_at=s.created_at,
            completed_at=s.completed_at,
        )

    def _build_question_out(self, t: InterviewTurn) -> QuestionOut:
        return QuestionOut(
            turn_id=t.id,
            content=t.question_content,
            type=t.question_type,
            round=t.round_number,
            follow_up_type=t.follow_up_type,
        )

    def _build_turn_out(self, t: InterviewTurn) -> TurnOut:
        return TurnOut(
            turn_id=t.id,
            round=t.round_number,
            type=t.question_type,
            question_id=t.question_id,
            question_content=t.question_content,
            follow_up_type=t.follow_up_type,
            answer_content=t.answer_content,
        )

    def _build_answer_response(self, session: InterviewSession, turn: InterviewTurn | None, action: str | None = None) -> AnswerResponse:
        if turn is None:
            return AnswerResponse(
                session_id=session.id,
                status=session.status,
                current_round=session.current_round,
                action="completed",
                question=None,
            )
        if action is None:
            action = "follow_up" if turn.question_type == QUESTION_TYPE_FOLLOW_UP else "next_question"
        return AnswerResponse(
            session_id=session.id,
            status=session.status,
            current_round=session.current_round,
            action=action,
            question=self._build_question_out(turn),
        )


def _utcnow():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)
