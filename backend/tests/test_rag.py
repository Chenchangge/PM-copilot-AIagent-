"""RAG 数据管线测试（Loader / Chunker / Embedding / Chroma / Indexer）。"""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.core.capabilities import resolve_capabilities
from app.rag.chunker import KnowledgeChunker
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.indexer import KnowledgeIndexer
from app.rag.loader import MarkdownLoader
from app.services.model_router import model_router
from app.services.providers.embedding import MockEmbeddingAdapter


class TestMarkdownLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = MarkdownLoader().load()

    def test_document_count(self):
        self.assertGreater(len(self.docs), 200)

    def test_unique_ids(self):
        ids = [d.id for d in self.docs]
        self.assertEqual(len(ids), len(set(ids)))

    def test_metadata_and_content(self):
        doc = self.docs[0]
        self.assertTrue(doc.id)
        self.assertTrue(doc.title)
        self.assertTrue(doc.category)
        self.assertTrue(doc.content)
        self.assertTrue(doc.source_path)
        self.assertNotIn("---", doc.content)  # front matter 已去除


class TestChunker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = MarkdownLoader().load()[0]
        cls.chunks = KnowledgeChunker().chunk(cls.doc)

    def test_chunks_generated(self):
        self.assertGreaterEqual(len(self.chunks), 1)

    def test_chunk_ids_unique(self):
        ids = [c.chunk_id for c in self.chunks]
        self.assertEqual(len(ids), len(set(ids)))

    def test_chunk_metadata(self):
        for c in self.chunks:
            self.assertEqual(c.metadata["document_id"], self.doc.id)
            self.assertEqual(c.metadata["title"], self.doc.title)
            self.assertIn("section", c.metadata)
            self.assertIn("source_path", c.metadata)

    def test_chunk_has_context(self):
        self.assertIn(self.doc.title, self.chunks[0].content)


class TestMockEmbedding(unittest.TestCase):
    def test_shape(self):
        vecs = MockEmbeddingAdapter().embed(["hello", "world"])
        self.assertEqual(len(vecs), 2)
        self.assertEqual(len(vecs[0]), 384)

    def test_deterministic(self):
        emb = MockEmbeddingAdapter()
        self.assertEqual(emb.embed(["a", "b"]), emb.embed(["a", "b"]))


class TestIndexer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = MarkdownLoader().load()
        cls.tmp = tempfile.mkdtemp()
        cls.indexer = KnowledgeIndexer(embedding=MockEmbeddingAdapter(), persist_dir=cls.tmp)

    def test_build_and_count(self):
        stats = self.indexer.build(self.docs)
        self.assertGreater(stats["document_count"], 200)
        self.assertEqual(stats["chunk_count"], stats["embedding_count"])
        self.assertGreater(stats["chunk_count"], 0)
        col = self.indexer._client.get_collection(self.indexer.collection_name)
        self.assertEqual(col.count(), stats["chunk_count"])

    def test_build_idempotent(self):
        self.indexer.build(self.docs)
        col = self.indexer._client.get_collection(self.indexer.collection_name)
        n1 = col.count()
        self.indexer.build(self.docs)
        self.assertEqual(col.count(), n1)

    def test_rebuild(self):
        stats = self.indexer.rebuild(self.docs)
        col = self.indexer._client.get_collection(self.indexer.collection_name)
        self.assertEqual(col.count(), stats["chunk_count"])

    def test_embedding_model_metadata(self):
        self.indexer.build(self.docs)
        meta = self.indexer._meta.load()
        self.assertEqual(meta["embedding_model"], "mock-embedding-384d")
        self.assertIn("knowledge_hash", meta)

    def test_index_meta_records_dimension(self):
        self.indexer.build(self.docs)
        meta = self.indexer._meta.load()
        self.assertEqual(meta["dimension"], 384)  # MockEmbeddingAdapter 维度


class TestEmbeddingCapability(unittest.TestCase):
    def test_embedding_model_name_supported(self):
        caps = resolve_capabilities("openai", "text-embedding-3-small")
        self.assertEqual(caps["embedding"], "supported")

    def test_deepseek_flash_not_embedding(self):
        caps = resolve_capabilities("deepseek", "deepseek-flash")
        self.assertEqual(caps["embedding"], "unknown")

    def test_router_filters_embedding(self):
        models = [
            SimpleNamespace(capabilities={"embedding": "supported"}),
            SimpleNamespace(capabilities={"embedding": "unknown"}),
            SimpleNamespace(capabilities={"embedding": "unsupported"}),
        ]
        eligible = model_router.find_models_by_capabilities(models, ["embedding"])
        self.assertEqual(len(eligible), 1)


class TestInvalidMarkdown(unittest.TestCase):
    def test_missing_id_raises(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "product").mkdir()
        (tmp / "product" / "bad.md").write_text(
            "# 无 metadata\n\n## 定义\n没有 front matter。", encoding="utf-8"
        )
        loader = MarkdownLoader(data_dir=tmp)
        with self.assertRaises(RAGError) as ctx:
            loader.load()
        self.assertEqual(ctx.exception.code, RAGErrorCode.invalid_knowledge_metadata)


if __name__ == "__main__":
    unittest.main()
