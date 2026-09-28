"""Model Router 能力过滤的单元测试。"""
import unittest
from types import SimpleNamespace

from app.services.model_router import model_router


def _model(caps):
    return SimpleNamespace(capabilities=caps)


class TestModelRouter(unittest.TestCase):
    def test_filters_by_capabilities(self):
        models = [
            _model({"reasoning": "supported", "structured_output": "supported", "embedding": "unsupported"}),
            _model({"reasoning": "unknown", "structured_output": "supported"}),
        ]
        result = model_router.find_models_by_capabilities(models, ["reasoning", "structured_output"])
        self.assertEqual(len(result), 1)
        self.assertIs(result[0], models[0])

    def test_empty_required_returns_all(self):
        models = [_model({}), _model({"embedding": "supported"})]
        self.assertEqual(len(model_router.find_models_by_capabilities(models, [])), 2)

    def test_no_match_returns_empty(self):
        models = [_model({"embedding": "unsupported"})]
        self.assertEqual(model_router.find_models_by_capabilities(models, ["embedding"]), [])


if __name__ == "__main__":
    unittest.main()
