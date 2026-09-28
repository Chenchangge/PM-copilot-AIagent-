"""RAG 检索开发测试 CLI（仅供开发验证，非公开 API）。

用法（在 backend/ 目录下）：
    python -m app.scripts.test_retrieval "用户需求分析" --mock
    python -m app.scripts.test_retrieval "用户需求分析" --mock --top-k 3

绝不输出 API Key。
"""
import argparse

from app.db.database import SessionLocal, init_db
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.retriever import Retriever
from app.services.model_service import ModelService
from app.services.providers import get_embedding_adapter
from app.services.providers.embedding import MockEmbeddingAdapter
from app.services.secret_storage import secret_storage

DEFAULT_USER_ID = "anonymous"


def resolve_embedding(use_mock: bool):
    if use_mock:
        return MockEmbeddingAdapter()
    init_db()
    db = SessionLocal()
    try:
        cfg = ModelService(db).find_embedding_model(DEFAULT_USER_ID)
    finally:
        db.close()
    if cfg is None:
        raise RAGError(
            RAGErrorCode.embedding_model_not_found,
            "未找到可用 Embedding Model（需 capabilities.embedding == supported）。",
        )
    key = secret_storage.unseal(cfg.api_key_secret)
    return get_embedding_adapter(cfg.provider, cfg.base_url or "", key, cfg.model)


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG 检索开发测试")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--mock", action="store_true", help="使用 Mock Embedding（测试）")
    args = parser.parse_args()

    try:
        embedding = resolve_embedding(args.mock)
        retriever = Retriever(embedding=embedding)
        result = retriever.retrieve(args.query, top_k=args.top_k)
    except RAGError as e:
        print(f"错误 [{e.code.value}]：{e.message}")
        return 1
    except Exception as e:  # 不打印原始异常，避免潜在 Key 泄露
        print(f"错误：{type(e).__name__}")
        return 1

    print(f"Query: {result.query}")
    print(f"Results: {len(result.results)}")
    for i, it in enumerate(result.results, 1):
        print(f"[{i}] {it.knowledge_id} | {it.title} | {it.section}")
        print(f"    distance={it.distance}  score={it.score}")
        print(f"    source={it.source_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
