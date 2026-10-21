"""Context Builder：把检索到的 chunks 组装成 LLM Context，并维护 source 列表。"""
from app.rag.retriever import RetrieverItem
from app.rag.schemas import Source

DEFAULT_MAX_CONTEXT_CHARS = 10000


class ContextBuilder:
    def __init__(self, max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS) -> None:
        self.max_context_chars = max_context_chars

    def build(self, chunks: list[RetrieverItem]) -> tuple[str, list[Source]]:
        """返回 (context 文本, sources)。超长时优先保留排名靠前的结果，不无限拼接。

        sources 按 knowledge_id 聚合：同一篇文章只保留 score 最高的一段，
        并记录 extra_chunks（该文另有 N 段相关）。context 仍保留全部段落供 LLM 使用。
        """
        parts: list[str] = []
        raw_sources: list[Source] = []
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
            raw_sources.append(
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
        return "\n\n".join(parts), self._aggregate_sources(raw_sources)

    @staticmethod
    def _aggregate_sources(sources: list[Source]) -> list[Source]:
        order: list[str] = []
        best: dict[str, Source] = {}
        counts: dict[str, int] = {}
        for source in sources:
            key = source.knowledge_id or source.chunk_id
            if key not in best:
                order.append(key)
                best[key] = source
                counts[key] = 0
            counts[key] += 1
            old_score = best[key].score if best[key].score is not None else -1.0
            new_score = source.score if source.score is not None else -1.0
            if new_score > old_score:
                best[key] = source
        aggregated: list[Source] = []
        for key in order:
            source = best[key]
            source.extra_chunks = max(0, counts[key] - 1)
            aggregated.append(source)
        return aggregated

    def _format_chunk(self, chunk: RetrieverItem) -> str:
        # 不把 knowledge/data/... 内部路径交给 LLM；引用统一用「参考知识库中《标题》」。
        return (
            f"[知识] {chunk.title}\n"
            f"分类：{chunk.category}\n"
            f"章节：{chunk.section}\n"
            f"引用写法：参考知识库中《{chunk.title}》\n"
            f"内容：\n{chunk.content}"
        )
