import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app/site-packages"))
from whisper_key import diagnostics  # noqa: E402


class Engine:
    model_key = "small"
    device = "cpu"
    compute_type = "int8"


class DiagnosticsTests(unittest.TestCase):
    def test_allowlisted_report_has_required_fields_and_no_private_content(self):
        with patch("whisper_key.model_store.model_status", return_value="valid") as status:
            data = diagnostics.collect(Engine(), ROOT)
        status.assert_called_once_with(ROOT, "small", verify_hashes=True)
        report = diagnostics.format_report(data)
        version = json.loads((ROOT / "config/release.json").read_text(encoding="utf-8"))["version"]
        for value in (version, "small", "CPU", "int8", "Model revision", "Model directory"):
            self.assertIn(value, report)
        for forbidden in ("token", "password", "transcription", "hotword", "correction", "dictionary"):
            self.assertNotIn(forbidden, report.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
