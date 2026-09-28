"""能力推导的单元测试。"""
import unittest

from app.core.capabilities import ALL_CAPABILITIES, CapabilityState, resolve_capabilities


class TestResolveCapabilities(unittest.TestCase):
    def test_deepseek_preset(self):
        caps = resolve_capabilities("deepseek", "deepseek-flash")
        self.assertEqual(caps["text_generation"], CapabilityState.supported.value)
        self.assertEqual(caps["reasoning"], CapabilityState.supported.value)
        self.assertEqual(caps["structured_output"], CapabilityState.supported.value)
        self.assertEqual(caps["multimodal_understanding"], CapabilityState.unsupported.value)
        self.assertEqual(caps["image_generation"], CapabilityState.unsupported.value)
        self.assertEqual(caps["embedding"], CapabilityState.unknown.value)

    def test_unknown_provider_all_unknown(self):
        caps = resolve_capabilities("future_provider", "some-model")
        self.assertEqual(set(caps.keys()), set(ALL_CAPABILITIES))
        self.assertTrue(all(v == CapabilityState.unknown.value for v in caps.values()))

    def test_openai_embedding_model_supported(self):
        caps = resolve_capabilities("openai", "text-embedding-3-small")
        self.assertEqual(caps["embedding"], CapabilityState.supported.value)

    def test_openai_non_embedding_unknown(self):
        caps = resolve_capabilities("openai", "gpt-4o")
        self.assertEqual(caps["embedding"], CapabilityState.unknown.value)

    def test_custom_embedding_name_supported(self):
        caps = resolve_capabilities("custom", "text-embedding-v3")
        self.assertEqual(caps["embedding"], CapabilityState.supported.value)

    def test_custom_no_embedding_word_unknown(self):
        # 名字不含 "embedding" 的模型（如 bge-m3）不预判为支持 embedding
        caps = resolve_capabilities("custom", "bge-m3")
        self.assertEqual(caps["embedding"], CapabilityState.unknown.value)


if __name__ == "__main__":
    unittest.main()
