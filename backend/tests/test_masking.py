"""API Key 脱敏的单元测试。"""
import unittest

from app.core.masking import mask_secret


class TestMaskSecret(unittest.TestCase):
    def test_long_secret_keeps_only_tail(self):
        masked = mask_secret("sk-test-1234abcd")
        self.assertTrue(masked.endswith("abcd"))
        self.assertNotIn("sk-test", masked)
        self.assertNotIn("1234abcd", masked)

    def test_short_secret_fully_hidden(self):
        masked = mask_secret("ab")
        self.assertEqual(len(masked), 2)
        self.assertNotIn("a", masked)
        self.assertNotIn("b", masked)

    def test_empty_secret(self):
        self.assertEqual(mask_secret(""), "")
        self.assertEqual(mask_secret(None), "")


if __name__ == "__main__":
    unittest.main()
