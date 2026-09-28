"""分类体系 / 数据完整性测试（Step 12-4：统一知识库分类 → 知识点 → 面试题 → Learning Plan）。

覆盖 §十六：
1. 11 KnowledgeCategory seed  2. 10 InterviewType seed  3. 4 ProductDirection seed
4. 3 Specialization seed      5. KnowledgePoint category 映射  6. KnowledgePoint topic 映射
7. InterviewQuestion type 映射  8. InterviewQuestion direction 映射
9. QuestionKnowledge core/related/prerequisite  10. Learning Plan 使用新 taxonomy
11. 旧分类历史数据兼容  12. 不存在孤立 KnowledgePoint  13. 不存在孤立 InterviewQuestion
14. 不存在非法 taxonomy id
"""
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/taxonomy_test.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.db.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.interview.question_bank import QuestionBank  # noqa: E402
from app.learning.constants import (  # noqa: E402
    CATEGORY_NAMES,
    DIRECTIONS,
    INTERVIEW_TYPES,
    KNOWLEDGE_CATEGORIES,
    KNOWLEDGE_TOPICS,
    LEGACY_CATEGORY_LABELS,
    SPECIALIZATIONS,
    TOPIC_CATEGORY,
    TOPIC_NAMES,
)
from app.learning.knowledge_index import build_knowledge_index, resolve_target  # noqa: E402
from app.learning.service import LearningService  # noqa: E402
from app.main import app  # noqa: E402
from app.models.taxonomy import (  # noqa: E402
    InterviewType,
    KnowledgeCategory,
    KnowledgeTopic,
    ProductDirection,
    QuestionKnowledge,
    Specialization,
)
from app.rag.loader import MarkdownLoader  # noqa: E402


def _ids(db, model) -> set[str]:
    return {r.id for r in db.execute(select(model)).scalars().all()}


class TestTaxonomySeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_categories_seed_11(self):
        ids = _ids(self.db, KnowledgeCategory)
        self.assertEqual(len(ids), 11)
        self.assertEqual(ids, {slug for slug, _ in KNOWLEDGE_CATEGORIES})

    def test_interview_types_seed_10(self):
        ids = _ids(self.db, InterviewType)
        self.assertEqual(len(ids), 10)
        self.assertEqual(ids, set(INTERVIEW_TYPES))
        self.assertNotIn("综合面试", ids)  # 综合面试是 InterviewMode，不是 InterviewType

    def test_directions_seed_4(self):
        ids = _ids(self.db, ProductDirection)
        self.assertEqual(len(ids), 4)
        self.assertEqual(ids, set(DIRECTIONS))

    def test_specializations_seed_3(self):
        ids = _ids(self.db, Specialization)
        self.assertEqual(ids, set(SPECIALIZATIONS))
        self.assertNotIn("行业解决方案", ids)  # 旧命名已清理

    def test_topics_seed(self):
        rows = {r.id: r for r in self.db.execute(select(KnowledgeTopic)).scalars().all()}
        self.assertEqual(len(rows), len(KNOWLEDGE_TOPICS))
        for category_slug, topic_slug, name in KNOWLEDGE_TOPICS:
            self.assertIn(topic_slug, rows, f"缺少 topic {topic_slug}")
            self.assertEqual(rows[topic_slug].category_id, category_slug)
            self.assertEqual(rows[topic_slug].name, name)

    def test_seed_cleans_legacy_1to1_topics(self):
        # 旧 seed 曾产生 1:1 topic（id == category_id）；重跑 seed 应被清理（幂等 + 不重复）
        from app.learning.seed import seed_taxonomy

        self.db.add(KnowledgeTopic(id="ai-product", category_id="ai-product", name="AI产品"))
        self.db.commit()
        seed_taxonomy(self.db)
        ids = {r.id for r in self.db.execute(select(KnowledgeTopic)).scalars().all()}
        self.assertNotIn("ai-product", ids)  # 旧 1:1 topic 已清理
        self.assertIn("rag-retrieval", ids)  # 新 topic 保留
        self.assertEqual(len(ids), len(KNOWLEDGE_TOPICS))


class TestKnowledgeDataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = MarkdownLoader().load()
        cls.by_id = {d.id: d for d in cls.docs}

    def test_45_points(self):
        self.assertGreater(len(self.docs), 200)

    def test_category_valid(self):
        valid = set(CATEGORY_NAMES)
        for d in self.docs:
            self.assertIn(d.category, valid, f"{d.id} 非法 category {d.category}")

    def test_topic_valid_and_consistent(self):
        valid_topics = set(TOPIC_NAMES)
        for d in self.docs:
            self.assertTrue(d.topic, f"{d.id} 缺少 topic")
            self.assertIn(d.topic, valid_topics, f"{d.id} 非法 topic {d.topic}")
            self.assertEqual(TOPIC_CATEGORY.get(d.topic), d.category, f"{d.id} topic 与 category 不一致")

    def test_no_tool_category(self):
        cats = {d.category for d in self.docs}
        self.assertNotIn("tools", cats)  # 工具不再是一级分类


class TestInterviewDataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = QuestionBank()
        cls.bank.load()

    def test_30_questions(self):
        self.assertGreater(self.bank.count(), 200)

    def test_type_valid(self):
        valid = set(INTERVIEW_TYPES)
        for q in self.bank.all():
            self.assertIn(q["type"], valid, f"{q['id']} 非法 type {q['type']}")

    def test_no_comprehensive_type(self):
        types = {q["type"] for q in self.bank.all()}
        self.assertNotIn("综合面试", types)

    def test_direction_valid(self):
        valid = set(DIRECTIONS)
        for q in self.bank.all():
            self.assertTrue(q["directions"], f"{q['id']} 缺少 direction")
            for d in q["directions"]:
                self.assertIn(d, valid, f"{q['id']} 非法 direction {d}")

    def test_evaluation_dimensions_bound(self):
        valid_dims = {"产品思维", "需求分析", "逻辑与表达", "AI知识", "业务意识"}
        for q in self.bank.all():
            dims = q.get("evaluation_dimensions", [])
            self.assertTrue(dims, f"{q['id']} 未绑定评价维度")
            self.assertTrue(set(dims) <= valid_dims, f"{q['id']} 非法评价维度")
            self.assertTrue(1 <= len(dims) <= 5)


class TestQuestionKnowledgeRelations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = SessionLocal()
        cls.bank = QuestionBank()
        cls.bank.load()
        cls.doc_ids = {d.id for d in MarkdownLoader().load()}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_relations_seeded_with_three_types(self):
        rows = self.db.execute(select(QuestionKnowledge)).scalars().all()
        self.assertGreater(len(rows), 30)  # 至少每题一个 core
        types = {r.relation_type for r in rows}
        self.assertEqual(types, {"core", "related", "prerequisite"})

    def test_no_orphan_knowledge(self):
        rows = self.db.execute(select(QuestionKnowledge)).scalars().all()
        for r in rows:
            self.assertIn(r.knowledge_point_id, self.doc_ids, f"孤立知识点 {r.knowledge_point_id}")

    def test_no_orphan_question(self):
        qids = {q["id"] for q in self.bank.all()}
        rows = self.db.execute(select(QuestionKnowledge)).scalars().all()
        for r in rows:
            self.assertIn(r.question_id, qids, f"孤立题目 {r.question_id}")


class TestLearningPlanNewTaxonomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.index = build_knowledge_index()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def test_resolve_direction_covers_related_categories(self):
        pts = resolve_target(self.index, "direction", "AI产品经理")
        cats = {p.category for p in pts}
        self.assertIn("ai-product", cats)
        self.assertGreater(len(pts), 0)
        self.assertGreaterEqual(len(cats), 2)

    def test_estimate_direction(self):
        resp = self.client.post(
            "/api/learning/plans/estimate",
            json={
                "target_type": "direction",
                "target_id": "AI产品经理",
                "current_level": "入门",
                "daily_minutes": 30,
                "intensity": "标准",
            },
            headers={"X-User-Id": "tax-dir"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["knowledge_count"], 0)
        self.assertEqual(data["target"]["name"], "AI产品经理")

    def test_legacy_target_name_compat(self):
        db = SessionLocal()
        try:
            svc = LearningService(db, knowledge_index={})
            self.assertEqual(svc._target_name("category", "ai"), "AI产品")  # 旧 slug 兼容
            self.assertEqual(svc._target_name("category", "ai-product"), "AI产品")
            self.assertEqual(svc._target_name("topic", "rag-retrieval"), "RAG与检索")
        finally:
            db.close()

    def test_legacy_category_labels_preserved(self):
        # 旧 6 分类 slug 仍需保留以兼容历史计划
        self.assertEqual(set(LEGACY_CATEGORY_LABELS), {"product", "design", "data", "ai", "tools", "interview"})


if __name__ == "__main__":
    unittest.main()
