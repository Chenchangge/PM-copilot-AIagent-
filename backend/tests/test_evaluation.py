"""面试评价单元测试（总分 / 校验 / 重试 / 推荐）。"""
import json
import os
import tempfile
import unittest
from types import SimpleNamespace

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["ENVIRONMENT"] = "test"

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  # 注册模型到 Base.metadata
from app.db.database import Base
from app.interview.constants import (
    EVALUATION_DIMENSIONS,
    EVAL_STATUS_COMPLETED,
    EVAL_STATUS_FAILED,
    STATUS_COMPLETED,
)
from app.interview.errors import InterviewError, InterviewErrorCode
from app.interview.evaluation import (
    EvaluationParseError,
    calculate_overall_score,
    recommend_knowledge,
    validate_evaluation_output,
)
from app.models.interview import InterviewEvaluation, InterviewSession, InterviewTurn
from app.schemas.evaluation import DimensionEvaluation, EvidenceItem
from app.services.evaluation_service import EvaluationService

ENGINE = create_engine(f"sqlite:///{_TMP}/eval.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=ENGINE)
Session = sessionmaker(bind=ENGINE)


class MockLLM:
    """可编程的 LLM 适配器：按队列返回输出。"""

    def __init__(self, outputs=None):
        self.outputs = list(outputs or [])
        self.provider = "mock"
        self.model = "mock-llm"
        self.calls = 0

    def generate(self, messages, options=None):
        self.calls += 1
        return {"content": self.outputs.pop(0)}

    def classify_error(self, exc):
        return "PROVIDER_ERROR", "模型服务返回错误"


def _valid_data(scores=None, evidence_by_dim=None):
    scores = scores or {"产品思维": 84, "需求分析": 76, "逻辑与表达": 88, "AI知识": 71, "业务意识": 80}
    evidence_by_dim = evidence_by_dim or {}
    dims = []
    for name in EVALUATION_DIMENSIONS:
        dims.append({
            "dimension": name,
            "score": scores[name],
            "evidence": evidence_by_dim.get(name, []),
            "strengths": ["s"],
            "weaknesses": ["w"],
        })
    return {
        "dimensions": dims,
        "overall_strengths": ["s"],
        "overall_weaknesses": ["w"],
        "summary": "总结",
    }


def _valid_json(scores=None):
    return json.dumps(_valid_data(scores=scores))


def _dims(scores):
    return [
        DimensionEvaluation(dimension=n, score=s, evidence=[], strengths=[], weaknesses=[])
        for n, s in scores.items()
    ]


# ---- 总分计算 ----
class TestOverallScore(unittest.TestCase):
    def test_all_full(self):
        self.assertEqual(calculate_overall_score(_dims({"产品思维": 100, "需求分析": 100, "逻辑与表达": 100, "AI知识": 100, "业务意识": 100})), 100)

    def test_all_half(self):
        self.assertEqual(calculate_overall_score(_dims({"产品思维": 50, "需求分析": 50, "逻辑与表达": 50, "AI知识": 50, "业务意识": 50})), 50)

    def test_only_product_thinking(self):
        self.assertEqual(calculate_overall_score(_dims({"产品思维": 100, "需求分析": 0, "逻辑与表达": 0, "AI知识": 0, "业务意识": 0})), 30)

    def test_mixed_rounding(self):
        # 84*0.3+76*0.2+88*0.2+71*0.15+80*0.15 = 80.65 -> 81（明确四舍五入，非银行家舍入）
        self.assertEqual(calculate_overall_score(_dims({"产品思维": 84, "需求分析": 76, "逻辑与表达": 88, "AI知识": 71, "业务意识": 80})), 81)


# ---- 维度校验 ----
class TestDimensionValidation(unittest.TestCase):
    def test_valid_passes(self):
        out = validate_evaluation_output(_valid_data(), valid_turn_ids={1, 2})
        self.assertEqual(len(out.dimensions), 5)

    def test_missing_dimension(self):
        data = _valid_data()
        data["dimensions"] = data["dimensions"][:4]
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})

    def test_duplicate_dimension(self):
        data = _valid_data()
        data["dimensions"][1]["dimension"] = "产品思维"
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})

    def test_unknown_dimension(self):
        data = _valid_data()
        data["dimensions"][0]["dimension"] = "未知维度"
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})

    def test_more_than_five_dimensions(self):
        data = _valid_data()
        data["dimensions"].append({"dimension": "产品思维", "score": 80, "evidence": [], "strengths": [], "weaknesses": []})
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})


# ---- 分数校验 ----
class TestScoreValidation(unittest.TestCase):
    def test_negative(self):
        data = _valid_data()
        data["dimensions"][0]["score"] = -1
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})

    def test_over_100(self):
        data = _valid_data()
        data["dimensions"][0]["score"] = 101
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})

    def test_string_score(self):
        data = _valid_data()
        data["dimensions"][0]["score"] = "84"
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})

    def test_bool_score(self):
        data = _valid_data()
        data["dimensions"][0]["score"] = True
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})


