"""知识问答的小闲聊/问候识别。

这类输入不是知识问题，不应该走 Embedding 检索，更不应该回复「知识库没有找到」。
只匹配短问候/致谢/身份/用法问题，包含知识关键词的长问题不会被误判。
"""
from __future__ import annotations

import re

_GREETING = re.compile(
    r"^(你好|您好|嗨|哈喽|hi|hello|hey|在吗|早上好|上午好|下午好|晚上好)[\s!！。,.，?？~～]*$",
    re.IGNORECASE,
)
_THANKS = re.compile(r"^(谢谢|多谢|感谢|thanks|thank you|thx)[\s!！。,.，?？~～]*$", re.IGNORECASE)
_IDENTITY = re.compile(
    r"^(你是谁|你是什么|介绍一下你自己|你能做什么|你会什么|怎么用|如何使用)[\s!！。,.，?？~～]*$",
    re.IGNORECASE,
)

_GREETING_ANSWER = (
    "你好！我是 PM Copilot，可以帮你解释产品知识、做模拟面试、制定学习计划。"
    "你可以直接问我「什么是 MVP」「RAG 是什么」「如何做需求分析」这类问题。"
)
_THANKS_ANSWER = "不客气！如果还想继续了解产品知识，可以直接问我一个具体问题。"
_IDENTITY_ANSWER = (
    "我是 PM Copilot，一个面向产品经理的学习与模拟面试助手。"
    "我可以做三件事：解释知识库里的产品概念、陪你做多轮模拟面试、按目标生成学习计划。"
)


def smalltalk_answer(query: str) -> str | None:
    """命中问候/致谢/身份/用法时返回友好回答，否则返回 None。"""
    text = (query or "").strip()
    if not text or len(text) > 30:
        return None
    if _GREETING.fullmatch(text):
        return _GREETING_ANSWER
    if _THANKS.fullmatch(text):
        return _THANKS_ANSWER
    if _IDENTITY.fullmatch(text):
        return _IDENTITY_ANSWER
    return None
