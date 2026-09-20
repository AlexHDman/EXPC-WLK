"""Deterministic installed-mode Ready handshake tests."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "WhisperKey" / "app" / "site-packages"))
sys.path.insert(0, str(REPO / "installer" / "runtime"))

from whisper_key import installed_updater  # noqa: E402
import installed_boot  # noqa: E402


class InstalledReadyTests(unittest.TestCase):
    def setUp(self):
        installed_updater._READY_HANDSHAKE = None

    def tearDown(self):
        installed_updater._READY_HANDSHAKE = None

    def test_explicit_receipt_is_atomic_structured_and_one_shot(self):
        token = "a" * 32
        with tempfile.TemporaryDirectory() as temp:
            user_data = Path(temp)
            receipt = user_data / f"installed-update-ready-{token}.json"
            installed_updater.configure_ready(token, receipt, user_data=user_data)
            self.assertTrue(installed_updater.mark_ready())
            self.assertEqual(json.loads(receipt.read_text(encoding="ascii")), {
                "format": 1, "state": "ready", "token": token,
            })
            self.assertFalse(installed_updater.mark_ready())
            self.assertEqual(list(user_data.glob("*.tmp-*")), [])

    def test_invalid_token_and_receipt_path_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            user_data = Path(temp)
            with self.assertRaises(ValueError):
                installed_updater.configure_ready("bad", user_data / "receipt.json",
                                                   user_data=user_data)
            token = "b" * 32
            with self.assertRaises(ValueError):
                installed_updater.configure_ready(
                    token, user_data.parent / f"installed-update-ready-{token}.json",
                    user_data=user_data)
            self.assertEqual(list(user_data.iterdir()), [])

    def test_bootstrap_consumes_only_exact_explicit_arguments(self):
        token = "c" * 32
        receipt = os.path.join("C:\\", "receipt.json")
        self.assertEqual(installed_boot.consume_ready_handshake([
            "--installed-update-token", token,
            "--installed-update-receipt", receipt,
        ]), (token, receipt))
        for malformed in (["--installed-update-token", token],
                          ["--unknown", token, "--installed-update-receipt", receipt]):
            with self.assertRaises(ValueError):
                installed_boot.consume_ready_handshake(malformed)

    def test_bootstrap_preserves_test_mode(self):
        token = "d" * 32
        receipt = os.path.join("C:\\", "receipt.json")
        original = sys.argv
        try:
            sys.argv = ["installed_boot.py", "--installed-update-token", token,
                        "--installed-update-receipt", receipt, "--test"]
            self.assertEqual(installed_boot.consume_ready_handshake(), (token, receipt))
            self.assertEqual(sys.argv, ["installed_boot.py", "--test"])
        finally:
            sys.argv = original

    def test_bootstrap_allows_test_mode_without_handshake(self):
        original = sys.argv
        try:
            sys.argv = ["installed_boot.py", "--test"]
            self.assertIsNone(installed_boot.consume_ready_handshake())
            self.assertEqual(sys.argv, ["installed_boot.py", "--test"])
        finally:
            sys.argv = original


if __name__ == "__main__":
    unittest.main()
