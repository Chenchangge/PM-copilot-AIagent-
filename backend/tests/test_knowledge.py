"""知识库 Learning 服务单元测试（基于真实 Markdown 解析，不依赖 DB / 不 mock）。"""
import unittest

from app.rag.errors import RAGError, RAGErrorCode
from app.services.knowledge_service import KnowledgeService


class TestKnowledgeService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = KnowledgeService()

    def test_list_total(self):
        resp = self.service.list_knowledge()
        self.assertGreater(resp.total, 200)
        ids = [i.id for i in resp.items]
        self.assertIn("rag-basics", ids)
        self.assertIn("mvp", ids)
        self.assertIn("agent-basics", ids)

    def test_list_items_are_slugs(self):
        resp = self.service.list_knowledge()
        for i in resp.items:
            self.assertTrue(i.id and isinstance(i.id, str))
            self.assertTrue(i.title)
            self.assertTrue(i.category)

    def test_category_filter_ai(self):
        resp = self.service.list_knowledge(category="ai-product")
        self.assertGreater(resp.total, 0)
        self.assertTrue(all(i.category == "ai-product" for i in resp.items))

    def test_category_filter_unknown_returns_empty(self):
        resp = self.service.list_knowledge(category="nope")
        self.assertEqual(resp.total, 0)
        self.assertEqual(resp.items, [])

    def test_get_rag(self):
        d = self.service.get_knowledge("rag-basics")
        self.assertEqual(d.id, "rag-basics")
        self.assertEqual(d.category, "ai-product")
        self.assertTrue(d.definition)
        self.assertTrue(d.core_content)
        self.assertIsInstance(d.common_scenarios, list)
        self.assertIsInstance(d.pm_focus, list)

    def test_get_mvp(self):
        d = self.service.get_knowledge("mvp")
        self.assertEqual(d.id, "mvp")
        self.assertEqual(d.category, "product-foundation")
        self.assertTrue(d.definition)
        self.assertTrue(d.core_content)
        self.assertGreaterEqual(len(d.common_scenarios), 1)
        self.assertGreaterEqual(len(d.pm_focus), 1)

    def test_get_ai_agent(self):
        d = self.service.get_knowledge("agent-basics")
        self.assertEqual(d.id, "agent-basics")
        self.assertEqual(d.category, "ai-product")
        self.assertTrue(d.definition)

    def test_not_found(self):
        with self.assertRaises(RAGError) as ctx:
            self.service.get_knowledge("not-exist")
        self.assertEqual(ctx.exception.code, RAGErrorCode.knowledge_not_found)


if __name__ == "__main__":
    unittest.main()
