"""API Key 服务端存储抽象。

当前为「明文透传」占位实现，仅保证：
- 密钥不出现在 API 响应（由 masking 层处理）
- 密钥不写入日志
- 密钥不进入前端代码

TODO(Secret Storage): 接入真实加密。未来使用 SECRET_ENCRYPTION_KEY 对
  api_key_secret 加密后再入库。本阶段不自行发明「看起来加密、实际不安全」的
  自定义方案，而是保留此抽象作为唯一读写入口，后续替换为成熟加密实现。
"""


class SecretStorage:
    """密钥存储接口。seal/unseal 目前为恒等（明文），后续替换为真实加密。"""

    def seal(self, secret: str) -> str:
        """加密/封装密钥，返回可安全存储的值。"""
        return secret

    def unseal(self, sealed: str) -> str:
        """解封密钥，仅供服务端调用。"""
        return sealed


secret_storage = SecretStorage()
