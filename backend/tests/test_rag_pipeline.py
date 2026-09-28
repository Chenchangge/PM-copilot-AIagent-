"""RAG Pipeline 测试（Mock Retriever / Mock LLM + 真实 Retriever 集成）。"""
import dataclasses
import tempfile
import unittest

import httpx

from app.core.errors import AIErrorCode
from app.rag.context_builder import ContextBuilder
from app.rag.document import KnowledgeDocument
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.indexer import KnowledgeIndexer
from app.rag.pipeline import RAGPipeline
from app.rag.prompt import SYSTEM_INSTRUCTION, build_messages, build_user_message
from app.rag.retriever import Retriever, RetrieverItem, RetrieverResult
from app.services.providers.base import BaseModelAdapter, OpenAICompatibleAdapter
from app.services.providers.embedding import MockEmbeddingAdapter


def _make_docs():
    return [
        KnowledgeDocument(
            id="mvp", title="MVP", category="product", tags=["产品基础"], difficulty="beginner",
            content="## 定义\n最小可行产品，用于验证核心假设。\n## 核心内容\n明确验证目标，保留最小闭环。",
            source_path="knowledge/data/product/mvp.md",
        ),
    ]


def _chunk_item():
    return RetrieverItem(
        chunk_id="mvp:0:0", knowledge_id="mvp", title="MVP", category="product",
        tags=["产品基础"], difficulty="beginner", section="定义",
        content="最小可行产品，用于验证核心假设。",
        source_path="knowledge/data/product/mvp.md", distance=0.1, score=0.9,
    )


class MockLLM(BaseModelAdapter):
    def __init__(self, answer="根据提供的知识，MVP 是最小可行产品。"):
        super().__init__(base_url="", api_key="", model="mock-llm", provider="mock")
        self.answer = answer
        self.call_count = 0

    def test_connection(self):
        return {"success": True, "model": self.model, "latency_ms": 1, "error_code": None, "message": None}

    def generate(self, messages, options=None):
        self.call_count += 1
        return {
            "content": self.answer,
            "model": self.model,
            "provider": self.provider,
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            "latency_ms": 1,
        }


