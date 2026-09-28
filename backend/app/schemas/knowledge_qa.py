"""知识库 AI 问答 API 的请求 / 响应 Schema。

- Request（KnowledgeQARequest）：字段类型校验交给 Pydantic；语义校验
  （trim / 长度 / top_k 范围 / threshold 范围 / 冲突）在 Route 层完成，
  以便抛 RAGError 并映射为统一错误码 + HTTP 状态。
- Response（KnowledgeQAResponse）：与 RAGResult 字段一一对应，只做序列化，
  不重新设计数据模型。
"""
from pydantic import BaseModel

from app.rag.schemas import RAGResult


class KnowledgeQARequest(BaseModel):
    query: str
    top_k: int = 5
    similarity_threshold: float | None = None
    max_distance: float | None = None


class KnowledgeQASource(BaseModel):
    knowledge_id: str
    chunk_id: str
    title: str
    category: str = ""
    section: str = ""
    source_path: str = ""
    score: float | None = None


class KnowledgeQAResponse(BaseModel):
    query: str
    answer: str
    sources: list[KnowledgeQASource] = []
    retrieval_count: int = 0
    provider: str | None = None
    model: str | None = None
    usage: dict | None = None


def to_qa_response(result: RAGResult) -> KnowledgeQAResponse:
    """RAGResult（dataclass）→ API 响应模型。Source 来自 Backend，此处仅搬运字段。"""
    return KnowledgeQAResponse(
        query=result.query,
        answer=result.answer,
        sources=[
            KnowledgeQASource(
                knowledge_id=s.knowledge_id,
                chunk_id=s.chunk_id,
                title=s.title,
                category=s.category,
                section=s.section,
                source_path=s.source_path,
                score=s.score,
            )
            for s in result.sources
        ],
        retrieval_count=result.retrieval_count,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
    )
