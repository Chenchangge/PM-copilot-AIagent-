"""RAG Retriever：Query → Query Embedding → Chroma → Top-K → 结果。

只负责「检索」，不负责 LLM / Prompt / Chat / 对话历史 / 前端 UI。
Query Embedding 复用 Step 7-1 的 Embedding Adapter，并与 Index 的 embedding model 保持一致。
"""
from dataclasses import dataclass, field
from pathlib import Path

import chromadb

from app.core.config import settings
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.index_meta import IndexMeta
from app.services.providers.embedding import BaseEmbeddingAdapter

MAX_QUERY_LENGTH = 2000
DEFAULT_TOP_K = 5
MAX_TOP_K = 20


@dataclass
class RetrieverItem:
    chunk_id: str
    knowledge_id: str
    title: str
    category: str
    tags: list[str] = field(default_factory=list)
    difficulty: str = ""
    section: str = ""
    content: str = ""
    source_path: str = ""
    distance: float | None = None
    score: float | None = None


@dataclass
class RetrieverResult:
    query: str
    results: list[RetrieverItem] = field(default_factory=list)


class Retriever:
    def __init__(
        self,
        embedding: BaseEmbeddingAdapter,
        persist_dir: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        self.embedding = embedding
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._meta = IndexMeta(Path(self.persist_dir) / "index_meta.json")

    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        similarity_threshold: float | None = None,
        max_distance: float | None = None,
    ) -> RetrieverResult:
        query = self._validate_query(query)
        top_k = self._validate_top_k(top_k)
        self._ensure_index()
        self._check_model_consistency()
        query_vector = self._embed_query(query)
        self._check_dimension_consistency(len(query_vector))

        collection = self._client.get_collection(self.collection_name)
        raw = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        items = self._build_items(raw, collection.metadata, similarity_threshold, max_distance)
        return RetrieverResult(query=query, results=items)

    # ---- 校验 ----
    def _validate_query(self, query) -> str:
        if not isinstance(query, str):
            raise RAGError(RAGErrorCode.retrieval_invalid_query, "query 必须是字符串")
        query = query.strip()
        if not query:
            raise RAGError(RAGErrorCode.retrieval_invalid_query, "query 不能为空")
        if len(query) > MAX_QUERY_LENGTH:
            raise RAGError(RAGErrorCode.retrieval_invalid_query, f"query 超过最大长度 {MAX_QUERY_LENGTH}")
        return query

    def _validate_top_k(self, top_k) -> int:
        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise RAGError(RAGErrorCode.retrieval_invalid_top_k, "top_k 必须是整数")
        if top_k < 1 or top_k > MAX_TOP_K:
            raise RAGError(RAGErrorCode.retrieval_invalid_top_k, f"top_k 必须在 1～{MAX_TOP_K} 之间")
        return top_k

    # ---- 前置检查 ----
    def _ensure_index(self) -> None:
        try:
            self._client.get_collection(self.collection_name)
        except Exception as exc:
            raise RAGError(RAGErrorCode.index_not_found, "知识库索引不存在，请先构建索引。") from exc

    def _check_model_consistency(self) -> None:
        meta = self._meta.load()
        if not meta or not meta.get("embedding_model"):
            raise RAGError(RAGErrorCode.index_not_found, "索引元数据缺失，请重新构建索引。")
        index_provider = meta.get("embedding_provider")
        index_model = meta.get("embedding_model")
        if index_provider != self.embedding.provider or index_model != self.embedding.model:
            raise RAGError(
                RAGErrorCode.index_model_mismatch,
                f"Embedding 模型不一致：索引使用 {index_provider}/{index_model}，"
                f"查询使用 {self.embedding.provider}/{self.embedding.model}。",
            )

    def _check_dimension_consistency(self, query_dimension: int) -> None:
        meta = self._meta.load()
        index_dimension = meta.get("dimension")
        if index_dimension and index_dimension != query_dimension:
            raise RAGError(
                RAGErrorCode.index_model_mismatch,
                f"向量维度不一致：索引为 {index_dimension} 维，查询为 {query_dimension} 维，请重新构建索引。",
            )

    def _embed_query(self, query: str):
        try:
            vecs = self.embedding.embed([query])
        except Exception as exc:
            raise RAGError(RAGErrorCode.retrieval_provider_error, "Query Embedding 失败") from exc
        if not vecs:
            raise RAGError(RAGErrorCode.retrieval_provider_error, "Query Embedding 返回为空")
        return vecs[0]

    # ---- 结果组装 ----
    def _build_items(self, raw: dict, collection_metadata: dict, similarity_threshold, max_distance):
        ids = (raw.get("ids") or [[]])[0]
        documents = (raw.get("documents") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        space = (collection_metadata or {}).get("hnsw:space", "l2")

        items = []
        for i, chunk_id in enumerate(ids):
            meta = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            items.append(
                RetrieverItem(
                    chunk_id=chunk_id,
                    knowledge_id=meta.get("document_id") or meta.get("knowledge_id") or "",
                    title=meta.get("title") or "",
                    category=meta.get("category") or "",
                    tags=[t for t in (meta.get("tags") or "").split(",") if t],
                    difficulty=meta.get("difficulty") or "",
                    section=meta.get("section") or "",
                    content=documents[i] if i < len(documents) else "",
                    source_path=meta.get("source_path") or "",
                    distance=distance,
                    score=self._to_score(distance, space),
                )
            )
        return self._apply_threshold(items, similarity_threshold, max_distance)

    def _to_score(self, distance, space: str) -> float | None:
        if distance is None:
            return None
        if space == "cosine":
            return round(1.0 - distance, 6)  # cosine similarity = 1 - cosine distance
        return None  # 非 cosine 无法保证语义，明确返回 null

    def _apply_threshold(self, items, similarity_threshold, max_distance):
        result = items
        if similarity_threshold is not None:
            result = [it for it in result if it.score is not None and it.score >= similarity_threshold]
        if max_distance is not None:
            result = [it for it in result if it.distance is not None and it.distance <= max_distance]
        return result
