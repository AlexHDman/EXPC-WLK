"""Live HKCU test: restores only EXPC-WLK values to their original state."""
import json
import shutil
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
import winreg

from portable_boot import configure
configure()
from whisper_key import portable_tray_actions as actions, system_tray as ui  # noqa: E402

root = actions.launcher_path().parent
results = []
original = {}
for key_path in (actions.RUN_KEY, actions.APPROVAL_KEY):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            original[key_path] = winreg.QueryValueEx(key, actions.VALUE_NAME)
    except FileNotFoundError:
        original[key_path] = None


def check(condition, description):
    assert condition, description
    results.append(description)


try:
    state = SimpleNamespace(get_application_state=lambda: {},
                            get_available_audio_hosts=lambda: [],
                            get_current_audio_host=lambda: "",
                            get_available_audio_devices=lambda host: [],
                            get_current_audio_device_id=lambda: None)
    config = SimpleNamespace(get_setting=lambda section, key: "large-v3-turbo" if key == "model" else False)
    tray = ui.SystemTray(state, {"enabled": True}, config)
    tray.icon = Mock()
    tray.current_state = "idle"
    tray.language = "ru"
    menu = tray._create_menu()
    items = {item.text: item for item in menu.items}
    toggle = items["Запускать вместе с Windows"]
    check(items["Статус: Готов"].enabled is False, "Ready status label")
    for label in ("Перезапустить WhisperKey", "Открыть папку приложения", "Выход"):
        check(label in items, label)
    actions.set_autostart(False)
    check(not toggle.checked, "OFF reads actual absent entry")
    toggle(tray.icon)
    check(toggle.checked, "Tray callback ON and checkmark true")
    check(actions._read(actions.RUN_KEY) == '"' + str(actions.launcher_path()) + '"', "HKCU contains exact current launcher")
    code = "from portable_boot import configure; configure(); from whisper_key.portable_tray_actions import autostart_enabled; assert autostart_enabled()"
    subprocess.run([sys.executable, "-I", "-c", code], check=True)
    check(True, "Fresh isolated process reads persisted ON state")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, actions.APPROVAL_KEY) as key:
        winreg.SetValueEx(key, actions.VALUE_NAME, 0, winreg.REG_BINARY, bytes([3]) + bytes(11))
    check(not toggle.checked, "Task Manager disabled state is unchecked")
    toggle(tray.icon)
    check(toggle.checked, "Toggle clears disabled override")
    moved = root / "WhisperKey/logs/autostart moved path"
    moved.mkdir(exist_ok=True)
    moved_exe = moved / "EXPC-WLK.exe"
    shutil.copyfile(root / "EXPC-WLK.exe", moved_exe)
    subprocess.run([str(moved_exe), "--enable-autostart", "--quiet"], check=True)
    check(actions.autostart_enabled(moved_exe), "Relocated launcher registers its own path including spaces")
    check(not toggle.checked, "Old/different path is unchecked in current tray")
    toggle(tray.icon)
    check(toggle.checked and str(moved) not in actions._read(actions.RUN_KEY), "Retoggle replaces stale path with current launcher")
    toggle(tray.icon)
    check(not toggle.checked and actions._read(actions.RUN_KEY) is None, "OFF removes entry and checkmark")
    with patch.object(ui, "open_file") as opened:
        items["Открыть папку приложения"](tray.icon)
        opened.assert_called_once_with(str(root))
    check(True, "Open folder resolves current portable root")
    with patch.object(actions, "request_restart") as request, patch.object(tray, "_quit_application_from_tray") as quit_app:
        items["Перезапустить WhisperKey"](tray.icon)
        request.assert_called_once()
        quit_app.assert_called_once()
    check(True, "Restart menu signals launcher before exit")
    moved_exe.unlink()
    moved.rmdir()
finally:
    for key_path, value in original.items():
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            if value is None:
                try:
                    winreg.DeleteValue(key, actions.VALUE_NAME)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(key, actions.VALUE_NAME, 0, value[1], value[0])
    (root / "WhisperKey/logs/tray-autostart-tests.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print("PASS:", len(results), "checks; original registry values restored")
