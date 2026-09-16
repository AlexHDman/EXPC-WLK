import io
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from portable_boot import ROOT, configure
configure()

from whisper_key.audio_recorder import AudioRecorder  # noqa: E402
from whisper_key.clipboard_manager import ClipboardManager  # noqa: E402
from whisper_key.hotkey_listener import HotkeyListener  # noqa: E402
from whisper_key.instance_manager import guard_against_multiple_instances  # noqa: E402


class ReleaseRegressionTests(unittest.TestCase):
    def test_portable_tls_uses_bundled_ca_store(self):
        expected = ROOT / "app" / "site-packages" / "certifi" / "cacert.pem"
        self.assertTrue(expected.is_file())
        self.assertEqual(os.environ["SSL_CERT_FILE"], str(expected))
        self.assertNotIn("SSL_CERT_DIR", os.environ)

    def test_no_microphone_fails_clearly_during_source_test(self):
        recorder = AudioRecorder.__new__(AudioRecorder)
        recorder.device = None
        recorder.logger = Mock()
        with patch("whisper_key.audio_recorder.sd.query_devices", side_effect=RuntimeError("no input device")):
            with self.assertRaisesRegex(RuntimeError, "no input device"):
                recorder._test_audio_source()
        recorder.logger.error.assert_called_once()

    @patch("whisper_key.hotkey_listener.hotkeys")
    def test_hotkey_bindings_and_callbacks(self, hotkeys):
        state = SimpleNamespace(
            start_recording=Mock(), stop_recording=Mock(),
            cancel_recording_hotkey_pressed=Mock(), start_command_recording=Mock(),
            audio_recorder=SimpleNamespace(get_recording_status=lambda: True),
        )
        listener = HotkeyListener(
            state, "ctrl+alt+space", "ctrl+alt+s", "ctrl+alt+enter",
            "escape", "ctrl+alt+c", "toggle",
        )
        self.addCleanup(listener.stop_listening)
        self.assertEqual(len(listener.hotkey_bindings), 5)
        listener._standard_hotkey_pressed()
        listener._arm_keys_on_release()
        listener._auto_send_key_pressed()
        listener._cancel_hotkey_pressed()
        listener._command_hotkey_pressed()
        state.start_recording.assert_called_once()
        state.stop_recording.assert_called_once_with(use_auto_enter=True)
        state.cancel_recording_hotkey_pressed.assert_called_once()
        state.start_command_recording.assert_called_once()
        hotkeys.register.assert_called_once()
        hotkeys.start.assert_called_once()

    @patch("whisper_key.clipboard_manager.time.sleep")
    @patch("whisper_key.clipboard_manager.keyboard")
    @patch("whisper_key.clipboard_manager.pyperclip")
    def test_clipboard_copy_paste_restore_and_direct_type(self, clipboard, keyboard, sleep):
        clipboard.paste.return_value = "original"
        manager = ClipboardManager(True, "paste", "ctrl+v", 0, True, 0, True, 0, 0, 0)
        self.assertTrue(manager.deliver_transcription("hello"))
        self.assertEqual(clipboard.copy.call_args_list[0].args, ("hello",))
        self.assertEqual(clipboard.copy.call_args_list[-1].args, ("original",))
        keyboard.send_hotkey.assert_called_once_with("ctrl", "v")

        manager.delivery_method = "type"
        self.assertTrue(manager.deliver_transcription("привет"))
        keyboard.type_text.assert_called_once_with("привет")

    def test_duplicate_instance_is_rejected(self):
        with patch("whisper_key.instance_manager.instance_lock.acquire_lock", return_value=None), \
                patch("whisper_key.instance_manager.time.sleep"), \
                patch("sys.stdout", new=io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                guard_against_multiple_instances("EXPC-WLK-test")
        self.assertEqual(stopped.exception.code, 0)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main(verbosity=2)
