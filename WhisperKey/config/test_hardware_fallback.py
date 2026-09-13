import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "WhisperKey/app"))

import portable_boot  # noqa: E402

portable_boot.configure()


class HardwareFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = portable_boot.prepare_app()

    def config(self, mode):
        data = {
            "hardware": {"mode": mode},
            "whisper": {"device": "cpu", "compute_type": "int8"},
        }
        return SimpleNamespace(config=data), data["whisper"].copy()

    def test_auto_selects_cuda_fp16(self):
        manager, whisper = self.config("auto")
        with patch("ctranslate2.get_cuda_device_count", return_value=1), patch(
            "ctranslate2.get_supported_compute_types", return_value={"float16", "int8"}
        ):
            result = self.main.run_gpu_onboarding(manager, whisper)
        self.assertEqual((result["device"], result["compute_type"]), ("cuda", "float16"))
        self.assertFalse(manager.config["_cpu_fallback"])

    def test_forced_cpu_does_not_probe_cuda(self):
        manager, whisper = self.config("cpu")
        with patch("ctranslate2.get_cuda_device_count") as probe:
            result = self.main.run_gpu_onboarding(manager, whisper)
        probe.assert_not_called()
        self.assertEqual((result["device"], result["compute_type"]), ("cpu", "int8"))

    def test_auto_without_cuda_falls_back_to_cpu(self):
        manager, whisper = self.config("auto")
        with patch("ctranslate2.get_cuda_device_count", return_value=0):
            result = self.main.run_gpu_onboarding(manager, whisper)
        self.assertEqual((result["device"], result["compute_type"]), ("cpu", "int8"))
        self.assertTrue(manager.config["_cpu_fallback"])

    def test_auto_model_init_failure_retries_on_cpu(self):
        manager, whisper = self.config("auto")
        expected = Mock(device="cpu")
        with patch.object(self.main, "setup_whisper_engine", return_value=expected) as setup:
            result = self.main._handle_gpu_failure(
                RuntimeError("CUDA unavailable"), whisper, Mock(), Mock(), manager
            )
        self.assertIs(result, expected)
        self.assertEqual((whisper["device"], whisper["compute_type"]), ("cpu", "int8"))
        setup.assert_called_once()

    def test_forced_cuda_failure_is_reported(self):
        manager, whisper = self.config("cuda")
        with patch("ctranslate2.get_cuda_device_count", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "NVIDIA CUDA"):
                self.main.run_gpu_onboarding(manager, whisper)


if __name__ == "__main__":
    unittest.main()
