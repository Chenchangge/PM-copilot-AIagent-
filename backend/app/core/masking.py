"""API Key 脱敏工具。

对外（API 响应、日志）一律只暴露脱敏后的 Key，绝不返回明文。
"""

_MASK_PREFIX = "•" * 12


def mask_secret(secret: str | None, visible: int = 4) -> str:
    """返回固定前缀 + 末尾若干位的脱敏形式，如 '••••••••••••abcd'。"""
    if not secret:
        return ""
    if len(secret) <= visible:
        return "•" * len(secret)
    return _MASK_PREFIX + secret[-visible:]
