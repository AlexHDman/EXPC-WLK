"""Installed-only bootstrap. Portable bootstrap behavior is intentionally separate."""
import ctypes
import json
import os
import sys
from pathlib import Path


INSTALL_ROOT = Path(__file__).resolve().parent.parent
METADATA_ROOT = INSTALL_ROOT / "updater"
DLL_HANDLES = []
CONSOLE_STREAM = None


def consume_ready_handshake(arguments=None):
    consume_current = arguments is None
    values = list(sys.argv[1:] if consume_current else arguments)
    if not values:
        return None
    if values == ["--test"]:
        return None
    app_arguments = []
    if values[-1:] == ["--test"]:
        app_arguments = [values.pop()]
    if len(values) != 4 or values[0] != "--installed-update-token" or values[2] != "--installed-update-receipt":
        raise ValueError("Invalid installed launcher arguments")
    token, receipt = values[1], values[3]
    if consume_current:
        sys.argv[1:] = app_arguments
    return token, receipt


def model_root():
    program_data = os.environ.get("PROGRAMDATA")
    if not program_data:
        raise RuntimeError("PROGRAMDATA is unavailable")
    return Path(program_data) / "EXPC-WLK" / "Models"


def user_data_root():
    app_data = os.environ.get("APPDATA")
    if not app_data:
        raise RuntimeError("APPDATA is unavailable")
    return Path(app_data) / "whisperkey"


def package_variant():
    profile = METADATA_ROOT / "config" / "package-profile.json"
    variant = json.loads(profile.read_text(encoding="utf-8")).get("variant")
    if variant not in ("cpu", "cuda"):
        raise ValueError("Invalid installed runtime profile")
    return variant


def configure():
    global CONSOLE_STREAM
    runtime = INSTALL_ROOT / "runtime"
    native = runtime / "native"
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    launcher = INSTALL_ROOT / "EXPC-WLK.exe"
    models = model_root()
    user_data = user_data_root()

    os.chdir(INSTALL_ROOT)
    os.environ["PATH"] = os.pathsep.join(map(str, (native, runtime,
                                                   windows / "System32", windows)))
    for key in ("PYTHONPATH", "PYTHONHOME", "CUDA_PATH", "PYAPP"):
        os.environ.pop(key, None)
    os.environ.update({
        "EXPC_WLK_MODE": "installed",
        "EXPC_WLK_INSTALL_ROOT": str(INSTALL_ROOT),
        "EXPC_WLK_METADATA_ROOT": str(METADATA_ROOT),
        "EXPC_WLK_MODEL_ROOT": str(models),
        "EXPC_WLK_LAUNCHER": str(launcher),
        "EXPC_WLK_RESTART_EVENT": r"Local\WhisperKeyInstalledRestart",
        "HF_HOME": str(user_data / "cache" / "huggingface"),
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
    })

    ca_bundle = INSTALL_ROOT / "app" / "site-packages" / "certifi" / "cacert.pem"
    if not ca_bundle.is_file():
        raise FileNotFoundError("Bundled CA certificate store is missing: " + str(ca_bundle))
    os.environ["SSL_CERT_FILE"] = str(ca_bundle)
    os.environ.pop("SSL_CERT_DIR", None)
    for folder in (runtime, native,
                   INSTALL_ROOT / "app" / "site-packages" / "pywin32_system32",
                   INSTALL_ROOT / "app" / "site-packages" / "ctranslate2"):
        if folder.is_dir():
            DLL_HANDLES.append(os.add_dll_directory(str(folder)))
    import pywin32_bootstrap  # noqa: F401

    models.mkdir(parents=True, exist_ok=True)
    user_data.mkdir(parents=True, exist_ok=True)
    if sys.stdout is None or sys.stderr is None:
        CONSOLE_STREAM = (user_data / "installed-console.log").open(
            "a", encoding="utf-8", buffering=1
        )
        if sys.stdout is None:
            sys.stdout = CONSOLE_STREAM
        if sys.stderr is None:
            sys.stderr = CONSOLE_STREAM
    return models, user_data


