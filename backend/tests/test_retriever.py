"""RAG Retriever 测试（临时 Chroma + Mock Embedding，可重复，不依赖本机数据）。"""
import tempfile
import unittest

from app.rag.document import KnowledgeDocument
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.indexer import KnowledgeIndexer
from app.rag.retriever import Retriever
from app.services.providers.embedding import MockEmbeddingAdapter


def _make_docs():
    return [
        KnowledgeDocument(
            id="mvp", title="MVP", category="product", tags=["产品基础"], difficulty="beginner",
            content="## 定义\n最小可行产品，用于验证核心假设。\n## 核心内容\n明确验证目标，保留最小闭环。",
            source_path="knowledge/data/product/mvp.md",
        ),
        KnowledgeDocument(
            id="rag", title="RAG", category="ai", tags=["AI产品"], difficulty="intermediate",
            content="## 定义\n检索增强生成。\n## 核心内容\n先检索相关知识，再基于知识生成回答。",
            source_path="knowledge/data/ai/rag.md",
        ),
        KnowledgeDocument(
            id="funnel-analysis", title="漏斗分析", category="data", tags=["数据分析"], difficulty="intermediate",
            content="## 定义\n定位用户流失环节。\n## 核心内容\n逐层拆解转化率。",
            source_path="knowledge/data/data/funnel-analysis.md",
        ),
    ]


class _RaiseEmbedding(MockEmbeddingAdapter):
    def embed(self, texts):
        raise RuntimeError("provider down")


class TestRetriever(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.embedding = MockEmbeddingAdapter()
        cls.indexer = KnowledgeIndexer(embedding=cls.embedding, persist_dir=cls.tmp)
        cls.indexer.build(_make_docs())
        cls.retriever = Retriever(embedding=cls.embedding, persist_dir=cls.tmp)

    # ---- query 校验 ----
    def test_empty_query(self):
        with self.assertRaises(RAGError) as ctx:
            self.retriever.retrieve("   ")
        self.assertEqual(ctx.exception.code, RAGErrorCode.retrieval_invalid_query)

    def test_non_string_query(self):
        with self.assertRaises(RAGError) as ctx:
            self.retriever.retrieve(123)
        self.assertEqual(ctx.exception.code, RAGErrorCode.retrieval_invalid_query)

    def test_query_too_long(self):
        with self.assertRaises(RAGError) as ctx:
            self.retriever.retrieve("长" * 2001)
        self.assertEqual(ctx.exception.code, RAGErrorCode.retrieval_invalid_query)

    # ---- top_k 校验 ----
    def test_top_k_default(self):
        result = self.retriever.retrieve("MVP")
        self.assertGreater(len(result.results), 0)
        self.assertLessEqual(len(result.results), 5)

    def test_top_k_1(self):
        result = self.retriever.retrieve("MVP", top_k=1)
        self.assertEqual(len(result.results), 1)

    def test_top_k_20_valid(self):
        result = self.retriever.retrieve("MVP", top_k=20)
        self.assertLessEqual(len(result.results), 20)

    def test_top_k_over_20(self):
        with self.assertRaises(RAGError) as ctx:
            self.retriever.retrieve("MVP", top_k=21)
        self.assertEqual(ctx.exception.code, RAGErrorCode.retrieval_invalid_top_k)

    def test_top_k_zero(self):
        with self.assertRaises(RAGError) as ctx:
            self.retriever.retrieve("MVP", top_k=0)
        self.assertEqual(ctx.exception.code, RAGErrorCode.retrieval_invalid_top_k)

    # ---- 结果字段 ----
    def test_metadata_fields(self):
        item = self.retriever.retrieve("MVP", top_k=1).results[0]
        self.assertTrue(item.chunk_id)
        self.assertTrue(item.knowledge_id)
        self.assertTrue(item.title)
        self.assertTrue(item.category)
        self.assertTrue(item.source_path)

    def test_source_path_relative(self):
        for item in self.retriever.retrieve("MVP", top_k=3).results:
            self.assertTrue(item.source_path.startswith("knowledge/data/"))
            self.assertNotIn(":", item.source_path)  # 无 Windows 盘符
            self.assertNotIn("/home/", item.source_path)

    def test_distance_is_float(self):
        for item in self.retriever.retrieve("MVP", top_k=3).results:
            self.assertIsInstance(item.distance, float)
            self.assertGreaterEqual(item.distance, 0)

    def test_score_semantics_cosine(self):
        for item in self.retriever.retrieve("MVP", top_k=3).results:
            self.assertAlmostEqual(item.score, 1 - item.distance, delta=1e-5)

    def test_results_sorted_by_distance(self):
        distances = [it.distance for it in self.retriever.retrieve("MVP 验证假设", top_k=5).results]
        self.assertEqual(distances, sorted(distances))  # 距离升序 = 相关度降序

    # ---- threshold ----
    def test_threshold_all_filtered(self):
        result = self.retriever.retrieve("MVP", top_k=3, similarity_threshold=0.999)
        self.assertEqual(result.results, [])

    def test_threshold_partial_filter(self):
        from app.rag.retriever import RetrieverItem

        items = [
            RetrieverItem(chunk_id="a", knowledge_id="k", title="t", category="c", distance=0.1, score=0.9),
            RetrieverItem(chunk_id="b", knowledge_id="k", title="t", category="c", distance=0.8, score=0.2),
        ]
        filtered = self.retriever._apply_threshold(items, similarity_threshold=0.5, max_distance=None)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].chunk_id, "a")

    # ---- 错误 ----
    def test_index_not_found(self):
        retriever = Retriever(embedding=self.embedding, persist_dir=tempfile.mkdtemp())
        with self.assertRaises(RAGError) as ctx:
            retriever.retrieve("MVP")
        self.assertEqual(ctx.exception.code, RAGErrorCode.index_not_found)

    def test_model_mismatch(self):
        other = MockEmbeddingAdapter()
        other.model = "different-model"
        with self.assertRaises(RAGError) as ctx:
            Retriever(embedding=other, persist_dir=self.tmp).retrieve("MVP")
        self.assertEqual(ctx.exception.code, RAGErrorCode.index_model_mismatch)

    def test_embedding_provider_error(self):
        with self.assertRaises(RAGError) as ctx:
            Retriever(embedding=_RaiseEmbedding(), persist_dir=self.tmp).retrieve("MVP")
        self.assertEqual(ctx.exception.code, RAGErrorCode.retrieval_provider_error)

    def test_dimension_mismatch(self):
        # 独立临时目录，避免污染共享索引
        tmp = tempfile.mkdtemp()
        emb = MockEmbeddingAdapter()
        indexer = KnowledgeIndexer(embedding=emb, persist_dir=tmp)
        indexer.build(_make_docs())
        # 篡改 meta 维度，模拟索引由不同维度模型构建
        meta = indexer._meta.load()
        meta["dimension"] = 128
        indexer._meta.save(meta)
        with self.assertRaises(RAGError) as ctx:
            Retriever(embedding=emb, persist_dir=tmp).retrieve("MVP")
        self.assertEqual(ctx.exception.code, RAGErrorCode.index_model_mismatch)


class TestEmbeddingModelResolution(unittest.TestCase):
    def test_find_embedding_model_returns_none_when_empty(self):
        import tempfile as _tf

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.db.database import Base
        from app.services.model_service import ModelService

        engine = create_engine(
            f"sqlite:///{_tf.mkdtemp()}/t.db", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            self.assertIsNone(ModelService(db).find_embedding_model("anonymous"))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
