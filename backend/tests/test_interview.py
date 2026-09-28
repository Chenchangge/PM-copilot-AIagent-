"""模拟面试单元测试（题库 / 选择器 / 结构化输出 / Service）。"""
import json
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["ENVIRONMENT"] = "test"

import httpx
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  # 注册模型到 Base.metadata
from app.core.errors import AIErrorCode
from app.db.database import Base
from app.interview.constants import (
    DIFFICULTIES,
    DIRECTIONS,
    END_REASON_MANUAL,
    END_REASON_MAX_MAIN,
    INTERVIEW_TYPES,
    STATUS_COMPLETED,
    STATUS_WAITING_ANSWER,
)
from app.interview.errors import InterviewError, InterviewErrorCode
from app.interview.followup import FollowUpDecider, FollowUpParseError, parse_follow_up_decision
from app.interview.question_bank import QuestionBank
from app.interview.selector import QuestionSelector
from app.models.interview import InterviewSession, InterviewTurn
from app.services.interview_service import InterviewService

ENGINE = create_engine(f"sqlite:///{_TMP}/svc.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=ENGINE)
Session = sessionmaker(bind=ENGINE)


class MockLLM:
    """可编程的 LLM 适配器：按队列返回输出，或抛出指定异常。"""

    def __init__(self, outputs=None, error=None):
        self.outputs = list(outputs or [])
        self.error = error
        self.provider = "mock"
        self.model = "mock-llm"
        self.calls = 0

    def generate(self, messages, options=None):
        self.calls += 1
        if self.error:
            raise self.error
        if self.outputs:
            return {"content": self.outputs.pop(0)}
        return {
            "content": json.dumps(
                {"should_follow_up": False, "follow_up_type": None, "follow_up_question": None, "reason": "ok"}
            )
        }

    def classify_error(self, exc):
        return "PROVIDER_ERROR", "模型服务返回错误"


def _followup_json(**overrides):
    data = {"should_follow_up": False, "follow_up_type": None, "follow_up_question": None, "reason": "ok"}
    data.update(overrides)
    return json.dumps(data)


# ---- 题库 ----
class TestQuestionBank(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = QuestionBank()
        cls.bank.load()

    def test_count_at_least_30(self):
        self.assertGreaterEqual(self.bank.count(), 30)

    def test_unique_ids(self):
        ids = [q["id"] for q in self.bank.all()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_fields(self):
        for q in self.bank.all():
            for f in ["id", "content", "type", "difficulty", "directions", "knowledge_ids", "evaluation_points", "reference_answer"]:
                self.assertIn(f, q, f"{q.get('id')} 缺字段 {f}")

    def test_valid_enums(self):
        for q in self.bank.all():
            self.assertIn(q["type"], INTERVIEW_TYPES)
            self.assertIn(q["difficulty"], DIFFICULTIES)
            for d in q["directions"]:
                self.assertIn(d, DIRECTIONS)

    def test_knowledge_ids_exist(self):
        from app.rag.loader import MarkdownLoader

        valid_ids = {d.id for d in MarkdownLoader().load()}
        for q in self.bank.all():
            for kid in q["knowledge_ids"]:
                self.assertIn(kid, valid_ids, f"{q['id']} 引用了不存在的 knowledge_id: {kid}")

    def test_no_duplicate_content(self):
        contents = [q["content"] for q in self.bank.all()]
        self.assertEqual(len(contents), len(set(contents)))


# ---- 选择器 ----
def _mini_bank():
    bank = QuestionBank.__new__(QuestionBank)
    bank._questions = [
        {"id": "q1", "content": "x", "type": "产品设计", "difficulty": "基础", "directions": ["AI产品经理"],
         "knowledge_ids": ["mvp"], "evaluation_points": ["p"], "reference_answer": "a"},
        {"id": "q2", "content": "y", "type": "AI产品", "difficulty": "中等", "directions": ["C端产品经理"],
         "knowledge_ids": ["mvp"], "evaluation_points": ["p"], "reference_answer": "a"},
    ]
    bank._by_id = {q["id"]: q for q in bank._questions}
    return bank


class TestQuestionSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = QuestionBank()
        cls.bank.load()
        cls.selector = QuestionSelector(cls.bank)

    def test_select_by_direction_and_type(self):
        q = self.selector.select("AI产品经理", "中等", "AI产品", exclude_ids=set())
        self.assertIn("AI产品经理", q["directions"])
        self.assertEqual(q["type"], "AI产品")

    def test_select_by_difficulty(self):
        q = self.selector.select("数据产品经理", "困难", "数据分析", exclude_ids=set())
        self.assertEqual(q["difficulty"], "困难")

    def test_exclude_ids(self):
        first = self.selector.select("AI产品经理", "中等", "AI产品", exclude_ids=set())
        second = self.selector.select("AI产品经理", "中等", "AI产品", exclude_ids={first["id"]})
        self.assertNotEqual(first["id"], second["id"])

    def test_fallback_keeps_direction(self):
        sel = QuestionSelector(_mini_bank())
        # AI产品经理 + 产品设计 + 困难：无「困难」，降级为 方向+类型
        q = sel.select("AI产品经理", "困难", "产品设计", exclude_ids=set())
        self.assertEqual(q["id"], "q1")

    def test_no_question_error(self):
        empty = QuestionBank.__new__(QuestionBank)
        empty._questions = []
        empty._by_id = {}
        sel = QuestionSelector(empty)
        with self.assertRaises(InterviewError) as ctx:
            sel.select("AI产品经理", "困难", "AI产品", exclude_ids=set())
        self.assertEqual(ctx.exception.code, InterviewErrorCode.interview_question_bank_error)

    def test_no_repeat_when_exhausted(self):
        sel = QuestionSelector(_mini_bank())
        first = sel.select("AI产品经理", "困难", "产品设计", exclude_ids=set())
        second = sel.select("AI产品经理", "困难", "产品设计", exclude_ids={first["id"]})
        self.assertNotEqual(first["id"], second["id"])
        # 两个都已使用 → 必须报错，绝不能重复返回旧题
        with self.assertRaises(InterviewError) as ctx:
            sel.select("AI产品经理", "困难", "产品设计", exclude_ids={first["id"], second["id"]})
        self.assertEqual(ctx.exception.code, InterviewErrorCode.interview_question_bank_error)


# ---- 结构化输出解析 ----
class TestParseFollowUp(unittest.TestCase):
    def test_valid_followup(self):
        d = parse_follow_up_decision(_followup_json(should_follow_up=True, follow_up_type="why", follow_up_question="为什么？"))
        self.assertTrue(d.should_follow_up)
        self.assertEqual(d.follow_up_type, "why")

    def test_valid_no_followup(self):
        d = parse_follow_up_decision(_followup_json())
        self.assertFalse(d.should_follow_up)
        self.assertIsNone(d.follow_up_type)

    def test_invalid_json(self):
        with self.assertRaises(FollowUpParseError):
            parse_follow_up_decision("not json")

    def test_invalid_enum(self):
        with self.assertRaises(FollowUpParseError):
            parse_follow_up_decision(_followup_json(should_follow_up=True, follow_up_type="bogus", follow_up_question="q"))

    def test_missing_question_when_true(self):
        with self.assertRaises(FollowUpParseError):
            parse_follow_up_decision(_followup_json(should_follow_up=True, follow_up_type="why"))

    def test_missing_should_follow_up(self):
        with self.assertRaises(FollowUpParseError):
            parse_follow_up_decision('{"follow_up_type": "why"}')


# ---- 追问决策器 ----
class TestFollowUpDecider(unittest.TestCase):
    def test_retry_once_then_success(self):
        llm = MockLLM(outputs=["garbage", _followup_json(should_follow_up=True, follow_up_type="deepen", follow_up_question="展开说说")])
        decider = FollowUpDecider(llm)
        d = decider.decide("AI产品经理", "中等", "AI产品", 1, "主问题", "回答", 2)
        self.assertTrue(d.should_follow_up)
        self.assertEqual(llm.calls, 2)

    def test_both_fail_then_fallback(self):
        llm = MockLLM(outputs=["garbage", "still garbage"])
        decider = FollowUpDecider(llm)
        d = decider.decide("AI产品经理", "中等", "AI产品", 1, "主问题", "回答", 2)
        self.assertFalse(d.should_follow_up)
        self.assertIsNone(d.follow_up_question)
        self.assertEqual(llm.calls, 2)

    def test_provider_error_propagates(self):
        req = httpx.Request("POST", "http://x")
        err = httpx.HTTPStatusError("429", request=req, response=httpx.Response(429, request=req))
        llm = MockLLM(error=err)
        decider = FollowUpDecider(llm)
        with self.assertRaises(InterviewError) as ctx:
            decider.decide("AI产品经理", "中等", "AI产品", 1, "主问题", "回答", 2)
        self.assertEqual(ctx.exception.code, AIErrorCode.provider_error)


# ---- Service ----
class TestInterviewService(unittest.TestCase):
    def setUp(self):
        self.db = Session()
        self.llm = MockLLM()
        self.service = InterviewService(self.db, llm_adapter=self.llm)

    def tearDown(self):
        self.db.close()

    def _turn_count(self, sid):
        return self.db.execute(
            select(func.count(InterviewTurn.id)).where(InterviewTurn.session_id == sid)
        ).scalar()

    def test_create_session(self):
        resp = self.service.create_session("user-1", "AI产品经理", "中等", "AI产品")
        self.assertEqual(resp.status, STATUS_WAITING_ANSWER)
        self.assertEqual(resp.current_round, 1)
        self.assertEqual(resp.question.type, "main")
        s = self.db.get(InterviewSession, resp.session_id)
        self.assertEqual(s.user_id, "user-1")
        self.assertEqual(s.config_snapshot["max_main_questions"], 5)
        self.assertEqual(s.config_snapshot["max_followups_per_question"], 2)

    def test_submit_answer_followup(self):
        sid = self.service.create_session("u1", "AI产品经理", "中等", "AI产品").session_id
        self.llm.outputs = [_followup_json(should_follow_up=True, follow_up_type="why", follow_up_question="为什么这样判断？")]
        ans = self.service.submit_answer("u1", sid, "我的回答", client_request_id="r1")
        self.assertEqual(ans.action, "follow_up")
        self.assertEqual(ans.question.type, "follow_up")
        self.assertEqual(ans.question.follow_up_type, "why")
        self.assertEqual(self.db.get(InterviewSession, sid).status, STATUS_WAITING_ANSWER)

    def test_submit_answer_next_question(self):
        sid = self.service.create_session("u1", "AI产品经理", "中等", "AI产品").session_id
        ans = self.service.submit_answer("u1", sid, "回答")
        self.assertEqual(ans.action, "next_question")
        self.assertEqual(ans.question.type, "main")
        self.assertEqual(ans.current_round, 2)

    def test_completion_after_max_main(self):
        sid = self.service.create_session("u1", "AI产品经理", "中等", "AI产品").session_id
        for i in range(5):
            ans = self.service.submit_answer("u1", sid, f"回答{i}")
            if i < 4:
                self.assertEqual(ans.action, "next_question", f"第 {i} 次应为 next_question")
            else:
                self.assertEqual(ans.action, "completed")
        s = self.db.get(InterviewSession, sid)
        self.assertEqual(s.status, STATUS_COMPLETED)
        self.assertEqual(s.end_reason, END_REASON_MAX_MAIN)

    def test_main_questions_not_repeated(self):
        # 触发真实缺陷的场景：产品基础 + 中等 只有 3 题，需放宽难度才能凑够 5 题
        sid = self.service.create_session("u1", "C端产品经理", "中等", "产品基础").session_id
        for i in range(5):
            self.service.submit_answer("u1", sid, f"回答{i}")
        main_ids = self.db.execute(
            select(InterviewTurn.question_id).where(
                InterviewTurn.session_id == sid,
                InterviewTurn.question_id.isnot(None),
            )
        ).scalars().all()
        self.assertEqual(len(main_ids), 5)
        self.assertEqual(len(set(main_ids)), 5)

    def test_followup_does_not_affect_dedup(self):
        sid = self.service.create_session("u1", "C端产品经理", "中等", "产品基础").session_id
        # 第1题 → 追问
        self.llm.outputs = [_followup_json(should_follow_up=True, follow_up_type="why", follow_up_question="为什么？")]
        ans1 = self.service.submit_answer("u1", sid, "回答1")
        self.assertEqual(ans1.action, "follow_up")
        # 回答追问 → 换下一题
        self.llm.outputs = [_followup_json(should_follow_up=False)]
        ans2 = self.service.submit_answer("u1", sid, "回答追问")
        self.assertEqual(ans2.action, "next_question")
        # 两个主问题应不同（追问不算新的主问题）
        main_ids = self.db.execute(
            select(InterviewTurn.question_id).where(
                InterviewTurn.session_id == sid,
                InterviewTurn.question_id.isnot(None),
            )
        ).scalars().all()
        self.assertEqual(len(main_ids), 2)
        self.assertEqual(len(set(main_ids)), 2)

    def test_empty_answer(self):
        sid = self.service.create_session("u1", "AI产品经理", "中等", "AI产品").session_id
        with self.assertRaises(InterviewError) as ctx:
            self.service.submit_answer("u1", sid, "   ")
        self.assertEqual(ctx.exception.code, InterviewErrorCode.interview_invalid_answer)

    def test_answer_too_long(self):
        sid = self.service.create_session("u1", "AI产品经理", "中等", "AI产品").session_id
        with self.assertRaises(InterviewError) as ctx:
            self.service.submit_answer("u1", sid, "长" * 2001)
        self.assertEqual(ctx.exception.code, InterviewErrorCode.interview_invalid_answer)

    def test_user_isolation(self):
        sid = self.service.create_session("user-a", "AI产品经理", "中等", "AI产品").session_id
        with self.assertRaises(InterviewError) as ctx:
            self.service.get_session("user-b", sid)
        self.assertEqual(ctx.exception.code, InterviewErrorCode.interview_session_not_found)

    def test_idempotent_submit(self):
        sid = self.service.create_session("u1", "AI产品经理", "中等", "AI产品").session_id
        self.service.submit_answer("u1", sid, "回答", client_request_id="req-1")
        before = self._turn_count(sid)
        calls_before = self.llm.calls
        self.service.submit_answer("u1", sid, "回答", client_request_id="req-1")
        self.assertEqual(self._turn_count(sid), before)
        self.assertEqual(self.llm.calls, calls_before)

    def test_finish_manual(self):
        sid = self.service.create_session("u1", "AI产品经理", "中等", "AI产品").session_id
        s = self.service.finish("u1", sid)
        self.assertEqual(s.status, STATUS_COMPLETED)
        self.assertEqual(s.end_reason, END_REASON_MANUAL)

    def test_model_not_found(self):
        db = Session()
        svc = InterviewService(db)  # 不注入 llm_adapter，走真实解析
        sid = svc.create_session("u2", "AI产品经理", "中等", "AI产品").session_id
        with self.assertRaises(InterviewError) as ctx:
            svc.submit_answer("u2", sid, "回答")
        self.assertEqual(ctx.exception.code, InterviewErrorCode.interview_model_not_found)
        db.close()

    def test_provider_error_rolls_back_answer(self):
        sid = self.service.create_session("u1", "AI产品经理", "中等", "AI产品").session_id
        req = httpx.Request("POST", "http://x")
        self.llm.error = httpx.HTTPStatusError("500", request=req, response=httpx.Response(500, request=req))
        with self.assertRaises(InterviewError):
            self.service.submit_answer("u1", sid, "回答")
        # 回滚后：仍有一个未回答的 turn，answer 未保存
        s = self.db.get(InterviewSession, sid)
        self.assertEqual(s.status, STATUS_WAITING_ANSWER)
        turn = self.service._get_unanswered_turn(s)
        self.assertIsNotNone(turn)
        self.assertIsNone(turn.answer_content)


if __name__ == "__main__":
    unittest.main()