def prepare_app(ready_handshake=None):
    from whisper_key import installed_updater, main, portable_updater
    from whisper_key.model_registry import ModelRegistry

    models = model_root()
    original_cached = ModelRegistry.is_model_cached
    local_models = {"small", "large-v3-turbo"}

    def model_source(self, key):
        if key in local_models:
            from whisper_key import model_import, model_store, tray_i18n, tray_popup
            verified = model_store.verify_local_model(
                METADATA_ROOT, key, model_root=models)
            if verified["status"] == "valid":
                return str(models / model_store.manifest_for(METADATA_ROOT, key)["directory"])
            language = tray_i18n.startup_language()
            while True:
                choice = tray_popup.choose(
                    tray_i18n.text("first_run_model", language).format(model=key),
                    [tray_i18n.text("use_existing_model", language),
                     tray_i18n.text("download", language),
                     tray_i18n.text("cancel", language)],
                )
                if choice == 0:
                    source = model_import.choose_folder(
                        tray_i18n.text("import_select_folder", language))
                    if source is None:
                        continue
                    try:
                        result = model_import.import_selected(
                            METADATA_ROOT, models, source, preferred_model=key,
                            require_preferred=True)
                        return str(result["path"])
                    except model_import.ModelImportError as error:
                        tray_popup.choose(
                            tray_i18n.text("import_failed", language).format(error=error),
                            ["OK"])
                        continue
                if choice == 1:
                    return str(model_store.ensure_model(
                        METADATA_ROOT, key, consent=lambda manifest, files: True,
                        model_root=models))
                raise RuntimeError("Model setup cancelled / Настройка модели отменена.")
        raise ValueError("Unsupported installed model: " + str(key))

    def model_cached(self, key):
        if key in local_models:
            from whisper_key.model_store import manifest_for, valid_file
            manifest = manifest_for(METADATA_ROOT, key)
            target = models / manifest["directory"]
            return all(valid_file(target / item["name"], item) for item in manifest["files"])
        return original_cached(self, key)

    def gpu_check(config_manager, config):
        mode = config_manager.config.get("hardware", {}).get("mode", "auto")
        if mode not in ("auto", "cpu", "cuda"):
            mode = "auto"
        if package_variant() == "cpu":
            mode = "cpu"

        cuda_available = False
        if mode != "cpu":
            from whisper_key.cuda_guard import probe
            cuda_available, _ = probe(METADATA_ROOT)
        if mode == "cuda" and not cuda_available:
            from whisper_key import tray_i18n, tray_popup
            from whisper_key.model_store import model_status
            language = tray_i18n.startup_language()
            small_ready = model_status(
                METADATA_ROOT, "small", verify_hashes=True, model_root=models
            ) == "valid"
            first = tray_i18n.text(
                "switch_small" if small_ready else "install_small", language)
            choice = tray_popup.choose(
                tray_i18n.text("cuda_unavailable", language),
                [first, tray_i18n.text("cancel", language)])
            if choice != 0:
                raise RuntimeError(tray_i18n.text("cuda_unavailable", language))
            mode = "cpu"
            update_setting = getattr(config_manager, "update_user_setting", None)
            if callable(update_setting):
                update_setting("hardware", "mode", "cpu")
            config_manager.config.setdefault("hardware", {})["mode"] = "cpu"

        use_cuda = mode == "cuda" or (mode == "auto" and cuda_available)
        config["device"] = "cuda" if use_cuda else "cpu"
        config["compute_type"] = "float16" if use_cuda else "int8"
        config["model"] = "large-v3-turbo" if use_cuda else "small"
        for key, model in config.get("models", {}).items():
            if isinstance(model, dict):
                model["enabled"] = key in local_models
        config_manager.config["whisper"]["device"] = config["device"]
        config_manager.config["whisper"]["compute_type"] = config["compute_type"]
        config_manager.config["whisper"]["model"] = config["model"]
        config_manager.config["_hardware_backend"] = (
            "NVIDIA CUDA (FP16)" if use_cuda else "CPU (INT8)"
        )
        config_manager.config["_cpu_fallback"] = mode == "auto" and not cuda_available
        config_manager.config["_cpu_notice"] = not use_cuda
        return config

    def gpu_failure(error, whisper_config, vad_manager, model_registry, config_manager):
        mode = config_manager.config.get("hardware", {}).get("mode", "auto")
        if mode == "auto":
            config_manager.config["_cpu_fallback"] = True
            config_manager.config["_cpu_notice"] = True
            config_manager.config["_hardware_backend"] = "CPU (INT8)"
            whisper_config.update(device="cpu", compute_type="int8", model="small")
            config_manager.config["whisper"].update(
                device="cpu", compute_type="int8", model="small"
            )
            return main.setup_whisper_engine(
                whisper_config, vad_manager, model_registry, config_manager
            )
        raise RuntimeError("CUDA model initialization failed. Check NVIDIA driver, GPU memory "
                           "and installed native DLLs. " + str(error)) from error

    ModelRegistry.get_source = model_source
    ModelRegistry.is_model_cached = model_cached
    main.run_gpu_onboarding = gpu_check
    main._handle_gpu_failure = gpu_failure
    main.check_for_updates = lambda *args, **kwargs: None
    portable_updater.check_latest = installed_updater.check_latest
    portable_updater.offer_update = installed_updater.offer_update
    portable_updater.mark_ready = installed_updater.mark_ready
    if ready_handshake is not None:
        installed_updater.configure_ready(*ready_handshake, user_data=user_data_root())
    return main


