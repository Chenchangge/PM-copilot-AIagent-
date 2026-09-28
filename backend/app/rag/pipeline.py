"""RAG Pipeline：Query → Retriever → Context Builder → Prompt → LLM → RAGResult。

不依赖具体 LLM Provider：LLM 通过 BaseModelAdapter 注入（复用 Step 6 BYOK 架构）。
Sources 由 Retriever / Backend 维护，不由 LLM 自己生成。
"""
from app.core.errors import AIErrorCode
from app.rag.context_builder import ContextBuilder
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.prompt import build_messages
from app.rag.retriever import MAX_QUERY_LENGTH, Retriever
from app.rag.schemas import RAGResult

NO_CONTEXT_ANSWER = "当前知识库中没有找到足够相关的信息，暂时无法基于知识库回答该问题。"


class RAGPipeline:
    def __init__(self, retriever: Retriever, llm_adapter, context_builder: ContextBuilder | None = None) -> None:
        self.retriever = retriever
        self.llm_adapter = llm_adapter
        self.context_builder = context_builder or ContextBuilder()

    def run(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float | None = None,
        max_distance: float | None = None,
    ) -> RAGResult:
        query = self._validate_query(query)
        retrieval = self.retriever.retrieve(
            query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            max_distance=max_distance,
        )

        # 没有足够相关知识：不调用 LLM（不浪费 API，不伪装成 RAG）
        if not retrieval.results:
            return RAGResult(
                query=query,
                answer=NO_CONTEXT_ANSWER,
                sources=[],
                retrieval_count=0,
                provider=self.llm_adapter.provider,
                model=self.llm_adapter.model,
                usage=None,
            )

        context, sources = self.context_builder.build(retrieval.results)
        messages = build_messages(query, context)
        answer, usage = self._generate(messages)

        return RAGResult(
            query=query,
            answer=answer,
            sources=sources,
            retrieval_count=len(sources),
            provider=self.llm_adapter.provider,
            model=self.llm_adapter.model,
            usage=usage,
        )

    def _validate_query(self, query) -> str:
        if not isinstance(query, str):
            raise RAGError(RAGErrorCode.retrieval_invalid_query, "query 必须是字符串")
        query = query.strip()
        if not query:
            raise RAGError(RAGErrorCode.retrieval_invalid_query, "query 不能为空")
        if len(query) > MAX_QUERY_LENGTH:
            raise RAGError(RAGErrorCode.retrieval_invalid_query, f"query 超过最大长度 {MAX_QUERY_LENGTH}")
        return query

    def _generate(self, messages: list[dict]) -> tuple[str, dict | None]:
        try:
            result = self.llm_adapter.generate(messages)
        except Exception as exc:
            code_str, message = self.llm_adapter.classify_error(exc)
            raise RAGError(AIErrorCode(code_str), message) from exc
        return result.get("content") or "", result.get("usage")


def build_rag_pipeline(user_id: str = "anonymous") -> "RAGPipeline":
    """根据 user_id 解析 Embedding（Retriever）+ LLM Adapter，构造 RAGPipeline。

    无 Embedding 模型 → EMBEDDING_MODEL_NOT_FOUND；无文本生成模型 → LLM_MODEL_NOT_FOUND。
    不自动 fallback 到 Mock。
    """
    from app.db.database import SessionLocal
    from app.services.model_service import ModelService
    from app.services.providers import get_adapter, get_embedding_adapter
    from app.services.secret_storage import secret_storage

    db = SessionLocal()
    try:
        service = ModelService(db)
        embedding_model = service.find_embedding_model(user_id)
        if embedding_model is None:
            raise RAGError(RAGErrorCode.embedding_model_not_found, "知识问答功能需要先配置一个支持知识检索的模型。")
        llm_model = service.find_text_generation_model(user_id)
        if llm_model is None:
            raise RAGError(RAGErrorCode.llm_model_not_found, "知识问答功能需要先配置一个支持文本生成的模型。")

        embedding = get_embedding_adapter(
            embedding_model.provider,
            embedding_model.base_url or "",
            secret_storage.unseal(embedding_model.api_key_secret),
            embedding_model.model,
        )
        llm = get_adapter(
            llm_model.provider,
            llm_model.base_url or "",
            secret_storage.unseal(llm_model.api_key_secret),
            llm_model.model,
        )
    finally:
        db.close()

    return RAGPipeline(retriever=Retriever(embedding=embedding), llm_adapter=llm)
