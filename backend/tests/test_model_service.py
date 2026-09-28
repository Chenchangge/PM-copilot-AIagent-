"""ModelService 能力推导 / 连接测试路由 测试（内存 SQLite + mock adapter，不调用真实 API）。"""
import tempfile
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.schemas.model import ModelConfigCreate
from app.services.model_service import ModelService


def _make_service():
    tmp = tempfile.mkdtemp()
    engine = create_engine(f"sqlite:///{tmp}/t.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    return db, ModelService(db)


def _create(service, user_id, provider, model, model_type=None):
    data = ModelConfigCreate(
        name="m", provider=provider, model=model, base_url=None, api_key="sk-test", model_type=model_type
    )
    return service.create_model(user_id, data)


class TestCustomModelCapability(unittest.TestCase):
    def test_custom_embedding_type_explicit(self):
        db, svc = _make_service()
        try:
            # bge-m3 名字不含 "embedding"，靠 model_type 显式声明
            out = _create(svc, "u1", "custom", "bge-m3", model_type="embedding")
            self.assertEqual(out.capabilities["embedding"], "supported")
        finally:
            db.close()

    def test_custom_text_generation_type_explicit(self):
        db, svc = _make_service()
        try:
            out = _create(svc, "u1", "custom", "my-company-llm", model_type="text_generation")
            self.assertEqual(out.capabilities["text_generation"], "supported")
        finally:
            db.close()

    def test_custom_no_type_stays_unknown(self):
        db, svc = _make_service()
        try:
            out = _create(svc, "u1", "custom", "bge-m3")
            self.assertEqual(out.capabilities["embedding"], "unknown")
        finally:
            db.close()

    def test_custom_embedding_name_auto_detected(self):
        db, svc = _make_service()
        try:
            out = _create(svc, "u1", "custom", "text-embedding-v3")
            self.assertEqual(out.capabilities["embedding"], "supported")
        finally:
            db.close()

    def test_official_provider_ignores_model_type(self):
        db, svc = _make_service()
        try:
            # deepseek 无 Embedding，model_type=embedding 不应被强制标为 supported
            out = _create(svc, "u1", "deepseek", "deepseek-flash", model_type="embedding")
            self.assertEqual(out.capabilities["embedding"], "unknown")
        finally:
            db.close()


class TestConnectionRouting(unittest.TestCase):
    def test_embedding_model_uses_embedding_adapter(self):
        db, svc = _make_service()
        try:
            out = _create(svc, "u1", "custom", "bge-m3", model_type="embedding")

            class FakeEmb:
                def test_connection(self):
                    return {"success": True, "model": "bge-m3", "latency_ms": 5, "error_code": None, "message": None}

            with patch("app.services.model_service.get_embedding_adapter", return_value=FakeEmb()) as m_emb, patch(
                "app.services.model_service.get_adapter"
            ) as m_text:
                result = svc.test_connection("u1", out.id)
            m_emb.assert_called_once()
            m_text.assert_not_called()
            self.assertTrue(result.success)
        finally:
            db.close()

    def test_text_model_uses_text_adapter(self):
        db, svc = _make_service()
        try:
            out = _create(svc, "u1", "deepseek", "deepseek-flash")

            class FakeText:
                def test_connection(self):
                    return {"success": True, "model": "deepseek-flash", "latency_ms": 5, "error_code": None, "message": None}

            with patch("app.services.model_service.get_adapter", return_value=FakeText()) as m_text, patch(
                "app.services.model_service.get_embedding_adapter"
            ) as m_emb:
                result = svc.test_connection("u1", out.id)
            m_text.assert_called_once()
            m_emb.assert_not_called()
            self.assertTrue(result.success)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
