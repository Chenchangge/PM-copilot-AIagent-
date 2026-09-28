"""知识库索引构建 CLI。

用法（在 backend/ 目录下）：
    python -m app.scripts.build_knowledge_index              # 幂等增量 build
    python -m app.scripts.build_knowledge_index --rebuild    # 清空 collection 后重建
    python -m app.scripts.build_knowledge_index --mock       # 使用 Mock Embedding（仅测试）

绝不输出 API Key。
"""
import argparse
import time

from app.db.database import SessionLocal, init_db
from app.rag.chunker import KnowledgeChunker
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.indexer import KnowledgeIndexer
from app.rag.loader import MarkdownLoader
from app.services.model_service import ModelService
from app.services.providers import ProviderNotSupportedError, get_embedding_adapter
from app.services.providers.embedding import MockEmbeddingAdapter
from app.services.secret_storage import secret_storage

DEFAULT_USER_ID = "anonymous"


def resolve_embedding(use_mock: bool, user_id: str):
    if use_mock:
        return MockEmbeddingAdapter(), True
    init_db()
    db = SessionLocal()
    try:
        cfg = ModelService(db).find_embedding_model(user_id)
    finally:
        db.close()
    if cfg is None:
        raise RAGError(
            RAGErrorCode.embedding_model_not_found,
            "未找到可用 Embedding Model（需 capabilities.embedding == supported）。请先配置 Embedding 模型，或使用 --mock 进行测试。",
        )
    api_key = secret_storage.unseal(cfg.api_key_secret)
    if not api_key:
        raise RAGError(
            RAGErrorCode.embedding_api_key_missing,
            "Embedding 模型未配置 API Key。请在「AI 模型 / API」中为该模型填写 API Key 后重试。",
        )
    try:
        adapter = get_embedding_adapter(cfg.provider, cfg.base_url or "", api_key, cfg.model)
    except ProviderNotSupportedError:
        raise RAGError(
            RAGErrorCode.embedding_capability_unsupported,
            f"该 Provider（{cfg.provider}）暂未支持 Embedding。请改用 OpenAI 或 OpenAI 兼容的 Embedding 模型。",
        )
    return adapter, False


def main() -> int:
    parser = argparse.ArgumentParser(description="构建 PM Copilot 知识库向量索引")
    parser.add_argument("--rebuild", action="store_true", help="清空 collection 后重建")
    parser.add_argument("--mock", action="store_true", help="使用 Mock Embedding（仅测试）")
    parser.add_argument(
        "--user-id",
        default=DEFAULT_USER_ID,
        help="使用哪个用户配置的 Embedding 模型（前端匿名 ID 以 anon- 开头）。",
    )
    args = parser.parse_args()

    start = time.perf_counter()
    try:
        embedding, is_mock = resolve_embedding(args.mock, args.user_id)
        documents = MarkdownLoader().load()
        indexer = KnowledgeIndexer(embedding=embedding, chunker=KnowledgeChunker())
        if args.rebuild:
            stats = indexer.rebuild(documents)
        else:
            stats = indexer.build(documents)
    except RAGError as e:
        print(f"错误 [{e.code.value}]：{e.message}")
        return 1
    except Exception as e:  # 不打印原始异常，避免潜在 Key 泄露
        print(f"错误：{type(e).__name__}")
        return 1
    elapsed = time.perf_counter() - start

    print("== 知识库索引构建完成 ==")
    print(f"Embedding: {embedding.provider}/{embedding.model}{' (mock)' if is_mock else ''}")
    print(f"Documents: {stats['document_count']}")
    print(f"Chunks: {stats['chunk_count']}")
    print(f"Embeddings: {stats['embedding_count']}")
    print(f"Collection: {stats['collection']}")
    print(f"平均 chunk 长度: {stats['avg_chunk_length']}")
    print(f"最小 chunk 长度: {stats['min_chunk_length']}")
    print(f"最大 chunk 长度: {stats['max_chunk_length']}")
    print(f"耗时: {elapsed:.2f}s")
    print("失败: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
