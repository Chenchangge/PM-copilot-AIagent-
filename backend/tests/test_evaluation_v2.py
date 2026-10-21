"""P0-3 面试评价：逐题复盘 / 未考察维度 / 差异化推荐。

验收基准：一场含主问题 + 追问的评价报告能展开 ≥2 道题的参考答案与评分点；
没有证据的维度返回 null 显示「本场未考察」；两条推荐学习理由不同。
"""
import json
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/eval_v2.db"
os.environ["ENVIRONMENT"] = "test"

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: F401  # 注册模型  # noqa: E402
from app.db.database import Base  # noqa: E402
from app.interview.constants import EVALUATION_DIMENSIONS, STATUS_COMPLETED  # noqa: E402
from app.interview.evaluation import (  # noqa: E402
    EvaluationParseError,
    calculate_overall_score,
    validate_evaluation_output,
)
from app.models.interview import InterviewSession, InterviewTurn  # noqa: E402
from app.schemas.evaluation import DimensionEvaluation  # noqa: E402
from app.services.evaluation_service import EvaluationService  # noqa: E402

ENGINE = create_engine(f"sqlite:///{_TMP}/eval_v2_engine.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=ENGINE)
Session = sessionmaker(bind=ENGINE)


def _evidence(turn_id, observation="回答有结构", impact="支撑判断"):
    return {"turn_id": turn_id, "observation": observation, "impact": impact}


def _payload():
    """主问题 + 追问；产品思维/需求分析/逻辑/业务意识有证据，AI知识无证据。"""
    dim_data = {
        "产品思维": (80, [_evidence(1)]),
        "需求分析": (70, [_evidence(2)]),
        "逻辑与表达": (65, [_evidence(2)]),
        "AI知识": (50, []),  # LLM 给了中位分，但无证据 -> 后端必须置 null
        "业务意识": (60, [_evidence(1)]),
    }
    dimensions = [
        {
            "dimension": name,
            "score": dim_data[name][0],
            "evidence": dim_data[name][1],
            "strengths": [f"{name}优势"],
            "weaknesses": [f"{name}需要加强"],
        }
        for name in EVALUATION_DIMENSIONS
    ]
    return {
        "dimensions": dimensions,
        "question_reviews": [
            {
                "turn_id": 1,
                "score": 78,
                "point_results": [
                    {"point": "p1", "status": "met", "comment": "覆盖"},
                    {"point": "p2", "status": "partial", "comment": "缺边界"},
                ],
                "comment": "主问题回答结构清楚",
            },
            {
                "turn_id": 2,
                "score": 70,
                "point_results": [
                    {"point": "p1", "status": "met", "comment": "追问保持了观点"},
                    {"point": "p2", "status": "missed", "comment": "没有补充指标"},
                ],
                "comment": "追问答得略浅",
            },
        ],
        "overall_strengths": ["表达清楚"],
        "overall_weaknesses": ["指标不足"],
        "summary": "整体合格，需要补指标。",
    }


class MockLLM:
    def __init__(self, content):
        self.content = content
        self.provider = "mock"
        self.model = "mock-llm"
        self.calls = 0

    def generate(self, messages, options=None):
        self.calls += 1
        return {"content": self.content}

    def classify_error(self, exc):
        return "PROVIDER_ERROR", "模型服务返回错误"


class TestUnassessedDimension(unittest.TestCase):
    def test_no_evidence_dimension_becomes_null(self):
        out = validate_evaluation_output(_payload(), valid_turn_ids={1, 2})
        by_name = {d.dimension: d for d in out.dimensions}
        self.assertIsNone(by_name["AI知识"].score)
        self.assertEqual(by_name["产品思维"].score, 80)
        self.assertEqual(out.question_reviews[0].point_results[1].status, "partial")

    def test_all_empty_evidence_keeps_legacy_scores(self):
        # 兼容旧模型/旧数据：整场都没有 evidence 时保留原分数，不把报告打成 0。
        data = _payload()
        for d in data["dimensions"]:
            d["evidence"] = []
        out = validate_evaluation_output(data, valid_turn_ids={1, 2})
        self.assertEqual({d.dimension: d.score for d in out.dimensions}["AI知识"], 50)

    def test_overall_score_normalizes_assessed_weights(self):
        dims = [
            DimensionEvaluation(dimension="产品思维", score=80),
            DimensionEvaluation(dimension="逻辑与表达", score=60),
            DimensionEvaluation(dimension="AI知识", score=None),
        ]
        # (80*.3 + 60*.2) / (.3+.2) = 72
        self.assertEqual(calculate_overall_score(dims), 72)

    def test_invalid_question_review_turn_rejected(self):
        data = _payload()
        data["question_reviews"][0]["turn_id"] = 99
        with self.assertRaises(EvaluationParseError):
            validate_evaluation_output(data, valid_turn_ids={1, 2})


class TestTurnReviewReport(unittest.TestCase):
    def setUp(self):
        self.db = Session()
        self.sid = f"intv-{id(self)}"
        self._seed_session()

    def tearDown(self):
        self.db.close()

    def _seed_session(self):
        self.db.add(
            InterviewSession(
                id=self.sid,
                user_id="u1",
                direction="AI产品经理",
                difficulty="中等",
                interview_type="AI产品",
                status=STATUS_COMPLETED,
                config_snapshot={},
                current_round=1,
                end_reason="manual",
            )
        )
        self.db.add_all(
            [
                InterviewTurn(
                    session_id=self.sid,
                    round_number=1,
                    question_id="q1",
                    question_content="什么是 MVP？",
                    question_type="main",
                    knowledge_ids=["k1", "k2"],
                    evaluation_points=["p1", "p2"],
                    reference_answer="MVP 是验证假设的最小方案。",
                    answer_content="MVP 是用于验证假设的最小可用产品。" * 4,
                    answer_length=80,
                ),
                InterviewTurn(
                    session_id=self.sid,
                    round_number=1,
                    question_id="q1",
                    question_content="如果用户不愿意用，你怎么验证？",
                    question_type="follow_up",
                    follow_up_type="验证方式追问",
                    knowledge_ids=["k3"],
                    evaluation_points=["p1", "p2"],
                    reference_answer="先定义可观察行为，再用访谈/实验验证。",
                    answer_content="我会先看行为数据，再补用户访谈。" * 3,
                    answer_length=48,
                ),
            ]
        )
        self.db.commit()

    def test_report_has_two_turn_reviews_with_points_and_answers(self):
        knowledge_index = {
            "k1": {"title": "MVP", "category": "product-foundation"},
            "k2": {"title": "产品验证", "category": "product-foundation"},
            "k3": {"title": "用户研究", "category": "user-research"},
        }
        svc = EvaluationService(
            self.db,
            llm_adapter=MockLLM(json.dumps(_payload(), ensure_ascii=False)),
            knowledge_index=knowledge_index,
        )
        report = svc.evaluate_session("u1", self.sid)

        self.assertEqual(len(report.turn_reviews), 2)
        first, second = report.turn_reviews
        self.assertEqual(first.round_number, 1)
        self.assertEqual(first.question_type, "main")
        self.assertEqual(second.question_type, "follow_up")
        self.assertEqual(second.follow_up_type, "验证方式追问")
        self.assertEqual(first.score, 78)
        self.assertEqual(second.score, 70)
        self.assertEqual([p.status for p in first.point_results], ["met", "partial"])
        self.assertEqual([p.status for p in second.point_results], ["met", "missed"])
        self.assertTrue(first.reference_answer)
        self.assertTrue(second.reference_answer)
        self.assertTrue(first.answer)
        self.assertEqual({d.dimension: d.score for d in report.dimensions}["AI知识"], None)

        # 两条推荐理由必须不同（按维度和薄弱点差异化）
        reasons = [r.reason for r in report.recommended_knowledge]
        self.assertGreaterEqual(len(reasons), 2)
        self.assertEqual(len(reasons), len(set(reasons)), reasons)

        # 持久化后 GET 报告仍能拿到逐题复盘
        again = svc.get_evaluation("u1", self.sid)
        self.assertEqual(len(again.turn_reviews), 2)
        self.assertEqual(again.turn_reviews[0].point_results[0].status, "met")


if __name__ == "__main__":
    unittest.main()
