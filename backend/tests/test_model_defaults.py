"""P1-1 默认模型 / 预检：服务器默认模型能让新用户直接问答与开始面试。"""
import os
import tempfile
import unittest
from unittest.mock import patch

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/defaults.db"
os.environ["ENVIRONMENT"] = "test"

from app.core.config import settings  # noqa: E402
from app.db.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.services.model_service import (  # noqa: E402
    ModelService,
    _server_default_models_for,
)


class TestServerDefaultModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_test_environment_disables_defaults(self):
        self.assertEqual(
            _server_default_models_for(["text_generation", "reasoning", "structured_output"]),
            [],
        )

    def test_resolve_uses_server_default_for_interview(self):
        with (
            patch.object(settings, "environment", "development"),
            patch.object(settings, "default_llm_provider", "deepseek"),
            patch.object(settings, "default_llm_base_url", "https://api.deepseek.com"),
            patch.object(settings, "default_llm_model", "deepseek-flash"),
            patch.object(settings, "default_llm_api_key", "sk-demo"),
        ):
            result = ModelService(self.db).resolve(
                "brand-new-user", ["text_generation", "reasoning", "structured_output"]
            )
        self.assertEqual(result.models, [])
        self.assertTrue(result.using_server_default)
        self.assertIn("deepseek-flash", result.server_default_models)
        self.assertIsNone(result.message)

    def test_resolve_qa_needs_two_default_models(self):
        with (
            patch.object(settings, "environment", "development"),
            patch.object(settings, "default_llm_provider", "deepseek"),
            patch.object(settings, "default_llm_model", "deepseek-flash"),
            patch.object(settings, "default_llm_api_key", "sk-demo"),
            patch.object(settings, "default_embedding_provider", "custom"),
            patch.object(settings, "default_embedding_base_url", "https://example.com/v1"),
            patch.object(settings, "default_embedding_model", "text-embedding-v4"),
            patch.object(settings, "default_embedding_api_key", "sk-embed"),
        ):
            result = ModelService(self.db).resolve(
                "brand-new-user", ["text_generation", "embedding"]
            )
        self.assertTrue(result.using_server_default)
        self.assertEqual(
            set(result.server_default_models), {"deepseek-flash", "text-embedding-v4"}
        )


if __name__ == "__main__":
    unittest.main()
