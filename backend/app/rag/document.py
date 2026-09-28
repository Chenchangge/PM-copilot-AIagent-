"""知识库统一数据结构。"""
from dataclasses import dataclass, field


@dataclass
class KnowledgeDocument:
    """标准化知识点文档。metadata 与 content 分离，content 不含重复 metadata。"""

    id: str
    title: str
    category: str
    tags: list[str] = field(default_factory=list)
    difficulty: str = ""
    content: str = ""
    source_path: str = ""
    # 可选扩展字段（Learning Plan / 未来 ingestion 使用；当前 MVP 数据通常缺失）
    topic: str = ""
    dependencies: list[str] = field(default_factory=list)
    estimated_minutes: int | None = None


@dataclass
class KnowledgeChunk:
    """可独立理解的文本片段。"""

    chunk_id: str
    document_id: str
    content: str
    metadata: dict = field(default_factory=dict)
