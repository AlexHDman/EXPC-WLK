import logging
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from portable_boot import configure
configure()
from whisper_key import system_tray as ui  # noqa: E402 - configure DLL paths first
from whisper_key import model_store  # noqa: E402
from whisper_key.platform.windows import icons  # noqa: E402


class TrayStatusTests(unittest.TestCase):
    def setUp(self):
        self.model = object()
        self.engine = SimpleNamespace(model=self.model, device="cpu", is_loading=lambda: False)
        self.state = SimpleNamespace(whisper_engine=self.engine, is_model_loading=False,
                                     get_current_state=lambda: "idle")
        self.tray = ui.SystemTray(self.state, {"enabled": True})
        self.tray.hotkey_listener = SimpleNamespace(is_listening=True)
        self.tray._create_menu = Mock(return_value=())
        self.tray.icon = Mock()
        self.tray.is_running = True
        self.addCleanup(self.tray.stop)
        self.addCleanup(ui.close_startup_status)

    def test_ready_recording_processing_colors(self):
        for state in ("idle", "recording", "processing"):
            self.tray.update_state(state)
            self.assertEqual(self.tray.current_state, state)
            self.assertEqual(self.tray.icon.title, self.tray._title(state))
        self.assertIs(self.engine.model, self.model)

    def test_loading_is_yellow(self):
        self.state.is_model_loading = True
        self.assertEqual(self.tray._display_state("processing"), "initializing")
        self.state.is_model_loading = False
        self.engine.is_loading = lambda: True
        self.assertEqual(self.tray._display_state("idle"), "initializing")

    def test_active_backend_is_shown(self):
        self.assertEqual(self.tray._backend_label(), "CPU (INT8)")
        self.engine.device = "cuda"
        self.assertEqual(self.tray._backend_label(), "NVIDIA CUDA (FP16)")
        self.assertIn("NVIDIA CUDA (FP16)", self.tray._title("idle"))

    def test_active_model_is_shown(self):
        self.engine.model_key = "small"
        self.assertEqual(self.tray._model_label(), "small")
        self.engine.model_key = "large-v3-turbo"
        self.assertEqual(self.tray._model_label(), "large-v3-turbo")

    def test_model_download_progress_uses_active_tray(self):
        ui._active_icon = self.tray.icon
        with patch("whisper_key.tray_i18n.startup_language", return_value="en"):
            model_store.show_progress(5, 10)
        self.assertEqual(self.tray.icon.title, "EXPC-WLK — Downloading model: 50%")

    def test_unavailable_model_and_hotkeys(self):
        self.engine.model = None
        self.assertEqual(self.tray._display_state("idle"), "unavailable")
        self.engine.model = self.model
        self.tray.hotkey_listener.is_listening = False
        self.assertEqual(self.tray._display_state("idle"), "unavailable")

    def test_error_is_gray_until_next_operation(self):
        record = logging.LogRecord("whisper_key.whisper_engine", logging.ERROR,
                                   "", 0, "test error", (), None)
        self.tray._error_handler.emit(record)
        self.tray.update_state("idle")
        self.assertEqual(self.tray.current_state, "unavailable")
        self.tray.update_state("recording")
        self.assertEqual(self.tray.current_state, "recording")
        self.assertIs(self.engine.model, self.model)

    def test_repeated_recording_does_not_clear_new_error(self):
        self.tray.update_state("recording")
        self.tray._status_error = True
        self.tray.update_state("recording")
        self.assertEqual(self.tray.current_state, "unavailable")
        self.tray.update_state("recording")
        self.assertEqual(self.tray.current_state, "unavailable")

    def test_badge_pixels(self):
        images = icons.get_tray_icons()
        for state, color in icons.STATUS_COLORS.items():
            image = images[state]
            center = (int(image.width * .81), int(image.height * .17))
            self.assertEqual(image.getpixel(center)[:3], color)
        self.assertEqual(set(images), set(ui.STATUS_TITLES))
        neutral = images["idle"]
        left = (0, 0, int(neutral.width * .6), neutral.height)
        for image in images.values():
            self.assertEqual(image.crop(left).tobytes(), neutral.crop(left).tobytes())

    def test_startup_icon_adopted_without_second_icon(self):
        self.tray.is_running = False
        self.tray.config_manager = SimpleNamespace(config={"_cpu_notice": True})
        with patch.object(ui.pystray, "Icon") as constructor, patch.object(ui.threading, "Thread"):
            ui.show_startup_status()
            initial = constructor.return_value
            self.assertEqual(constructor.call_args.args[2], "EXPC-WLK — " + ui.tray_i18n.text("initializing", ui.tray_i18n.startup_language()))
            self.assertTrue(self.tray.start())
            constructor.assert_called_once()
            self.assertIs(self.tray.icon, initial)
            self.assertIsNone(ui._startup_icon)
            self.assertEqual(initial.title, self.tray._title("idle"))
            initial.notify.assert_called_once_with(
                self.tray._text("cpu_fallback"), "EXPC-WLK"
            )

    def test_startup_error_visible_and_cleanup(self):
        with patch.object(ui.pystray, "Icon") as constructor:
            ui.show_startup_status()
            ui.show_startup_status("unavailable")
            self.assertEqual(constructor.return_value.title, "EXPC-WLK — " + ui.tray_i18n.text("unavailable", ui.tray_i18n.startup_language()))
            ui.close_startup_status()
            constructor.return_value.stop.assert_called_once()
            self.assertIsNone(ui._startup_icon)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main(verbosity=2)
