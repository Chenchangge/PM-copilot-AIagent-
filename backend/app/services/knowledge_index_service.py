"""知识库索引重建（设置页「重建知识库索引」）。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.rag.errors import RAGError, RAGErrorCode
from app.rag.indexer import KnowledgeIndexer
from app.rag.loader import MarkdownLoader
from app.services.model_service import ModelService
from app.services.providers import get_embedding_adapter
from app.services.secret_storage import secret_storage


def rebuild_knowledge_index(db: Session, user_id: str) -> dict:
    model = ModelService(db).find_embedding_model(user_id)
    if model is None:
        raise RAGError(
            RAGErrorCode.embedding_model_not_found,
            "重建索引需要先配置一个支持 Embedding 的模型。",
        )
    embedding = get_embedding_adapter(
        model.provider,
        model.base_url or "",
        secret_storage.unseal(model.api_key_secret),
        model.model,
    )
    docs = MarkdownLoader().load()
    stats = KnowledgeIndexer(embedding=embedding).rebuild(docs)
    return {
        "documents": stats.get("document_count", len(docs)),
        "chunks": stats.get("chunk_count", 0),
        "embedding_count": stats.get("embedding_count", 0),
        "embedding_model": model.model,
    }
