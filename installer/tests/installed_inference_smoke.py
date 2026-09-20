"""Live CUDA inference plus controlled hotkey/clipboard checks in installed runtime."""
import contextlib
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.environ["ProgramFiles"]) / "EXPC-WLK" / "app"))
from installed_boot import INSTALL_ROOT, configure, prepare_app


class FakeCallable:
    def __init__(self, result=None):
        self.calls = []
        self.result = result

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


class FakeClipboard:
    def __init__(self):
        self.values = []

    def paste(self):
        return "original"

    def copy(self, value):
        self.values.append(value)


class FakeKeyboard:
    def __init__(self):
        self.send_hotkey = FakeCallable()
        self.send_key = FakeCallable()
        self.type_text = FakeCallable()
        self.set_delay = FakeCallable()

    @staticmethod
    def validate_delivery_method(value):
        if value not in {"paste", "type"}:
            raise ValueError(value)
        return value


class FakeHotkeys:
    def __init__(self):
        self.register = FakeCallable()
        self.start = FakeCallable()
        self.stop = FakeCallable()


class State:
    def __init__(self):
        self.start_recording = FakeCallable()
        self.stop_recording = FakeCallable()
        self.cancel_recording_hotkey_pressed = FakeCallable()
        self.start_command_recording = FakeCallable()
        self.audio_recorder = type("Audio", (), {"get_recording_status": lambda self: True})()


def run():
    configure()
    app = prepare_app()
    from faster_whisper.audio import decode_audio
    from whisper_key import clipboard_manager, hotkey_listener
    from whisper_key.clipboard_manager import ClipboardManager
    from whisper_key.config_manager import ConfigManager
    from whisper_key.hotkey_listener import HotkeyListener
    from whisper_key.model_registry import ModelRegistry

    config = ConfigManager()
    whisper = config.get_whisper_config()
    app.run_gpu_onboarding(config, whisper)
    registry = ModelRegistry(whisper.get("models", {}))
    engine = app.setup_whisper_engine(whisper, None, registry, config)
    audio_path = INSTALL_ROOT / "app/site-packages/whisper_key/assets/sounds/streaming-recognizer-warmup.wav"
    audio = decode_audio(str(audio_path), sampling_rate=16000)
    text = engine.transcribe_audio(audio)
    if not text or engine.device != "cuda" or engine.compute_type != "float16":
        raise RuntimeError("CUDA FP16 transcription failed")

    fake_clipboard, fake_keyboard = FakeClipboard(), FakeKeyboard()
    clipboard_manager.pyperclip = fake_clipboard
    clipboard_manager.keyboard = fake_keyboard
    clipboard_manager.time.sleep = lambda *_: None
    delivery = ClipboardManager(True, "paste", "ctrl+v", 0, True, 0, True, 0, 0, 0)
    if not delivery.deliver_transcription("installed CUDA paste"):
        raise RuntimeError("Clipboard delivery failed")
    if not fake_keyboard.send_hotkey.calls or fake_clipboard.values[-1] != "original":
        raise RuntimeError("Clipboard restore/paste was not exercised")

    fake_hotkeys, state = FakeHotkeys(), State()
    hotkey_listener.hotkeys = fake_hotkeys
    listener = HotkeyListener(state, "ctrl+alt+space", "ctrl+alt+s", "ctrl+alt+enter",
                              "escape", "ctrl+alt+c", "toggle")
    listener._standard_hotkey_pressed()
    listener._arm_keys_on_release()
    listener._auto_send_key_pressed()
    listener._cancel_hotkey_pressed()
    listener._command_hotkey_pressed()
    listener.stop_listening()
    if not (state.start_recording.calls and state.stop_recording.calls and
            state.cancel_recording_hotkey_pressed.calls and state.start_command_recording.calls):
        raise RuntimeError("Hotkey callbacks failed")

    return {"pass": True, "device": engine.device,
            "compute_type": engine.compute_type, "model": whisper["model"],
            "text": text, "hotkey_bindings": len(listener.hotkey_bindings),
            "paste": True}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    with contextlib.redirect_stdout(io.StringIO()):
        result = run()
    print(json.dumps(result, ensure_ascii=False))