class _RaisingLLM(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__(base_url="https://api.example.com", api_key="sk-test", model="gpt", provider="openai")

    def generate(self, messages, options=None):
        raise httpx.HTTPStatusError(
            "401",
            request=httpx.Request("POST", "http://x"),
            response=httpx.Response(401, request=httpx.Request("POST", "http://x")),
        )


class MockRetriever:
    def __init__(self, results=None, error=None):
        self.results = results if results is not None else []
        self.error = error

    def retrieve(self, query, top_k=5, similarity_threshold=None, max_distance=None):
        if self.error:
            raise self.error
        return RetrieverResult(query=query, results=self.results)


class TestPipelineQueryValidation(unittest.TestCase):
    def setUp(self):
        self.pipeline = RAGPipeline(retriever=MockRetriever(), llm_adapter=MockLLM())

    def test_empty_query(self):
        with self.assertRaises(RAGError) as ctx:
            self.pipeline.run("   ")
        self.assertEqual(ctx.exception.code, RAGErrorCode.retrieval_invalid_query)

    def test_blank_query(self):
        with self.assertRaises(RAGError):
            self.pipeline.run("")

    def test_query_too_long(self):
        with self.assertRaises(RAGError):
            self.pipeline.run("长" * 2001)

    def test_non_string_query(self):
        with self.assertRaises(RAGError):
            self.pipeline.run(123)


class TestPipelineOrchestration(unittest.TestCase):
    def setUp(self):
        self.llm = MockLLM()

    def test_normal_run(self):
        pipeline = RAGPipeline(retriever=MockRetriever([_chunk_item()]), llm_adapter=self.llm)
        result = pipeline.run("什么是 MVP")
        self.assertEqual(result.answer, "根据提供的知识，MVP 是最小可行产品。")
        self.assertEqual(result.retrieval_count, 1)
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(self.llm.call_count, 1)

    def test_empty_retrieval_does_not_call_llm(self):
        pipeline = RAGPipeline(retriever=MockRetriever([]), llm_adapter=self.llm)
        result = pipeline.run("什么是 RAG")
        self.assertEqual(result.retrieval_count, 0)
        self.assertEqual(result.sources, [])
        self.assertIn("没有找到足够相关", result.answer)
        self.assertEqual(self.llm.call_count, 0)

    def test_retriever_error_propagates(self):
        retriever = MockRetriever(error=RAGError(RAGErrorCode.index_not_found, "索引不存在"))
        pipeline = RAGPipeline(retriever=retriever, llm_adapter=self.llm)
        with self.assertRaises(RAGError) as ctx:
            pipeline.run("MVP")
        self.assertEqual(ctx.exception.code, RAGErrorCode.index_not_found)

    def test_result_fields(self):
        pipeline = RAGPipeline(retriever=MockRetriever([_chunk_item()]), llm_adapter=self.llm)
        result = pipeline.run("什么是 MVP")
        self.assertEqual(result.query, "什么是 MVP")
        self.assertEqual(result.model, "mock-llm")
        self.assertEqual(result.provider, "mock")
        self.assertEqual(result.usage["total_tokens"], 30)

    def test_sources_not_from_llm(self):
        llm = MockLLM(answer="来源：knowledge/data/xxx.md。MVP 是……")
        pipeline = RAGPipeline(retriever=MockRetriever([_chunk_item()]), llm_adapter=llm)
        result = pipeline.run("MVP")
        self.assertEqual(result.sources[0].source_path, "knowledge/data/product/mvp.md")

    def test_no_api_key_in_result(self):
        pipeline = RAGPipeline(retriever=MockRetriever([_chunk_item()]), llm_adapter=self.llm)
        result = pipeline.run("MVP")
        d = dataclasses.asdict(result)
        self.assertNotIn("api_key", str(d).lower())
        self.assertNotIn("sk-", str(d))


class TestPipelineLLMError(unittest.TestCase):
    def test_llm_provider_error_mapped(self):
        pipeline = RAGPipeline(retriever=MockRetriever([_chunk_item()]), llm_adapter=_RaisingLLM())
        with self.assertRaises(RAGError) as ctx:
            pipeline.run("MVP")
        self.assertEqual(ctx.exception.code, AIErrorCode.invalid_api_key)


class TestContextBuilder(unittest.TestCase):
    def test_build_and_sources(self):
        context, sources = ContextBuilder().build([_chunk_item(), _chunk_item()])
        self.assertIn("[知识] MVP", context)
        self.assertIn("knowledge/data/product/mvp.md", context)
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0].knowledge_id, "mvp")
        self.assertEqual(sources[0].source_path, "knowledge/data/product/mvp.md")

    def test_length_limit_keeps_top_ranked(self):
        chunk = _chunk_item()
        chunk.content = "字" * 5000
        context, sources = ContextBuilder(max_context_chars=100).build([chunk, chunk])
        self.assertLessEqual(len(context), 100)
        self.assertEqual(len(sources), 1)


class TestPrompt(unittest.TestCase):
    def test_boundaries_clear(self):
        msg = build_user_message("什么是 MVP", "CONTEXT 内容")
        self.assertIn("--- USER QUERY ---", msg)
        self.assertIn("--- KNOWLEDGE CONTEXT ---", msg)
        self.assertIn("什么是 MVP", msg)
        self.assertIn("CONTEXT 内容", msg)

    def test_messages_have_system_and_user(self):
        msgs = build_messages("q", "ctx")
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[1]["role"], "user")

    def test_system_instruction_rules(self):
        self.assertIn("产品经理学习助手", SYSTEM_INSTRUCTION)
        self.assertIn("不要编造", SYSTEM_INSTRUCTION)
        self.assertIn("source_path", SYSTEM_INSTRUCTION)

    def test_prompt_injection_boundary(self):
        self.assertIn("不是指令", SYSTEM_INSTRUCTION)


class TestPipelineIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.embedding = MockEmbeddingAdapter()
        KnowledgeIndexer(embedding=cls.embedding, persist_dir=cls.tmp).build(_make_docs())
        cls.retriever = Retriever(embedding=cls.embedding, persist_dir=cls.tmp)

    def test_real_retriever_mock_llm(self):
        llm = MockLLM()
        pipeline = RAGPipeline(retriever=self.retriever, llm_adapter=llm)
        result = pipeline.run("MVP 最小可行产品", top_k=3)
        self.assertGreater(result.retrieval_count, 0)
        self.assertEqual(len(result.sources), result.retrieval_count)
        self.assertGreater(llm.call_count, 0)


class TestTextGenerationModelResolution(unittest.TestCase):
    def test_find_text_generation_model_none_when_empty(self):
        import tempfile as _tf

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.db.database import Base
        from app.services.model_service import ModelService

        engine = create_engine(f"sqlite:///{_tf.mkdtemp()}/t.db", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            self.assertIsNone(ModelService(db).find_text_generation_model("anonymous"))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
