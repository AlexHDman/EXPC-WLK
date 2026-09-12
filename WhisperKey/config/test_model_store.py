import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from urllib.parse import urlsplit

from whisper_key import model_store


class ModelStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        self.data = {name: name.encode() for name in ("model.bin", "config.json", "tokenizer.json", "vocabulary.json")}
        self.manifest = {"format": 1, "model": "large-v3-turbo", "source": "owner/model",
                         "revision": "a" * 40, "target": "models/large-v3-turbo",
                         "files": [{"name": n, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
                                   for n, b in self.data.items()]}
        self.write_manifest()

    def write_manifest(self):
        (self.root / "config/model-manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def download(self, request, timeout):
        self.assertIn("/resolve/" + "a" * 40 + "/", request.full_url)
        name = urlsplit(request.full_url).path.rsplit("/", 1)[1]
        response = io.BytesIO(self.data[name])
        response.url = request.full_url
        return response

    def test_pinned_download_then_offline_reuse(self):
        consent = Mock(return_value=True)
        path = model_store.ensure_model(self.root, consent=consent, progress=Mock(), opener=self.download)
        consent.assert_called_once()
        for name, content in self.data.items():
            self.assertEqual((path / name).read_bytes(), content)
        forbidden = Mock(side_effect=AssertionError("No prompt/network on valid local model"))
        self.assertEqual(model_store.ensure_model(self.root, consent=forbidden, opener=forbidden), path)
        forbidden.assert_not_called()

    def test_cancel_keeps_files_untouched(self):
        opener = Mock()
        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            model_store.ensure_model(self.root, consent=lambda *a: False, opener=opener)
        opener.assert_not_called()
        self.assertFalse((self.root / self.manifest["target"]).exists())

    def test_hash_failure_does_not_replace_existing_file(self):
        target = self.root / self.manifest["target"]
        target.mkdir(parents=True)
        (target / "model.bin").write_bytes(b"old-local-model")
        self.manifest["files"][0]["sha256"] = "0" * 64
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            model_store.ensure_model(self.root, consent=lambda *a: True, progress=Mock(), opener=self.download)
        self.assertEqual((target / "model.bin").read_bytes(), b"old-local-model")
        self.assertFalse(list(target.glob("*.download")))

    def test_network_failure_cleans_incomplete_download(self):
        with self.assertRaises(OSError):
            model_store.ensure_model(self.root, consent=lambda *a: True, progress=Mock(),
                                     opener=Mock(side_effect=OSError("offline")))
        self.assertFalse(list((self.root / self.manifest["target"]).iterdir()))

    def test_unpinned_revision_and_outside_path_rejected(self):
        for key, value in (("revision", "latest"), ("target", "../outside")):
            old = self.manifest[key]
            self.manifest[key] = value
            self.write_manifest()
            with self.assertRaises(ValueError):
                model_store.ensure_model(self.root)
            self.manifest[key] = old


if __name__ == "__main__":
    unittest.main(verbosity=2)
