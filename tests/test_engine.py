import unittest
from src.engine import GoogleAutoRedeemer


class TestGoogleAutoRedeemer(unittest.TestCase):
    def test_clean_url_valid(self):
        raw = "复制：https://serviceactivation.google.com/subscription/new/AQCpiIG9lrCBvajD2fbLQQRsc7q1GfSHdU6A== 优惠领取"
        cleaned = GoogleAutoRedeemer.clean_url(raw)
        self.assertEqual(
            cleaned,
            "https://serviceactivation.google.com/subscription/new/AQCpiIG9lrCBvajD2fbLQQRsc7q1GfSHdU6A=="
        )

    def test_clean_url_markdown(self):
        raw = "[Link](https://serviceactivation.google.com/subscription/new/TEST_TOKEN_123)"
        cleaned = GoogleAutoRedeemer.clean_url(raw)
        self.assertEqual(
            cleaned,
            "https://serviceactivation.google.com/subscription/new/TEST_TOKEN_123"
        )

    def test_clean_url_invalid(self):
        raw = "https://www.google.com/search?q=test"
        cleaned = GoogleAutoRedeemer.clean_url(raw)
        self.assertIsNone(cleaned)


if __name__ == "__main__":
    unittest.main()
