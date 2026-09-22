import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from whisper_key import model_import, model_store


class ModelImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        self.payloads = {
            "small": {name: ("small-" + name).encode() for name in
                      ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt")},
            "large-v3-turbo": {name: ("large-" + name).encode() for name in
                               ("model.bin", "config.json", "tokenizer.json", "vocabulary.json")},
        }
        models = {}
        for model_id, payloads in self.payloads.items():
            models[model_id] = {
                "id": model_id, "source": "owner/" + model_id,
                "revision": ("a" if model_id == "small" else "b") * 40,
                "directory": model_id,
                "runtime": {"format": "CTranslate2", "compatible": True},
                "files": [{"name": name, "bytes": len(payload),
                           "sha256": hashlib.sha256(payload).hexdigest()}
                          for name, payload in payloads.items()],
            }
        (self.root / "config/model-catalog.json").write_text(
            json.dumps({"format": 2, "model_root": "models", "models": models}),
            encoding="utf-8")
        self.destination = self.root / "machine-models"

    def make_source(self, base, model_id):
        target = Path(base) / model_id
        target.mkdir(parents=True)
        for name, payload in self.payloads[model_id].items():
            (target / name).write_bytes(payload)
        return target

    def test_portable_root_imports_small_offline_without_touching_source(self):
        portable = self.root / "portable/WhisperKey/models"
        source = self.make_source(portable, "small")
        before = {path.name: path.read_bytes() for path in source.iterdir()}
        result = model_import.import_selected(
            self.root, self.destination, self.root / "portable")
        self.assertEqual(result["model"], "small")
        self.assertTrue(result["copied"])
        self.assertEqual(before, {path.name: path.read_bytes() for path in source.iterdir()})
        self.assertEqual(model_store.model_status(
            self.root, "small", verify_hashes=True, model_root=self.destination), "valid")

    def test_installed_root_and_direct_directory_detect_both_models(self):
        installed = self.root / "copied/EXPC-WLK/Models"
        small = self.make_source(installed, "small")
        self.make_source(installed, "large-v3-turbo")
        result = model_import.import_selected(
            self.root, self.destination, self.root / "copied",
            preferred_model="large-v3-turbo", require_preferred=True)
        self.assertEqual(result["model"], "large-v3-turbo")
        direct = model_import.inspect_source(self.root, small)
        self.assertEqual([item["model"] for item in direct["valid"]], ["small"])

    def test_destination_adoption_avoids_copy_and_creates_metadata(self):
        target = self.make_source(self.destination, "small")
        result = model_import.import_model(self.root, self.destination, "small", target)
        self.assertFalse(result["copied"])
        self.assertTrue((target / model_store.METADATA_NAME).is_file())

    def test_invalid_or_incomplete_source_is_rejected_without_registration(self):
        source = self.make_source(self.root / "broken", "small")
        (source / "model.bin").write_bytes(b"corrupt")
        with self.assertRaisesRegex(model_import.ModelImportError, "SHA-256"):
            model_import.import_selected(self.root, self.destination, source)
        self.assertFalse((self.destination / "small").exists())
        (source / "model.bin").unlink()
        with self.assertRaisesRegex(model_import.ModelImportError, "missing"):
            model_import.import_selected(self.root, self.destination, source)

    def test_copy_failure_preserves_existing_destination(self):
        old = self.destination / "small"
        old.mkdir(parents=True)
        (old / "keep.txt").write_text("old", encoding="utf-8")
        source = self.make_source(self.root / "source", "small")
        with unittest.mock.patch.object(model_import.shutil, "copy2",
                                        Mock(side_effect=OSError("copy failed"))):
            with self.assertRaisesRegex(OSError, "copy failed"):
                model_import.import_model(self.root, self.destination, "small", source)
        self.assertEqual((old / "keep.txt").read_text(encoding="utf-8"), "old")


if __name__ == "__main__":
    unittest.main(verbosity=2)
