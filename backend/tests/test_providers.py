"""Provider Adapter 单元测试（mock httpx，不发起真实网络请求）。"""
import unittest
from unittest.mock import MagicMock, patch

import httpx

from app.services.providers import (
    DeepSeekAdapter,
    OpenAICompatibleAdapter,
    ProviderNotSupportedError,
    get_adapter,
)
from app.services.providers.deepseek import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DEEPSEEK_MODELS,
)


def _adapter():
    return OpenAICompatibleAdapter("https://api.openai.com/v1", "sk-test", "gpt-4o", provider="openai")


def _request():
    return httpx.Request("POST", "http://x")


class TestStatusToCode(unittest.TestCase):
    def test_status_mapping(self):
        cases = {
            401: "INVALID_API_KEY",
            403: "INVALID_API_KEY",
            404: "MODEL_NOT_FOUND",
            429: "RATE_LIMITED",
            400: "INVALID_BASE_URL",
            500: "PROVIDER_ERROR",
        }
        for status, expected in cases.items():
            self.assertEqual(OpenAICompatibleAdapter._status_to_code(status), expected)


class TestTestConnection(unittest.TestCase):
    def test_success(self):
        resp = httpx.Response(200, request=_request(), json={"choices": []})
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = resp
        with patch("app.services.providers.base.httpx.Client", return_value=client):
            result = _adapter().test_connection()
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["latency_ms"])
        self.assertIsNone(result["error_code"])

    def _error_case(self, exc):
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.side_effect = exc
        with patch("app.services.providers.base.httpx.Client", return_value=client):
            return _adapter().test_connection()

    def test_invalid_api_key(self):
        req = _request()
        exc = httpx.HTTPStatusError("401", request=req, response=httpx.Response(401, request=req))
        result = self._error_case(exc)
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "INVALID_API_KEY")

    def test_model_not_found(self):
        req = _request()
        exc = httpx.HTTPStatusError("404", request=req, response=httpx.Response(404, request=req))
        self.assertEqual(self._error_case(exc)["error_code"], "MODEL_NOT_FOUND")

    def test_invalid_base_url(self):
        req = _request()
        exc = httpx.HTTPStatusError("400", request=req, response=httpx.Response(400, request=req))
        self.assertEqual(self._error_case(exc)["error_code"], "INVALID_BASE_URL")

    def test_rate_limited(self):
        req = _request()
        exc = httpx.HTTPStatusError("429", request=req, response=httpx.Response(429, request=req))
        self.assertEqual(self._error_case(exc)["error_code"], "RATE_LIMITED")

    def test_provider_error(self):
        req = _request()
        exc = httpx.HTTPStatusError("500", request=req, response=httpx.Response(500, request=req))
        self.assertEqual(self._error_case(exc)["error_code"], "PROVIDER_ERROR")

    def test_timeout(self):
        self.assertEqual(self._error_case(httpx.TimeoutException("timeout"))["error_code"], "TIMEOUT")

    def test_network_error(self):
        self.assertEqual(self._error_case(httpx.ConnectError("conn", request=_request()))["error_code"], "NETWORK_ERROR")

    def test_unknown(self):
        self.assertEqual(self._error_case(RuntimeError("boom"))["error_code"], "UNKNOWN")

    def test_error_does_not_leak_key_or_traceback(self):
        req = _request()
        exc = httpx.HTTPStatusError("401", request=req, response=httpx.Response(401, request=req))
        result = self._error_case(exc)
        self.assertNotIn("sk-test", result["message"])
        self.assertNotIn("Traceback", result["message"])


class TestGenerate(unittest.TestCase):
    def test_generate_unified_format(self):
        resp = httpx.Response(
            200,
            request=_request(),
            json={
                "model": "gpt-4o",
                "choices": [{"message": {"role": "assistant", "content": "hello"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            },
        )
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = resp
        with patch("app.services.providers.base.httpx.Client", return_value=client):
            result = _adapter().generate([{"role": "user", "content": "hi"}])
        self.assertEqual(result["content"], "hello")
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["usage"]["input_tokens"], 1)
        self.assertEqual(result["usage"]["total_tokens"], 3)

    def test_generate_no_usage_is_null(self):
        resp = httpx.Response(
            200,
            request=_request(),
            json={"model": "gpt-4o", "choices": [{"message": {"content": "hello"}}]},
        )
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = resp
        with patch("app.services.providers.base.httpx.Client", return_value=client):
            result = _adapter().generate([{"role": "user", "content": "hi"}])
        self.assertIsNone(result["usage"]["input_tokens"])
        self.assertIsNone(result["usage"]["total_tokens"])


class TestAdapterFactory(unittest.TestCase):
    def test_deepseek_default_base_url(self):
        adapter = get_adapter("deepseek", "", "sk", "deepseek-flash")
        self.assertIsInstance(adapter, DeepSeekAdapter)
        self.assertEqual(adapter.base_url, "https://api.deepseek.com")

    def test_openai_compatible(self):
        adapter = get_adapter("openai", "https://api.openai.com/v1", "sk", "gpt-4o")
        self.assertIsInstance(adapter, OpenAICompatibleAdapter)
        self.assertEqual(adapter.provider, "openai")

    def test_unsupported_provider(self):
        with self.assertRaises(ProviderNotSupportedError):
            get_adapter("claude", "", "sk", "claude-3")


class TestDeepSeekConfig(unittest.TestCase):
    def test_default_base_url(self):
        self.assertEqual(DEFAULT_DEEPSEEK_BASE_URL, "https://api.deepseek.com")

    def test_default_model_is_flash(self):
        self.assertEqual(DEFAULT_DEEPSEEK_MODEL, "deepseek-flash")

    def test_model_list_contains_official_models(self):
        self.assertIn("deepseek-flash", DEEPSEEK_MODELS)
        self.assertIn("deepseek-v4-pro", DEEPSEEK_MODELS)
        self.assertNotIn("deepseek-chat", DEEPSEEK_MODELS)


class TestDeepSeekAdapterRequest(unittest.TestCase):
    def test_request_url_path_auth_and_model(self):
        resp = httpx.Response(
            200,
            request=_request(),
            json={
                "model": "deepseek-flash",
                "choices": [{"message": {"content": "hi"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            },
        )
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = resp
        adapter = DeepSeekAdapter("", "sk-test-key", "deepseek-flash")
        with patch("app.services.providers.base.httpx.Client", return_value=client):
            adapter.generate([{"role": "user", "content": "hi"}])
        args, kwargs = client.post.call_args
        self.assertEqual(args[0], "https://api.deepseek.com/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer sk-test-key")
        self.assertEqual(kwargs["json"]["model"], "deepseek-flash")

    def test_404_maps_to_model_not_found(self):
        req = _request()
        exc = httpx.HTTPStatusError("404", request=req, response=httpx.Response(404, request=req))
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.side_effect = exc
        adapter = DeepSeekAdapter("", "sk-test-key", "deepseek-flash")
        with patch("app.services.providers.base.httpx.Client", return_value=client):
            result = adapter.test_connection()
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "MODEL_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
