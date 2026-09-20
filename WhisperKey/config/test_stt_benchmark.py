import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from portable_boot import configure
configure()

from whisper_key import stt_benchmark  # noqa: E402


class BenchmarkTests(unittest.TestCase):
    def engine(self, model="small", device="cpu", loaded=True):
        runtime = Mock()
        runtime.transcribe.return_value = (
            [SimpleNamespace(text=" Hello.")], SimpleNamespace())
        return SimpleNamespace(
            model_key=model, device=device,
            compute_type="float16" if device == "cuda" else "int8",
            language=None, model=runtime if loaded else None,
        )

    def run_valid(self, engine, clocks):
        with patch.object(stt_benchmark.model_store, "verify_local_model",
                          return_value={"status": "valid"}), \
                patch.object(stt_benchmark, "_cpu_name", return_value="Test CPU"), \
                patch.object(stt_benchmark, "_gpu_name", return_value="Test GPU"), \
                patch.object(stt_benchmark.time, "perf_counter", side_effect=clocks):
            return stt_benchmark.run(engine, Path("metadata"), Path("models"))

    def test_small_cpu(self):
        engine = self.engine()
        result = self.run_valid(engine, [10.0, 14.0])
        self.assertEqual((result["model"], result["backend"]), ("small", "CPU"))
        self.assertAlmostEqual(result["audio_seconds"], 8.3621875)
        self.assertEqual(result["inference_seconds"], 4.0)
        self.assertAlmostEqual(result["rtf"], 4.0 / 8.3621875)
        self.assertFalse(result["model_was_loaded"])

    def test_large_cuda(self):
        engine = self.engine("large-v3-turbo", "cuda")
        with patch.object(stt_benchmark.cuda_guard, "probe", return_value=(True, None)):
            result = self.run_valid(engine, [3.0, 4.0])
        self.assertEqual((result["model"], result["backend"]),
                         ("large-v3-turbo", "CUDA"))

    def test_missing_model_does_not_download(self):
        engine = self.engine()
        with patch.object(stt_benchmark.model_store, "verify_local_model",
                          return_value={"status": "missing"}), \
                self.assertRaises(stt_benchmark.ModelUnavailable):
            stt_benchmark.run(engine, Path("metadata"), Path("models"))
        engine.model.transcribe.assert_not_called()

    def test_cuda_unavailable_stops_before_model_check(self):
        engine = self.engine("large-v3-turbo", "cuda")
        with patch.object(stt_benchmark.cuda_guard, "probe", return_value=(False, "no_gpu")), \
                patch.object(stt_benchmark.model_store, "verify_local_model") as verify, \
                self.assertRaises(stt_benchmark.CudaUnavailable):
            stt_benchmark.run(engine, Path("metadata"), Path("models"))
        verify.assert_not_called()

    def test_does_not_change_engine_or_config_and_repeats(self):
        engine = self.engine()
        config = {"whisper": {"model": "small", "device": "cpu"}}
        before_config = copy.deepcopy(config)
        before_engine = vars(engine).copy()
        self.run_valid(engine, [1.0, 2.0])
        self.run_valid(engine, [3.0, 4.0])
        self.assertEqual(config, before_config)
        self.assertEqual(vars(engine), before_engine)
        self.assertEqual(engine.model.transcribe.call_count, 2)

    def test_load_time_is_measured_only_when_model_not_loaded(self):
        engine = self.engine(loaded=False)
        runtime = Mock()
        runtime.transcribe.return_value = ([], SimpleNamespace())
        manifest = {"directory": "small"}
        with patch.object(stt_benchmark.model_store, "verify_local_model",
                          return_value={"status": "valid"}), \
                patch.object(stt_benchmark.model_store, "manifest_for", return_value=manifest), \
                patch("faster_whisper.WhisperModel", return_value=runtime), \
                patch.object(stt_benchmark, "_cpu_name", return_value="CPU"), \
                patch.object(stt_benchmark, "_gpu_name", return_value="GPU"), \
                patch.object(stt_benchmark.time, "perf_counter",
                             side_effect=[1.0, 2.5, 3.0, 4.0]):
            result = stt_benchmark.run(engine, Path("metadata"), Path("models"))
        self.assertTrue(result["model_was_loaded"])
        self.assertEqual(result["load_seconds"], 1.5)
        self.assertIsNone(engine.model)

    def test_result_can_be_saved_to_desktop(self):
        with tempfile.TemporaryDirectory() as temp:
            desktop = Path(temp) / "Desktop"
            desktop.mkdir()
            target = stt_benchmark.save_result("result", temp)
            self.assertEqual(target, desktop / "EXPC-WLK-benchmark.txt")
            self.assertEqual(target.read_text(encoding="utf-8"), "result\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
