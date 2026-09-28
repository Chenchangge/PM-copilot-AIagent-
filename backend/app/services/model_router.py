"""Model Router：根据能力需求筛选模型。

仅做能力匹配；不做成本优化、fallback、多模型投票、负载均衡等复杂路由（后续规划）。
"""
from typing import Iterable

from app.core.capabilities import CapabilityState


class ModelRouter:
    """基础能力路由。"""

    def find_models_by_capabilities(self, models: Iterable, required_capabilities: list[str]) -> list:
        """返回「支持全部所需能力」的模型；required_capabilities 为空则原样返回。"""
        required = set(required_capabilities)
        if not required:
            return list(models)
        eligible = []
        for m in models:
            caps = m.capabilities or {}
            if all(caps.get(c) == CapabilityState.supported.value for c in required):
                eligible.append(m)
        return eligible


model_router = ModelRouter()
