"""知识库分块器：按 Markdown section（## 标题）切分，过长再按长度切分。"""
import re

from app.rag.document import KnowledgeChunk, KnowledgeDocument

# 匹配 H2 章节标题（## 定义 / ## 核心内容 …），不匹配 H3（### 1. …）
SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


class KnowledgeChunker:
    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 80) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, doc: KnowledgeDocument) -> list[KnowledgeChunk]:
        sections = self._split_sections(doc.content)
        chunks: list[KnowledgeChunk] = []
        for sec_idx, (section_title, text) in enumerate(sections):
            text = text.strip()
            if not text:
                continue
            for chunk_idx, piece in enumerate(self._split_long(text)):
                content = self._with_context(doc.title, section_title, piece)
                chunk_id = f"{doc.id}:{sec_idx}:{chunk_idx}"
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=chunk_id,
                        document_id=doc.id,
                        content=content,
                        metadata={
                            "document_id": doc.id,
                            "title": doc.title,
                            "category": doc.category,
                            "tags": ",".join(doc.tags),
                            "difficulty": doc.difficulty,
                            "source_path": doc.source_path,
                            "chunk_id": chunk_id,
                            "section": section_title,
                        },
                    )
                )
        return chunks

    def _split_sections(self, content: str) -> list[tuple[str, str]]:
        matches = list(SECTION_RE.finditer(content))
        if not matches:
            return [("", content)]
        sections = []
        for i, m in enumerate(matches):
            title = m.group(1).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sections.append((title, content[start:end]))
        return sections

    def _split_long(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        pieces = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            pieces.append(text[start:end])
            if end >= len(text):
                break
            start = end - self.chunk_overlap
        return pieces

    def _with_context(self, title: str, section: str, text: str) -> str:
        parts = [title]
        if section:
            parts.append(section)
        parts.append(text)
        return "\n".join(parts)
