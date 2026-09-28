"""Markdown 知识库加载器。

扫描 knowledge/data/ 下所有 *.md，解析 front matter 与正文，转换为
KnowledgeDocument。Loader 只负责「读 + 标准化」，不涉及 Embedding / Vector DB / LLM。
"""
import re
from pathlib import Path

from app.core.config import PROJECT_ROOT
from app.rag.document import KnowledgeDocument
from app.rag.errors import RAGError, RAGErrorCode

KNOWLEDGE_DATA_DIR = PROJECT_ROOT / "knowledge" / "data"


def _parse_front_matter(text: str) -> dict:
    """极简 front matter 解析（无需 PyYAML）。

    支持标量 key: value 与列表（如 tags / dependencies 的 `- item`）。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}

    meta = {}
    list_key = None
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if val == "":
                meta[key] = []
                list_key = key
            else:
                meta[key] = val
                list_key = None
            continue
        item = re.match(r"^\s*-\s+(.+)$", line)
        if item and list_key is not None:
            meta[list_key].append(item.group(1).strip())
            continue
        list_key = None
    return meta


def _strip_front_matter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:])
    return text


def _strip_h1_title(body: str) -> str:
    """去掉正文开头的 H1 标题（title 已在 metadata，避免重复塞进 content）。"""
    lines = body.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            lines.pop(idx)
            break
    return "\n".join(lines).strip()


class MarkdownLoader:
    def __init__(self, data_dir: Path | str = KNOWLEDGE_DATA_DIR) -> None:
        self.data_dir = Path(data_dir)

    def load(self) -> list[KnowledgeDocument]:
        files = sorted(self.data_dir.glob("*/*.md"))
        if not files:
            raise RAGError(RAGErrorCode.knowledge_load_error, f"未找到知识库 Markdown：{self.data_dir}")
        docs: list[KnowledgeDocument] = []
        for f in files:
            docs.append(self._load_file(f))
        return docs

    def _load_file(self, path: Path) -> KnowledgeDocument:
        text = path.read_text(encoding="utf-8")
        meta = _parse_front_matter(text)
        doc_id = meta.get("id", "")
        if not doc_id:
            raise RAGError(RAGErrorCode.invalid_knowledge_metadata, f"{path.name}: 缺少 id")
        content = _strip_h1_title(_strip_front_matter(text))
        dependencies = meta.get("dependencies", [])
        if isinstance(dependencies, str):
            dependencies = [dependencies] if dependencies else []
        estimated_minutes = None
        if meta.get("estimated_minutes"):
            try:
                estimated_minutes = int(meta["estimated_minutes"])
            except ValueError:
                estimated_minutes = None
        return KnowledgeDocument(
            id=doc_id,
            title=meta.get("title", doc_id),
            category=meta.get("category", ""),
            tags=meta.get("tags", []),
            difficulty=meta.get("difficulty", ""),
            content=content,
            source_path=str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            topic=meta.get("topic", ""),
            dependencies=[d for d in dependencies if isinstance(d, str)],
            estimated_minutes=estimated_minutes,
        )
