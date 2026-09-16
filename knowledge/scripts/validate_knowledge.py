#!/usr/bin/env python3
"""知识库 Markdown 校验脚本。

只负责「Markdown 文件扫描 → 元数据与结构校验」，不涉及 Embedding / 向量库 / RAG。

校验项：
- Front Matter 存在且含必填字段 id / title / category / difficulty / tags
- id 唯一且为英文 kebab-case
- category / difficulty 枚举合法
- 正文 H1 标题与 front matter title 一致
- 正文含六个必要章节
- 面试问题数与参考答案数匹配（警告级）

用法：python knowledge/scripts/validate_knowledge.py
"""
import re
import sys
from pathlib import Path

# Windows 控制台默认 GBK 编码，无法输出 ✓ 等字符；统一转 UTF-8，避免 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]  # knowledge/
DATA_DIR = ROOT / "data"

CATEGORIES = {"product", "design", "data", "ai", "tools", "interview"}
DIFFICULTIES = {"beginner", "intermediate", "advanced"}
REQUIRED_SECTIONS = [
    "## 定义",
    "## 核心内容",
    "## 常见场景",
    "## 产品经理关注点",
    "## 面试问题",
    "## 参考答案",
]
KABAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_front_matter(text: str):
    """极简 Front Matter 解析（无需 PyYAML）。返回 dict 或 None。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None

    meta = {}
    tags = []
    in_tags = False
    for line in lines[1:end]:
        if line.startswith("tags:"):
            in_tags = True
            continue
        if in_tags:
            m = re.match(r"\s*-\s+(.+)$", line)
            if m:
                tags.append(m.group(1).strip())
                continue
            in_tags = False
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    if tags:
        meta["tags"] = tags
    return meta


def main():
    errors = []
    warnings = []
    ids = {}
    files = sorted(DATA_DIR.glob("*/*.md"))
    if not files:
        print("未找到知识库文件（data/*/*.md）")
        return 1

    for f in files:
        rel = str(f.relative_to(ROOT))
        text = f.read_text(encoding="utf-8")
        meta = parse_front_matter(text)
        if meta is None:
            errors.append(f"{rel}: Front Matter 缺失或格式错误")
            continue

        for key in ["id", "title", "category", "difficulty", "tags"]:
            if not meta.get(key):
                errors.append(f"{rel}: 缺少字段 {key}")

        kid = meta.get("id", "")
        if not KABAB_RE.match(kid):
            errors.append(f"{rel}: id 非法（需英文 kebab-case）：{kid!r}")
        if kid in ids:
            errors.append(f"{rel}: id 重复（已见于 {ids[kid]}）")
        ids[kid] = rel

        if meta.get("category") not in CATEGORIES:
            errors.append(f"{rel}: category 非法：{meta.get('category')!r}")
        if meta.get("difficulty") not in DIFFICULTIES:
            errors.append(f"{rel}: difficulty 非法：{meta.get('difficulty')!r}")

        title = meta.get("title", "")
        if not re.search(rf"^#\s+{re.escape(title)}\s*$", text, re.MULTILINE):
            errors.append(f"{rel}: H1 标题与 front matter title 不一致（title={title!r}）")

        for sec in REQUIRED_SECTIONS:
            if sec not in text:
                errors.append(f"{rel}: 缺少章节 {sec}")

        nq = len(re.findall(r"^###\s+\d+\.\s", text, re.MULTILINE))
        na = len(re.findall(r"^###\s+问题\s*\d+", text, re.MULTILINE))
        if nq != na:
            warnings.append(f"{rel}: 面试问题数({nq})与参考答案数({na})不一致")

    print(f"扫描文件数：{len(files)}")
    print(f"唯一 id 数：{len(ids)}")
    if warnings:
        print("\n[警告]")
        for w in warnings:
            print("  -", w)
    if errors:
        print(f"\n[错误] 共 {len(errors)} 条：")
        for e in errors:
            print("  -", e)
        return 1
    print("\n✓ 校验通过：所有知识点格式、字段、枚举与 id 唯一性均正常")
    return 0


if __name__ == "__main__":
    sys.exit(main())
