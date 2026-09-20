import logging
import io
import inspect
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from portable_boot import configure
configure()
from whisper_key import system_tray as ui  # noqa: E402 - configure DLL paths first
from whisper_key import model_store  # noqa: E402
from whisper_key import utils  # noqa: E402
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

    @staticmethod
    def _run_thread_now(*args, **kwargs):
        target = kwargs["target"]
        return SimpleNamespace(start=target)

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

    def test_complete_menu_builds_with_two_argument_model_callbacks(self):
        self.tray.config_manager = SimpleNamespace(
            get_setting=lambda section, key: {
                ("clipboard", "auto_paste"): True,
                ("whisper", "model"): "small",
                ("voice_commands", "enabled"): True,
            }[(section, key)]
        )
        self.state.get_application_state = lambda: {"model_loading": False}
        self.state.get_available_audio_hosts = lambda: [{"name": "MME"}]
        self.state.get_current_audio_host = lambda: "MME"
        self.state.get_available_audio_devices = lambda host: [{"id": 1, "name": "Microphone"}]
        self.state.get_current_audio_device_id = lambda: 1
        self.tray.model_registry = object()

        with patch.object(model_store, "model_status", side_effect=("valid", "missing")):
            menu = ui.SystemTray._create_menu(self.tray)

        callbacks = []
        pending = list(menu)
        while pending:
            entry = pending.pop()
            if entry.submenu is not None:
                pending.extend(list(entry.submenu))
            else:
                callbacks.append(entry._action)

        self.assertTrue(callbacks)
        self.assertTrue(all(len(inspect.signature(callback).parameters) <= 2 for callback in callbacks))

    def test_update_up_to_date_uses_compact_popup(self):
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch("whisper_key.portable_updater.check_latest",
                      return_value={"status": "up_to_date"}), \
                patch.object(self.tray, "_show_popup") as popup:
            self.tray._check_updates()
        popup.assert_called_once_with("Обновлений нет")

    def test_update_available_has_download_and_later_actions(self):
        result = {"status": "available", "version": "1.0.1", "size": 100}
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch("whisper_key.portable_updater.check_latest", return_value=result), \
                patch.object(self.tray, "_show_popup") as popup:
            self.tray._check_updates()
        call = popup.call_args
        self.assertEqual(call.args[0], "Доступно обновление: 1.0.1")
        self.assertEqual(call.kwargs["timeout"], 20)
        self.assertEqual([button[0] for button in call.kwargs["buttons"]], ["Скачать", "Позже"])
        self.assertTrue(call.kwargs["buttons"][0][1])
        self.assertIsNone(call.kwargs["buttons"][1][1])

    def test_update_download_popup_uses_real_bytes(self):
        from whisper_key import portable_updater
        result = {"url": "https://github.com/example/update.zip", "size": 4}
        response = io.BytesIO(b"data")
        handle = Mock()

        def offer(*args):
            request = SimpleNamespace(full_url=result["url"])
            with portable_updater.urlopen(request) as stream:
                stream.read()

        with patch.object(portable_updater, "urlopen", return_value=response), \
                patch.object(portable_updater, "offer_update", side_effect=offer), \
                patch.object(self.tray, "_show_popup", return_value=handle):
            self.tray._offer_update(result)
        self.assertIn("100%", handle.update.call_args.args[0])
        self.assertIn("МБ/с", handle.update.call_args.args[0])
        handle.close.assert_called_once()

    def test_verify_small_and_large_show_named_success(self):
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch.object(model_store, "verify_local_model",
                             return_value={"status": "valid", "adopted": False}), \
                patch.object(self.tray, "_show_popup") as popup:
            self.tray._verify_model("small")
            self.tray._verify_model("large-v3-turbo")
        self.assertEqual([call.args[0] for call in popup.call_args_list], [
            "Модель small исправна", "Модель large-v3-turbo исправна",
        ])

    def test_verify_model_corrupt_offers_redownload(self):
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch.object(model_store, "verify_local_model",
                             return_value={"status": "corrupt", "adopted": False}), \
                patch.object(self.tray, "_show_popup") as popup:
            self.tray._verify_model("small")
        call = popup.call_args
        self.assertEqual(call.args[0], "Модель повреждена: small. Перекачать?")
        self.assertEqual(call.kwargs["timeout"], 30)
        self.assertEqual([item[0] for item in call.kwargs["buttons"]], ["Перекачать", "Позже"])

    def test_verify_adopts_model_with_missing_metadata(self):
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch.object(model_store, "verify_local_model",
                             return_value={"status": "valid", "adopted": True}), \
                patch.object(self.tray, "_show_popup") as popup:
            self.tray._verify_model("large-v3-turbo")
        popup.assert_called_once_with("Модель large-v3-turbo найдена и подключена")

    def test_cuda_model_allowed_when_nvidia_backend_is_available(self):
        with patch("whisper_key.cuda_guard.probe", return_value=(True, None)), \
                patch.object(self.state, "request_model_change", return_value=True,
                             create=True) as change:
            self.tray.config_manager = Mock()
            self.tray._select_model("large-v3-turbo")
        change.assert_called_once_with("large-v3-turbo")

    def test_cuda_model_blocked_before_download_without_nvidia(self):
        with patch("whisper_key.cuda_guard.probe",
                   return_value=(False, "nvidia_gpu_unavailable")), \
                patch.object(model_store, "model_status", return_value="missing"), \
                patch.object(model_store, "ensure_model") as ensure, \
                patch.object(self.tray, "_show_popup") as popup:
            self.tray._download_model("large-v3-turbo")
        ensure.assert_not_called()
        self.assertIn("NVIDIA GPU", popup.call_args.args[0])
        self.assertEqual(popup.call_args.kwargs["buttons"][0][0], "Установить small")

    def test_cuda_model_blocked_when_runtime_is_unavailable(self):
        with patch("whisper_key.cuda_guard.probe",
                   return_value=(False, "cuda_backend_unavailable")), \
                patch.object(model_store, "model_status", return_value="valid"), \
                patch.object(self.tray, "_show_popup") as popup:
            self.tray._select_model("large-v3-turbo")
        self.assertEqual(popup.call_args.kwargs["buttons"][0][0], "Переключиться на small")

    def test_small_fallback_action_selects_small(self):
        with patch("whisper_key.cuda_guard.probe", return_value=(False, "no_gpu")), \
                patch.object(model_store, "model_status", return_value="valid"), \
                patch.object(self.tray, "_show_popup") as popup, \
                patch.object(self.tray, "_select_model") as select:
            self.tray._allow_cuda_model()
            popup.call_args.kwargs["buttons"][0][1]()
        select.assert_called_once_with("small")

    def test_model_download_popup_uses_real_progress(self):
        handle = Mock()
        def ensure(*args, **kwargs):
            kwargs["progress"](50, 100)
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch.object(model_store, "ensure_model", side_effect=ensure), \
                patch.object(self.tray, "_show_popup", side_effect=(handle, Mock())):
            self.tray._download_model("small")
        message = handle.update.call_args.args[0]
        self.assertIn("50%", message)
        self.assertIn("МБ/с", message)
        self.assertIn("ETA", message)
        handle.close.assert_called_once()

    def test_benchmark_callback_shows_result_and_can_repeat(self):
        from whisper_key import stt_benchmark
        progress = Mock()
        result = {"rtf": 0.5}
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch.object(stt_benchmark, "run", return_value=result) as run, \
                patch.object(stt_benchmark, "format_result", return_value="benchmark result"), \
                patch.object(stt_benchmark, "save_result") as save, \
                patch.object(self.tray, "_show_popup",
                             side_effect=(progress, Mock(), progress, Mock())) as popup:
            self.tray._run_benchmark()
            self.tray._run_benchmark()
        self.assertEqual(run.call_count, 2)
        self.assertEqual(save.call_count, 2)
        self.assertEqual([call.args[0] for call in popup.call_args_list[1::2]],
                         ["benchmark result", "benchmark result"])

    def test_missing_benchmark_model_requires_download_button(self):
        from whisper_key import stt_benchmark
        self.engine.model_key = "small"
        progress = Mock()
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch.object(stt_benchmark, "run",
                             side_effect=stt_benchmark.ModelUnavailable("missing")), \
                patch.object(self.tray, "_show_popup", side_effect=(progress, Mock())) as popup, \
                patch.object(self.tray, "_download_model") as download:
            self.tray._run_benchmark()
            download.assert_not_called()
            popup.call_args_list[1].kwargs["buttons"][0][1]()
        download.assert_called_once_with("small")

    def test_cuda_benchmark_uses_existing_guard(self):
        from whisper_key import stt_benchmark
        progress = Mock()
        with patch.object(ui.threading, "Thread", side_effect=self._run_thread_now), \
                patch.object(stt_benchmark, "run",
                             side_effect=stt_benchmark.CudaUnavailable("cuda")), \
                patch.object(self.tray, "_show_popup", return_value=progress), \
                patch.object(self.tray, "_allow_cuda_model") as guard:
            self.tray._run_benchmark()
        guard.assert_called_once_with()

    def test_version_comes_from_canonical_release_metadata(self):
        self.assertEqual(utils.get_version(), "1.0.1")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main(verbosity=2)