def selftest():
    models, user_data = configure()
    from whisper_key import diagnostics, model_store, portable_tray_actions, utils
    import ctranslate2

    checks = {
        "mode": os.environ["EXPC_WLK_MODE"],
        "variant": package_variant(),
        "version": utils.get_version(),
        "launcher": str(portable_tray_actions.launcher_path()),
        "models": str(models),
        "settings": str(user_data),
        "small_status": model_store.model_status(
            METADATA_ROOT, "small", model_root=models
        ),
        "large_status": model_store.model_status(
            METADATA_ROOT, "large-v3-turbo", model_root=models
        ),
        "cuda_devices": ctranslate2.get_cuda_device_count(),
        "cuda_fp16": "float16" in ctranslate2.get_supported_compute_types("cuda")
        if ctranslate2.get_cuda_device_count() else False,
        "diagnostics_mode": diagnostics.collect(root=INSTALL_ROOT)["mode"],
    }
    print(json.dumps(checks, ensure_ascii=False))
    return 0


def run():
    ready_handshake = consume_ready_handshake()
    configure()
    tray_ui = None
    try:
        app = prepare_app(ready_handshake)
        from whisper_key import system_tray as tray_ui
        tray_ui.show_startup_status("initializing")
        print("INSTALLED_START executable=" + sys.executable, flush=True)
        app.main()
    except Exception as exc:  # noqa: BLE001
        import traceback
        details = traceback.format_exc()
        print(details, file=sys.stderr)
        if tray_ui is not None:
            tray_ui.show_startup_status("unavailable")
        log_path = user_data_root() / "whisper-key.log"
        try:
            (user_data_root() / "installed-startup-error.log").write_text(
                details, encoding="utf-8"
            )
        except OSError:
            pass
        ctypes.windll.user32.MessageBoxW(
            None, str(exc) + "\n\nSee " + str(log_path), "EXPC-WLK startup failed", 0x10
        )
        return 1
    finally:
        if tray_ui is not None:
            tray_ui.close_startup_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else run())
