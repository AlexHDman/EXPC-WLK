"""Relocatable bootstrap for the unchanged WhisperKey dictation pipeline."""
import ctypes
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DLL_HANDLES = []


def package_variant():
    profile = ROOT / 'config' / 'package-profile.json'
    if not profile.is_file():
        return None
    import json
    variant = json.loads(profile.read_text(encoding='utf-8')).get('variant')
    return variant if variant in ('cpu', 'cuda') else None


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
    ca_bundle = ROOT / 'app' / 'site-packages' / 'certifi' / 'cacert.pem'
    if not ca_bundle.is_file():
        raise FileNotFoundError('Bundled CA certificate store is missing: ' + str(ca_bundle))
    os.environ['SSL_CERT_FILE'] = str(ca_bundle)
    os.environ.pop('SSL_CERT_DIR', None)
    for folder in (ROOT / 'runtime', native,
                   ROOT / 'app' / 'site-packages' / 'pywin32_system32',
                   ROOT / 'app' / 'site-packages' / 'ctranslate2'):
        if folder.is_dir():
            DLL_HANDLES.append(os.add_dll_directory(str(folder)))
    import pywin32_bootstrap  # noqa: F401


def prepare_app():
    from whisper_key import main
    from whisper_key.model_registry import ModelRegistry

    original_cached = ModelRegistry.is_model_cached
    local_models = {"small", "large-v3-turbo"}

    def model_source(self, key):
        if key in local_models:
            from whisper_key.model_store import ensure_model
            return str(ensure_model(ROOT, key))
        raise ValueError("Unsupported portable model: " + str(key))

    def model_cached(self, key):
        if key in local_models:
            from whisper_key.model_store import manifest_for, valid_file
            manifest = manifest_for(ROOT, key)
            target = ROOT / 'models' / manifest['directory']
            return all(valid_file(target / item['name'], item) for item in manifest['files'])
        return original_cached(self, key)

    def gpu_check(config_manager, config):
        mode = config_manager.config.get('hardware', {}).get('mode', 'auto')
        if mode not in ('auto', 'cpu', 'cuda'):
            mode = 'auto'
        if package_variant() == 'cpu':
            mode = 'cpu'

        cuda_available = False
        if mode != 'cpu':
            from whisper_key.cuda_guard import probe
            cuda_available, _ = probe(ROOT)

        if mode == 'cuda' and not cuda_available:
            from whisper_key import tray_i18n, tray_popup
            language = tray_i18n.startup_language()
            from whisper_key.model_store import model_status
            small_ready = model_status(ROOT, 'small', verify_hashes=True) == 'valid'
            first = tray_i18n.text('switch_small' if small_ready else 'install_small', language)
            choice = tray_popup.choose(
                tray_i18n.text('cuda_unavailable', language),
                [first, tray_i18n.text('cancel', language)])
            if choice != 0:
                raise RuntimeError(tray_i18n.text('cuda_unavailable', language))
            mode = 'cpu'
            update_setting = getattr(config_manager, 'update_user_setting', None)
            if callable(update_setting):
                update_setting('hardware', 'mode', 'cpu')
            config_manager.config.setdefault('hardware', {})['mode'] = 'cpu'

        use_cuda = mode == 'cuda' or (mode == 'auto' and cuda_available)
        config['device'] = 'cuda' if use_cuda else 'cpu'
        config['compute_type'] = 'float16' if use_cuda else 'int8'
        config['model'] = 'large-v3-turbo' if use_cuda else 'small'
        for key, model in config.get('models', {}).items():
            if isinstance(model, dict):
                model['enabled'] = key in local_models
        config_manager.config['whisper']['device'] = config['device']
        config_manager.config['whisper']['compute_type'] = config['compute_type']
        config_manager.config['whisper']['model'] = config['model']
        config_manager.config['_hardware_backend'] = (
            'NVIDIA CUDA (FP16)' if use_cuda else 'CPU (INT8)'
        )
        config_manager.config['_cpu_fallback'] = mode == 'auto' and not cuda_available
        config_manager.config['_cpu_notice'] = not use_cuda
        return config

    def gpu_failure(error, whisper_config, vad_manager, model_registry, config_manager):
        mode = config_manager.config.get('hardware', {}).get('mode', 'auto')
        if mode == 'auto':
            config_manager.config['_cpu_fallback'] = True
            config_manager.config['_cpu_notice'] = True
            config_manager.config['_hardware_backend'] = 'CPU (INT8)'
            whisper_config['device'] = 'cpu'
            whisper_config['compute_type'] = 'int8'
            whisper_config['model'] = 'small'
            config_manager.config['whisper']['device'] = 'cpu'
            config_manager.config['whisper']['compute_type'] = 'int8'
            config_manager.config['whisper']['model'] = 'small'
            return main.setup_whisper_engine(
                whisper_config, vad_manager, model_registry, config_manager
            )
        raise RuntimeError('CUDA model initialization failed. Check NVIDIA driver, GPU memory '
                           'and bundled native DLLs. ' + str(error)) from error

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