# ---- evidence 校验 ----
class TestEvidenceValidation(unittest.TestCase):
    def test_valid_turn_id(self):
        data = _valid_data(evidence_by_dim={"产品思维": [{"turn_id": 1, "observation": "o", "impact": "i"}]})
        out = validate_evaluation_output(data, {1, 2})
        self.assertEqual(out.dimensions[0].evidence[0].turn_id, 1)

    def test_nonexistent_turn_id(self):
        data = _valid_data(evidence_by_dim={"产品思维": [{"turn_id": 99, "observation": "o", "impact": "i"}]})
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, {1, 2})


# ---- Service：重试 / 幂等 / failed ----
class TestEvaluationService(unittest.TestCase):
    def setUp(self):
        self.db = Session()
        self._sid = f"intv-{id(self)}"

    def tearDown(self):
        self.db.close()

    def _make_completed_session(self):
        s = InterviewSession(
            id=self._sid, user_id="u1", direction="AI产品经理", difficulty="中等",
            interview_type="AI产品", status=STATUS_COMPLETED, config_snapshot={}, current_round=1,
            end_reason="manual",
        )
        self.db.add(s)
        t = InterviewTurn(
            session_id=self._sid, round_number=1, question_id="q1", question_content="主问题",
            question_type="main", knowledge_ids=["rag", "llm"], evaluation_points=["p"],
            reference_answer="a", answer_content="回答", answer_length=2,
        )
        self.db.add(t)
        self.db.commit()

    def test_retry_once_then_success(self):
        self._make_completed_session()
        llm = MockLLM(outputs=["garbage", _valid_json()])
        svc = EvaluationService(self.db, llm_adapter=llm)
        report = svc.evaluate_session("u1", self._sid)
        self.assertEqual(report.status, EVAL_STATUS_COMPLETED)
        self.assertEqual(report.overall_score, 81)
        self.assertEqual(llm.calls, 2)

    def test_retry_failure_persists_failed(self):
        self._make_completed_session()
        llm = MockLLM(outputs=["garbage", "still garbage"])
        svc = EvaluationService(self.db, llm_adapter=llm)
        with self.assertRaises(InterviewError) as ctx:
            svc.evaluate_session("u1", self._sid)
        self.assertEqual(ctx.exception.code, InterviewErrorCode.evaluation_failed)
        ev = self.db.execute(select(InterviewEvaluation).where(InterviewEvaluation.session_id == self._sid)).scalars().first()
        self.assertIsNotNone(ev)
        self.assertEqual(ev.status, EVAL_STATUS_FAILED)
        self.assertIsNone(ev.overall_score)
        self.assertEqual(ev.error_code, "EVALUATION_FAILED")

    def test_idempotent_success(self):
        self._make_completed_session()
        llm = MockLLM(outputs=[_valid_json()])
        svc = EvaluationService(self.db, llm_adapter=llm)
        first = svc.evaluate_session("u1", self._sid)
        second = svc.evaluate_session("u1", self._sid)
        self.assertEqual(first.evaluation_id, second.evaluation_id)
        self.assertEqual(llm.calls, 1)  # 不重复调用 LLM


# ---- 知识推荐 ----
class TestRecommendation(unittest.TestCase):
    def _index(self):
        return {
            "k1": {"title": "K1", "category": "ai"},
            "k2": {"title": "K2", "category": "ai"},
            "k3": {"title": "K3", "category": "product"},
        }

    def test_recommend_from_knowledge_ids(self):
        dims = _dims({"产品思维": 85, "需求分析": 85, "逻辑与表达": 85, "AI知识": 50, "业务意识": 85})
        dims[3].evidence = [EvidenceItem(turn_id=1, observation="o", impact="i")]
        turns = [SimpleNamespace(id=1, knowledge_ids=["k1", "k2"])]
        recs = recommend_knowledge(dims, turns, self._index())
        self.assertEqual([r["knowledge_id"] for r in recs], ["k1", "k2"])

    def test_dedupe_across_turns(self):
        dims = _dims({"产品思维": 85, "需求分析": 85, "逻辑与表达": 85, "AI知识": 50, "业务意识": 85})
        dims[3].evidence = [
            EvidenceItem(turn_id=1, observation="o", impact="i"),
            EvidenceItem(turn_id=2, observation="o", impact="i"),
        ]
        turns = [
            SimpleNamespace(id=1, knowledge_ids=["k1", "k2"]),
            SimpleNamespace(id=2, knowledge_ids=["k1", "k3"]),
        ]
        recs = recommend_knowledge(dims, turns, self._index())
        ids = [r["knowledge_id"] for r in recs]
        self.assertEqual(len(ids), len(set(ids)))  # 不重复
        self.assertEqual(set(ids), {"k1", "k2", "k3"})
        self.assertEqual(ids[0], "k1")  # 频次最高排最前

    def test_no_weak_dimension_returns_empty(self):
        dims = _dims({"产品思维": 85, "需求分析": 85, "逻辑与表达": 85, "AI知识": 85, "业务意识": 85})
        turns = [SimpleNamespace(id=1, knowledge_ids=["k1"])]
        self.assertEqual(recommend_knowledge(dims, turns, self._index()), [])


if __name__ == "__main__":
    unittest.main()
