"""Relocatable bootstrap for the unchanged WhisperKey dictation pipeline."""
import ctypes
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DLL_HANDLES = []


def configure():
    os.chdir(ROOT)
    native = ROOT / 'runtime' / 'native'
    windows = Path(os.environ.get('SystemRoot', r'C:\Windows'))
    os.environ['PATH'] = os.pathsep.join(map(str, (native, ROOT / 'runtime',
                                                  windows / 'System32', windows)))
    for key in ('PYTHONPATH', 'PYTHONHOME', 'CUDA_PATH', 'PYAPP'):
        os.environ.pop(key, None)
    os.environ['HF_HOME'] = str(ROOT / 'cache' / 'huggingface')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    for folder in (ROOT / 'runtime', native,
                   ROOT / 'app' / 'site-packages' / 'pywin32_system32',
                   ROOT / 'app' / 'site-packages' / 'ctranslate2'):
        DLL_HANDLES.append(os.add_dll_directory(str(folder)))
    import pywin32_bootstrap  # noqa: F401


def prepare_app():
    from whisper_key import main
    from whisper_key.model_registry import ModelRegistry

    original_source = ModelRegistry.get_source
    original_cached = ModelRegistry.is_model_cached

    def model_source(self, key):
        if key == 'large-v3-turbo':
            model = ROOT / 'models' / key
            if not (model / 'model.bin').is_file():
                raise RuntimeError('Missing portable model: ' + str(model))
            return str(model)
        return original_source(self, key)

    def model_cached(self, key):
        if key == 'large-v3-turbo':
            return (ROOT / 'models' / key / 'model.bin').is_file()
        return original_cached(self, key)

    def gpu_check(config_manager, config):
        if config['device'] == 'cuda':
            import ctranslate2
            if ctranslate2.get_cuda_device_count() < 1:
                raise RuntimeError('NVIDIA CUDA GPU/driver unavailable. Install a compatible '
                                   'NVIDIA driver. No automatic CPU fallback was applied.')
            ctranslate2.get_supported_compute_types('cuda')
        return config

    def gpu_failure(error, *args):
        raise RuntimeError('CUDA model initialization failed. Check NVIDIA driver, GPU memory '
                           'and bundled native DLLs. No automatic CPU fallback. ' + str(error)) from error

    ModelRegistry.get_source = model_source
    ModelRegistry.is_model_cached = model_cached
    main.run_gpu_onboarding = gpu_check
    main._handle_gpu_failure = gpu_failure
    main.check_for_updates = lambda *args, **kwargs: None
    return main


def run():
    (ROOT / 'logs').mkdir(exist_ok=True)
    with (ROOT / 'logs' / 'startup.log').open('a', encoding='utf-8', buffering=1) as stream:
        sys.stdout = stream
        sys.stderr = stream
        tray_ui = None
        try:
            configure()
            app = prepare_app()  # Preserve the original audio/platform import order.
            from whisper_key import system_tray as tray_ui
            tray_ui.show_startup_status("initializing")
            print('PORTABLE_START executable=' + sys.executable, flush=True)
            app.main()
        except Exception as exc:  # noqa: BLE001 - visible failure for a windowless app
            import traceback
            traceback.print_exc()
            if tray_ui is not None:
                tray_ui.show_startup_status("unavailable")
            ctypes.windll.user32.MessageBoxW(None, str(exc) + '\n\nSee WhisperKey\\logs\\startup.log',
                                            'EXPC-WLK startup failed', 0x10)
            return 1
        finally:
            if tray_ui is not None:
                tray_ui.close_startup_status()
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
