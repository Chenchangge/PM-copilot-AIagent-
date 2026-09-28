"""索引元数据：knowledge hash、embedding model、chunking 版本等。"""
import hashlib
import json
from pathlib import Path

from app.core.config import PROJECT_ROOT

KNOWLEDGE_INDEX_PATH = PROJECT_ROOT / "knowledge" / "index" / "index.json"


def compute_knowledge_hash(documents) -> str:
    """对所有 Markdown 的 path + content 求哈希，用于检测内容变化。"""
    h = hashlib.sha256()
    for doc in sorted(documents, key=lambda d: d.source_path):
        h.update(doc.source_path.encode("utf-8"))
        h.update(b"\x00")
        h.update(doc.content.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def read_knowledge_version() -> str:
    try:
        data = json.loads(KNOWLEDGE_INDEX_PATH.read_text(encoding="utf-8"))
        return str(data.get("version", "unknown"))
    except (OSError, json.JSONDecodeError):
        return "unknown"


class IndexMeta:
    def __init__(self, meta_path: Path | str) -> None:
        self.meta_path = Path(meta_path)

    def load(self) -> dict:
        if self.meta_path.exists():
            try:
                return json.loads(self.meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {}
        return {}

    def save(self, meta: dict) -> None:
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
