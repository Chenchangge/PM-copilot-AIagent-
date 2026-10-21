"""Pytest 全局数据库隔离。

必须在任何 `app.*` 模块导入之前执行：engine 在 `app.db.database` 导入时创建并缓存，
如果某条测试先以默认配置导入，后续测试的 DATABASE_URL 就不再生效，tearDown 里的
`Base.metadata.drop_all()` 会直接清空真实 `backend/pm_copilot.db`。

历史问题：test_model_service / test_embedding 等模块先导入 app，随后 test_api 的
drop_all 把开发库清空。这里让整个 pytest 会话固定使用临时 SQLite。
"""
import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="pm_copilot_pytest_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/pm_copilot_test.db"
os.environ["ENVIRONMENT"] = "test"
