import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from ruamel.yaml import YAML

from portable_boot import configure
configure()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from whisper_key.config_manager import ConfigManager
from whisper_key.hotkey_listener import HotkeyListener
from whisper_key.state_manager import StateManager
from whisper_key.voice_activity_detection import VadEvent


DEFAULTS = Path(__file__).resolve().parents[1] / "app/site-packages/whisper_key/config.defaults.yaml"


class FreshConfigurationTests(unittest.TestCase):
    def test_fresh_user_config_persists_push_to_talk(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.dict(os.environ, {"APPDATA": temporary}):
            manager = ConfigManager(config_path=str(DEFAULTS))
            settings = Path(temporary) / "whisperkey/user_settings.yaml"
            data = YAML(typ="safe").load(settings.read_text(encoding="utf-8"))
            self.assertEqual(data["hotkey"]["recording_mode"], "push_to_talk")
            self.assertEqual(manager.get_hotkey_config()["recording_mode"], "push_to_talk")
            manager.update_audio_host("test-host")
            data = YAML(typ="safe").load(settings.read_text(encoding="utf-8"))
            self.assertEqual(data["hotkey"]["recording_mode"], "push_to_talk")

    def test_existing_explicit_toggle_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.dict(os.environ, {"APPDATA": temporary}):
            settings = Path(temporary) / "whisperkey/user_settings.yaml"
            settings.parent.mkdir()
            settings.write_text("hotkey:\n  recording_mode: toggle\n", encoding="utf-8")
            manager = ConfigManager(config_path=str(DEFAULTS))
            self.assertEqual(manager.get_hotkey_config()["recording_mode"], "toggle")


class PushToTalkTests(unittest.TestCase):
    @patch("whisper_key.hotkey_listener.hotkeys.start")
    @patch("whisper_key.hotkey_listener.hotkeys.register")
    def test_release_stops_immediately_and_starts_processing(self, register, start):
        state = Mock()
        listener = HotkeyListener(state, "ctrl+win", "ctrl")
        recording = next(binding for binding in listener.hotkey_bindings
                         if binding[0] == "ctrl+win")
        self.assertIsNotNone(recording[2])
        recording[1]()
        released = time.perf_counter()
        recording[2]()
        self.assertLess(time.perf_counter() - released, 0.1)
        state.start_recording.assert_called_once_with()
        state.stop_recording.assert_called_once_with()

    def test_vad_timeout_cannot_terminate_push_to_talk(self):
        state = StateManager.__new__(StateManager)
        state.config_manager = Mock()
        state.config_manager.get_hotkey_config.return_value = {
            "recording_mode": "push_to_talk"}
        state.audio_recorder = Mock()
        state.logger = Mock()
        state.handle_vad_event(VadEvent.SILENCE_TIMEOUT)
        state.audio_recorder.stop_recording.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
