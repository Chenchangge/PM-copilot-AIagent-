"""P0-2 知识详情页：库里已有内容必须能端出来。

验收基准：打开 mvp 详情能看到 ≥3 条常见误区、≥2 条前置知识、≥5 道相关面试题；
页面区块从 4 个增至 ≥7 个（前端验收），后端保证数据字段齐全且空数据返回空数组。
"""
import unittest

from fastapi.testclient import TestClient

from app.db.database import Base, engine, init_db
from app.main import app
from app.services.knowledge_service import KnowledgeService


class TestKnowledgeDetailService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = KnowledgeService()

    def test_mvp_has_new_blocks(self):
        detail = self.service.get_knowledge("mvp")
        self.assertGreaterEqual(len(detail.misconceptions), 3)
        self.assertGreaterEqual(len(detail.prerequisites), 2)
        self.assertGreaterEqual(len(detail.related), 1)
        self.assertGreaterEqual(len(detail.related_questions), 5)
        self.assertEqual(detail.cases, [])  # mvp 没有案例，前端应隐藏该区块

    def test_prerequisites_have_titles(self):
        detail = self.service.get_knowledge("mvp")
        for item in detail.prerequisites:
            self.assertTrue(item.id)
            self.assertTrue(item.title)
        self.assertIn(
            "产品目标与成功标准",
            [item.title for item in detail.prerequisites],
        )

    def test_related_have_title_and_category(self):
        detail = self.service.get_knowledge("mvp")
        for item in detail.related:
            self.assertTrue(item.title)
            self.assertTrue(item.category)
            self.assertNotEqual(item.id, "mvp")

    def test_related_questions_are_capped_and_have_answers(self):
        detail = self.service.get_knowledge("mvp")
        self.assertLessEqual(len(detail.related_questions), 5)
        self.assertEqual(len({q.id for q in detail.related_questions}), len(detail.related_questions))
        for q in detail.related_questions:
            self.assertTrue(q.content)
            self.assertTrue(q.reference_answer)
        self.assertEqual(detail.related_questions[0].relation, "core")

    def test_case_doc_returns_cases(self):
        detail = self.service.get_knowledge("golden-set")
        self.assertGreaterEqual(len(detail.cases), 1)


class TestKnowledgeDetailAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def test_mvp_detail_api(self):
        resp = self.client.get("/api/knowledge/mvp")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(len(data["misconceptions"]), 3)
        self.assertGreaterEqual(len(data["prerequisites"]), 2)
        self.assertGreaterEqual(len(data["related"]), 1)
        self.assertGreaterEqual(len(data["related_questions"]), 5)
        self.assertLessEqual(len(data["related_questions"]), 5)
        self.assertTrue(data["related_questions"][0]["reference_answer"])

    def test_empty_cases_are_empty_not_missing(self):
        data = self.client.get("/api/knowledge/mvp").json()
        self.assertIn("cases", data)
        self.assertEqual(data["cases"], [])

    def test_case_doc_api(self):
        data = self.client.get("/api/knowledge/golden-set").json()
        self.assertGreaterEqual(len(data["cases"]), 1)


if __name__ == "__main__":
    unittest.main()
