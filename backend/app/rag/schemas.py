"""RAG Pipeline 的结构化结果与来源。"""
from dataclasses import dataclass, field


@dataclass
class Source:
    """检索到的知识来源（由 Retriever / Backend 维护，不由 LLM 生成）。"""

    knowledge_id: str
    chunk_id: str
    title: str
    category: str = ""
    section: str = ""
    source_path: str = ""
    score: float | None = None
    extra_chunks: int = 0  # 同一知识点还有多少段相关 chunk（来源按 knowledge_id 聚合）


@dataclass
class RAGResult:
    query: str
    answer: str
    sources: list[Source] = field(default_factory=list)
    retrieval_count: int = 0
    provider: str | None = None
    model: str | None = None
    usage: dict | None = None
    is_smalltalk: bool = False
