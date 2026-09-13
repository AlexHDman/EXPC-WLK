import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.parse import unquote, urlsplit

from whisper_key import model_store


class InterruptedResponse(io.BytesIO):
    def __init__(self, data, url):
        super().__init__(data)
        self.url = url
        self.reads = 0

    def read(self, size=-1):
        self.reads += 1
        if self.reads > 1:
            raise OSError("connection interrupted")
        return super().read(2)


class ModelStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        self.payloads = {
            "small": {name: ("small-" + name).encode() for name in
                      ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt")},
            "large-v3-turbo": {name: ("turbo-" + name).encode() for name in
                               ("model.bin", "config.json", "tokenizer.json", "vocabulary.json")},
        }
        models = {}
        for model_id, data in self.payloads.items():
            models[model_id] = {
                "id": model_id,
                "source": "owner/" + model_id,
                "revision": ("a" if model_id == "small" else "b") * 40,
                "directory": model_id,
                "runtime": {"format": "CTranslate2", "compatible": True},
                "files": [
                    {"name": name, "bytes": len(content),
                     "sha256": hashlib.sha256(content).hexdigest()}
                    for name, content in data.items()
                ],
            }
        self.catalog = {"format": 2, "model_root": "models", "models": models}
        self.write_catalog()

    def write_catalog(self):
        (self.root / "config/model-catalog.json").write_text(
            json.dumps(self.catalog), encoding="utf-8"
        )

    def download(self, request, timeout):
        parts = urlsplit(request.full_url).path.split("/")
        model_id = parts[2]
        revision = parts[4]
        self.assertEqual(revision, self.catalog["models"][model_id]["revision"])
        name = unquote(parts[-1])
        response = io.BytesIO(self.payloads[model_id][name])
        response.url = request.full_url
        return response

    def install(self, model_id, **kwargs):
        return model_store.ensure_model(
            self.root, model_id, consent=lambda *args: True,
            progress=Mock(), opener=self.download, **kwargs
        )

    def test_fresh_small_and_large_downloads(self):
        for model_id in ("small", "large-v3-turbo"):
            path = self.install(model_id)
            self.assertEqual(path, self.root / "models" / model_id)
            for name, content in self.payloads[model_id].items():
                self.assertEqual((path / name).read_bytes(), content)
            metadata = json.loads((path / model_store.METADATA_NAME).read_text(encoding="utf-8"))
            self.assertEqual(metadata["revision"], self.catalog["models"][model_id]["revision"])

    def test_status_and_remove_are_local(self):
        from whisper_key import model_store
        self.assertEqual(model_store.model_status(self.root, "small"), "missing")
        target = self.install("small")
        self.assertEqual(model_store.model_status(self.root, "small"), "valid")
        (target / "model.bin").write_bytes(b"x" * len((target / "model.bin").read_bytes()))
        self.assertEqual(model_store.model_status(self.root, "small", verify_hashes=True), "corrupt")
        model_store.remove_model(self.root, "small")
        self.assertFalse(target.exists())
        self.assertEqual(model_store.model_status(self.root, "small"), "missing")

    def test_existing_valid_model_reused_offline_without_cache(self):
        path = self.install("small")
        forbidden = Mock(side_effect=AssertionError("network/prompt must not be used"))
        with patch.dict(os.environ, {"HF_HOME": r"Z:\missing-cache", "HF_HUB_OFFLINE": "1"}):
            self.assertEqual(
                model_store.ensure_model(self.root, "small", consent=forbidden, opener=forbidden),
                path,
            )
        forbidden.assert_not_called()

    def test_corrupt_file_detected_and_failed_repair_preserves_it(self):
        path = self.install("small")
        (path / "model.bin").write_bytes(b"corrupt-old-copy")
        with self.assertRaises(OSError):
            model_store.ensure_model(
                self.root, "small", consent=lambda *args: True, progress=Mock(),
                opener=Mock(side_effect=OSError("offline")),
            )
        self.assertEqual((path / "model.bin").read_bytes(), b"corrupt-old-copy")
        self.assertFalse(list((self.root / "models").glob(".staging-small-*")))

    def test_checksum_failure_and_interruption_leave_target_untouched(self):
        target = self.root / "models/small"
        target.mkdir(parents=True)
        (target / "keep.txt").write_text("old", encoding="utf-8")
        original = self.catalog["models"]["small"]["files"][0]["sha256"]
        self.catalog["models"]["small"]["files"][0]["sha256"] = "0" * 64
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.install("small")
        self.assertEqual((target / "keep.txt").read_text(encoding="utf-8"), "old")
        self.catalog["models"]["small"]["files"][0]["sha256"] = original
        self.write_catalog()

        def interrupted(request, timeout):
            name = unquote(urlsplit(request.full_url).path.rsplit("/", 1)[1])
            return InterruptedResponse(self.payloads["small"][name], request.full_url)

        with self.assertRaisesRegex(OSError, "interrupted"):
            model_store.ensure_model(
                self.root, "small", consent=lambda *args: True,
                progress=Mock(), opener=interrupted,
            )
        self.assertEqual((target / "keep.txt").read_text(encoding="utf-8"), "old")

    def test_atomic_install_failure_restores_previous_directory(self):
        target = self.root / "models/small"
        target.mkdir(parents=True)
        (target / "old.bin").write_bytes(b"previous")
        real_replace = os.replace

        def fail_stage_install(source, destination):
            if Path(source).name.startswith(".staging-small-") and Path(destination) == target:
                raise OSError("swap failed")
            return real_replace(source, destination)

        with patch.object(model_store.os, "replace", side_effect=fail_stage_install):
            with self.assertRaisesRegex(OSError, "swap failed"):
                self.install("small")
        self.assertEqual((target / "old.bin").read_bytes(), b"previous")

    def test_moved_portable_folder_reuses_local_model(self):
        self.install("small")
        moved = self.root.parent / (self.root.name + "-moved")
        shutil.copytree(self.root, moved)
        self.addCleanup(lambda: shutil.rmtree(moved, ignore_errors=True))
        forbidden = Mock(side_effect=AssertionError("moved install must remain offline"))
        result = model_store.ensure_model(moved, "small", consent=forbidden, opener=forbidden)
        self.assertEqual(result, moved / "models/small")
        forbidden.assert_not_called()

    def test_compatible_manifest_metadata_change_does_not_download(self):
        target = self.install("small")
        metadata = target / model_store.METADATA_NAME
        old = json.loads(metadata.read_text(encoding="utf-8"))
        old["manifest_sha256"] = "0" * 64
        metadata.write_text(json.dumps(old), encoding="utf-8")
        forbidden = Mock(side_effect=AssertionError("valid snapshot must be reused"))
        model_store.ensure_model(self.root, "small", consent=forbidden, opener=forbidden)
        refreshed = json.loads(metadata.read_text(encoding="utf-8"))
        self.assertNotEqual(refreshed["manifest_sha256"], "0" * 64)
        forbidden.assert_not_called()

    def test_invalid_revision_path_and_executable_rejected(self):
        model = self.catalog["models"]["small"]
        cases = (("revision", "latest"), ("directory", "../outside"))
        for key, value in cases:
            old = model[key]
            model[key] = value
            self.write_catalog()
            with self.assertRaises(ValueError):
                model_store.ensure_model(self.root, "small")
            model[key] = old
        model["files"][0]["name"] = "payload.exe"
        self.write_catalog()
        with self.assertRaises(ValueError):
            model_store.ensure_model(self.root, "small")


if __name__ == "__main__":
    unittest.main(verbosity=2)
