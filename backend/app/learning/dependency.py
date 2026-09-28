"""知识点依赖关系校验与拓扑排序（§11）。

- dependencies = 硬前置（AND，有方向）。Learning Plan 生成时优先处理。
- 检测 A → B → C（合法链）与 A → B → A（循环，必须拒绝）。
- related/similar/supersedes/deprecated_by 不影响排课（在 taxonomy 模型中另存）。
"""
from __future__ import annotations

from collections import deque

from app.learning.constants import DIFFICULTY_RANK
from app.learning.errors import LearningError, LearningErrorCode
from app.learning.knowledge_index import KnowledgePointView


def build_dependency_graph(points: list[KnowledgePointView]) -> dict[str, list[str]]:
    """id → [前置 id]（仅保留目标范围内的依赖；范围外依赖作为 prerequisite 展示）。"""
    ids = {p.id for p in points}
    graph: dict[str, list[str]] = {}
    for p in points:
        deps = [d for d in p.dependencies if d in ids and d != p.id]
        graph[p.id] = deps
    return graph


def topological_levels(graph: dict[str, list[str]]) -> dict[str, int]:
    """Kahn 拓扑排序，返回每个节点的深度 level（前置在前）。

    存在循环时抛 LearningError(learning_dependency_cycle)。
    """
    indegree = {n: 0 for n in graph}
    dependents: dict[str, list[str]] = {n: [] for n in graph}
    for n, deps in graph.items():
        indegree[n] += len(deps)
        for d in deps:
            dependents[d].append(n)

    level = {n: 0 for n in graph}
    q = deque([n for n in graph if indegree[n] == 0])
    processed = 0
    while q:
        n = q.popleft()
        processed += 1
        for m in dependents[n]:
            indegree[m] -= 1
            level[m] = max(level[m], level[n] + 1)
            if indegree[m] == 0:
                q.append(m)

    if processed != len(graph):
        raise LearningError(
            LearningErrorCode.learning_dependency_cycle,
            "知识点依赖存在循环，无法生成学习计划",
        )
    return level


def has_cycle(points: list[KnowledgePointView]) -> bool:
    """依赖图中是否存在循环（供校验/测试使用）。"""
    try:
        topological_levels(build_dependency_graph(points))
        return False
    except LearningError as exc:
        if exc.code == LearningErrorCode.learning_dependency_cycle:
            return True
        raise


def order_points(points: list[KnowledgePointView]) -> list[KnowledgePointView]:
    """确定性排序：前置优先（拓扑 level），同一 level 内按 difficulty（易→难）、
    topic（相邻聚集）排序。"""
    graph = build_dependency_graph(points)
    levels = topological_levels(graph)

    def key(p: KnowledgePointView):
        return (
            levels.get(p.id, 0),
            DIFFICULTY_RANK.get(p.difficulty, 1),
            p.topic or p.category,
            p.title,
        )

    return sorted(points, key=key)
