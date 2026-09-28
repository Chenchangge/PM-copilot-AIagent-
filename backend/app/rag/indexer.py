"""知识库索引构建器：Documents → Chunks → Embeddings → Chroma。

- build：幂等 upsert（按 chunk_id）。
- rebuild：清空 collection 后重建。
- 检测 Embedding Model 变化：变化时要求 rebuild。
"""
from datetime import datetime, timezone
from pathlib import Path

import chromadb

from app.core.config import settings
from app.rag.chunker import KnowledgeChunker
from app.rag.document import KnowledgeDocument
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.index_meta import IndexMeta, compute_knowledge_hash, read_knowledge_version
from app.services.providers.embedding import BaseEmbeddingAdapter


class KnowledgeIndexer:
    def __init__(
        self,
        embedding: BaseEmbeddingAdapter,
        persist_dir: str | None = None,
        collection_name: str | None = None,
        chunker: KnowledgeChunker | None = None,
    ) -> None:
        self.embedding = embedding
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection
        self.chunker = chunker or KnowledgeChunker()
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._meta = IndexMeta(Path(self.persist_dir) / "index_meta.json")

    def build(self, documents: list[KnowledgeDocument]) -> dict:
        self._check_model_mismatch()
        return self._write(documents)

    def rebuild(self, documents: list[KnowledgeDocument]) -> dict:
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:
            pass
        return self._write(documents)

    def count(self) -> int:
        try:
            return self._client.get_collection(self.collection_name).count()
        except Exception:
            return 0

    def _write(self, documents: list[KnowledgeDocument]) -> dict:
        chunks = self._to_chunks(documents)
        embeddings = self._embed([c.content for c in chunks])
        collection = self._client.get_or_create_collection(
            self.collection_name,
            metadata={"hnsw:space": "cosine"},  # 使用 cosine 距离，便于语义相似度
        )
        collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.content for c in chunks],
            metadatas=[c.metadata for c in chunks],
        )
        dimension = len(embeddings[0]) if embeddings else 0
        self._save_meta(documents, chunks, dimension)
        return self._stats(documents, chunks)

    def _to_chunks(self, documents: list[KnowledgeDocument]):
        chunks = []
        for doc in documents:
            chunks.extend(self.chunker.chunk(doc))
        return chunks

    def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            return self.embedding.embed(texts)
        except Exception as exc:  # 不向调用方泄漏底层异常 / Secret
            raise RAGError(RAGErrorCode.embedding_provider_error, "Embedding 调用失败") from exc

    def _check_model_mismatch(self) -> None:
        meta = self._meta.load()
        if meta and meta.get("embedding_model") and meta["embedding_model"] != self.embedding.model:
            raise RAGError(
                RAGErrorCode.index_model_mismatch,
                "Embedding 模型已变化，请重新构建知识库索引（--rebuild）。",
            )

    def _save_meta(self, documents: list[KnowledgeDocument], chunks, dimension: int) -> None:
        self._meta.save(
            {
                "knowledge_hash": compute_knowledge_hash(documents),
                "knowledge_version": read_knowledge_version(),
                "embedding_provider": self.embedding.provider,
                "embedding_model": self.embedding.model,
                "dimension": dimension,
                "chunking_version": "1",
                "chunk_size": self.chunker.chunk_size,
                "chunk_overlap": self.chunker.chunk_overlap,
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                "document_count": len(documents),
                "chunk_count": len(chunks),
            }
        )

    def _stats(self, documents: list[KnowledgeDocument], chunks) -> dict:
        lengths = [len(c.content) for c in chunks]
        return {
            "document_count": len(documents),
            "chunk_count": len(chunks),
            "embedding_count": len(chunks),
            "collection": self.collection_name,
            "avg_chunk_length": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            "min_chunk_length": min(lengths) if lengths else 0,
            "max_chunk_length": max(lengths) if lengths else 0,
        }
