"""Context Builder：把检索到的 chunks 组装成 LLM Context，并维护 source 列表。"""
from app.rag.retriever import RetrieverItem
from app.rag.schemas import Source

DEFAULT_MAX_CONTEXT_CHARS = 10000


class ContextBuilder:
    def __init__(self, max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS) -> None:
        self.max_context_chars = max_context_chars

    def build(self, chunks: list[RetrieverItem]) -> tuple[str, list[Source]]:
        """返回 (context 文本, sources)。超长时优先保留排名靠前的结果，不无限拼接。"""
        parts: list[str] = []
        sources: list[Source] = []
        total = 0
        for chunk in chunks:
            if total >= self.max_context_chars:
                break
            block = self._format_chunk(chunk)
            remaining = self.max_context_chars - total
            if len(block) > remaining:
                block = block[:remaining]
            parts.append(block)
            total += len(block)
            sources.append(
                Source(
                    knowledge_id=chunk.knowledge_id,
                    chunk_id=chunk.chunk_id,
                    title=chunk.title,
                    category=chunk.category,
                    section=chunk.section,
                    source_path=chunk.source_path,
                    score=chunk.score,
                )
            )
        return "\n\n".join(parts), sources

    def _format_chunk(self, chunk: RetrieverItem) -> str:
        return (
            f"[知识] {chunk.title}\n"
            f"分类：{chunk.category}\n"
            f"章节：{chunk.section}\n"
            f"来源：{chunk.source_path}\n"
            f"内容：\n{chunk.content}"
        )
