import hashlib
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import zipfile

from portable_boot import configure
configure()
from whisper_key import portable_updater as updater, tray_i18n as i18n, system_tray as ui  # noqa: E402
from ruamel.yaml import YAML  # noqa: E402


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = {"repository": "example/EXPC-WLK", "version": "0.8.2", "asset_name": "EXPC-WLK-portable.zip"}
        self.data = {"tag_name": "v0.8.3", "draft": False, "prerelease": False, "assets": [{
            "name": self.config["asset_name"], "size": 100,
            "digest": "sha256:" + "a" * 64,
            "browser_download_url": "https://github.com/example/EXPC-WLK/releases/download/v0.8.3/EXPC-WLK-portable.zip"}]}

    def test_versions(self):
        for tag, expected in (("v0.8.3", "available"), ("0.8.2", "up_to_date"), ("0.7.9", "older")):
            self.data["tag_name"] = tag
            self.assertEqual(updater.check_latest(self.config, lambda url: self.data)["status"], expected)
        for value in ("0.8.3-beta", "01.2.3", "x", "1.2"):
            with self.assertRaises(ValueError):
                updater.version(value)

    def test_unconfigured_never_connects(self):
        fetch = Mock(side_effect=AssertionError("Network not allowed"))
        self.assertEqual(updater.check_latest({**self.config, "repository": ""}, fetch)["status"], "not_configured")
        fetch.assert_not_called()

    def test_official_url_and_hash_required(self):
        self.data["assets"][0]["browser_download_url"] = "https://evil.example/file.zip"
        with self.assertRaises(ValueError):
            updater.check_latest(self.config, lambda url: self.data)
        self.data["assets"][0]["browser_download_url"] = "https://github.com/example/EXPC-WLK/releases/download/v0.8.3/EXPC-WLK-portable.zip"
        self.data["assets"][0]["digest"] = ""
        with self.assertRaises(ValueError):
            updater.check_latest(self.config, lambda url: self.data)

    def test_split_package_tracks_same_variant(self):
        config = {**self.config, "package_variant": "cpu",
                  "asset_name": "EXPC-WLK-portable-CPU-v0.8.2.zip"}
        name = "EXPC-WLK-portable-CPU-v0.8.3.zip"
        data = {**self.data, "assets": [{**self.data["assets"][0], "name": name,
                "browser_download_url": "https://github.com/example/EXPC-WLK/releases/download/v0.8.3/" + name}]}
        result = updater.check_latest(config, lambda url: data)
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["url"].endswith(name))

    def archive(self, extra=None):
        path = self.root / "release.zip"
        files = {"EXPC-WLK.exe": b"MZ", "WhisperKey/runtime/pythonw.exe": b"MZ",
                 "WhisperKey/runtime/python312.dll": b"MZ", "WhisperKey/app/portable_boot.py": b"pass",
                 "WhisperKey/config/PortableUpdater.exe": b"MZ",
                 "WhisperKey/config/release.json": json.dumps({"version": "0.8.3"}).encode()}
        files.update(extra or {})
        with zipfile.ZipFile(path, "w") as package:
            for name, value in files.items():
                package.writestr(name, value)
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_stage_preserves_user_data_and_moved_path(self):
        user = self.root / "user_settings.yaml"
        user.write_bytes(b"post_processing: {corrections: {test: TEST}}")
        before = user.read_bytes()
        archive, digest = self.archive()
        stage = updater.stage_archive(archive, digest, "0.8.3", self.root / "Moved portable path")
        self.assertEqual(user.read_bytes(), before)
        self.assertTrue((stage / "EXPC-WLK.exe").exists())

    def test_bad_hash_and_version_leave_current_usable(self):
        current = self.root / "EXPC-WLK.exe"
        current.write_bytes(b"current")
        archive, digest = self.archive()
        for expected_hash, expected_version in (("0" * 64, "0.8.3"), (digest, "0.8.4")):
            with self.assertRaises(ValueError):
                updater.stage_archive(archive, expected_hash, expected_version, self.root / "stage")
            self.assertFalse((self.root / "stage").exists())
            self.assertEqual(current.read_bytes(), b"current")

    def test_archive_path_and_userdata_rejection(self):
        for name in ("../EXPC-WLK.exe", "C:/evil", "WhisperKey/logs/log.txt", "WhisperKey/models/model.bin",
                     "WhisperKey/app/user_settings.yaml", "WhisperKey/app/vocabulary.db", "WhisperKey/app/NUL.txt"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                updater.safe_member(name)


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        state = SimpleNamespace(get_application_state=lambda: {}, get_available_audio_hosts=lambda: [],
                                get_current_audio_host=lambda: "", get_available_audio_devices=lambda host: [],
                                get_current_audio_device_id=lambda: None)
        config = SimpleNamespace(get_setting=lambda section, key: "large-v3-turbo" if key == "model" else False)
        self.tray = ui.SystemTray(state, {"enabled": True}, config)
        self.tray.icon = Mock()
        self.tray.current_state = "idle"

    def test_all_menu_labels_and_statuses(self):
        for language in ("ru", "en"):
            self.tray.language = language
            menu = self.tray._create_menu()
            labels = {item.text for item in menu.items}
            for key in ("autostart", "restart", "folder", "updates", "benchmark", "language", "exit", "log", "settings", "copy"):
                self.assertIn(i18n.text(key, language), labels)
            for state in ("idle", "recording", "initializing", "unavailable"):
                self.assertEqual(
                    self.tray._title(state),
                    "EXPC-WLK — " + i18n.text(state, language) + " — CPU (INT8)",
                )

    def test_language_switch_persistence_preserves_corrections(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "user_settings.yaml"
            path.write_text("# preserved\npost_processing:\n  corrections: {майлстоун: Milestone}\n", encoding="utf-8")
            config = self.tray.config_manager
            config.user_settings_path = str(path)
            config.config = {}
            for language in ("en", "ru"):
                self.tray._set_language(language)
                with path.open(encoding="utf-8") as stream:
                    loaded = YAML().load(stream)
                self.assertEqual(loaded["system_tray"]["language"], language)
                self.assertEqual(loaded["post_processing"]["corrections"], {"майлстоун": "Milestone"})
                self.assertIn("# preserved", path.read_text(encoding="utf-8"))
                self.assertEqual(i18n.resolve_language(loaded["system_tray"]["language"]), language)
                subprocess.run([sys.executable, "-I", "-c",
                    "from ruamel.yaml import YAML; import sys; "
                    "data=YAML().load(open(sys.argv[1], encoding='utf-8')); "
                    "assert data['system_tray']['language']==sys.argv[2]", str(path), language], check=True)

    def test_windows_locale(self):
        with patch.object(i18n.ctypes.windll.kernel32, "GetUserDefaultUILanguage", return_value=0x419):
            self.assertEqual(i18n.resolve_language("auto"), "ru")
        with patch.object(i18n.ctypes.windll.kernel32, "GetUserDefaultUILanguage", return_value=0x409):
            self.assertEqual(i18n.resolve_language("auto"), "en")

    def test_offline_check_keeps_tray_running(self):
        self.tray.is_running = True
        with patch.object(updater, "check_latest", side_effect=OSError("offline")), \
                patch.object(self.tray, "_show_popup") as popup:
            self.tray._check_updates()
            self.assertTrue(self.tray._update_lock.acquire(timeout=3))
            self.tray._update_lock.release()
        self.assertTrue(self.tray.is_running)
        popup.assert_called_once_with(self.tray._text("update_failed"), timeout=15)

    def test_autostart_still_reads_live_state(self):
        for language in ("ru", "en"):
            self.tray.language = language
            item = next(i for i in self.tray._create_menu().items if i.text == i18n.text("autostart", language))
            with patch.object(ui.portable_actions, "autostart_enabled", return_value=True):
                self.assertTrue(item.checked)
            with patch.object(ui.portable_actions, "autostart_enabled", return_value=False):
                self.assertFalse(item.checked)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main(verbosity=2)
