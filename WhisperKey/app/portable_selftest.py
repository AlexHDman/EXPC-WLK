"""Offline inference and isolation checks using only the adjacent runtime."""
import ctypes
import hashlib
import json
import sys
from pathlib import Path

from portable_boot import ROOT, configure, prepare_app


def modules():
    psapi = ctypes.WinDLL('psapi')
    kernel = ctypes.WinDLL('kernel32')
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    handles = (ctypes.c_void_p * 2048)()
    needed = ctypes.c_ulong()
    process = kernel.GetCurrentProcess()
    psapi.EnumProcessModules.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong,
                                        ctypes.POINTER(ctypes.c_ulong)]
    psapi.GetModuleFileNameExW.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_wchar_p, ctypes.c_ulong]
    if not psapi.EnumProcessModules(process, handles, ctypes.sizeof(handles), ctypes.byref(needed)):
        raise ctypes.WinError()
    paths = []
    for handle in handles[:needed.value // ctypes.sizeof(ctypes.c_void_p)]:
        buffer = ctypes.create_unicode_buffer(32768)
        psapi.GetModuleFileNameExW(process, handle, buffer, len(buffer))
        paths.append(buffer.value)
    return paths


def run():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    configure()
    app = prepare_app()
    from faster_whisper.audio import decode_audio
    from whisper_key.config_manager import ConfigManager
    from whisper_key.model_registry import ModelRegistry

    config = ConfigManager()
    whisper = config.get_whisper_config()
    app.run_gpu_onboarding(config, whisper)
    registry = ModelRegistry(whisper.get('models', {}))
    engine = app.setup_whisper_engine(whisper, None, registry, config)
    processor = app.setup_text_postprocessor(config.get_post_processing_config())
    audio_path = ROOT / 'app/site-packages/whisper_key/assets/sounds/streaming-recognizer-warmup.wav'
    audio = decode_audio(str(audio_path), sampling_rate=16000)
    results = []
    for enabled in (False, True):
        engine.dynamic_vocabulary_config = {
            'enabled': enabled, 'project_directory': str(ROOT),
            'database_path': str(ROOT / 'logs/selftest-vocabulary.db'),
        }
        engine.dynamic_vocabulary_manager = None
        text = engine.transcribe_audio(audio.copy())
        assert text, 'No transcription from bundled speech sample'
        manager = engine.dynamic_vocabulary_manager
        dynamic = manager.last_report if manager else {}
        assert not dynamic.get('error'), dynamic
        results.append({'dynamic_enabled': enabled, 'text': text,
                        'corrected': processor.process(text),
                        'candidate_count': dynamic.get('candidate_count'),
                        'selected_count': len(dynamic.get('selected_hotwords', []))})
    loaded = modules()
    import os
    windows = str(Path(os.environ['WINDIR']).resolve()).casefold() + '\\'
    local = str(ROOT.resolve()).casefold() + '\\'
    outside = [p for p in loaded if p and not p.casefold().startswith((windows, local))]
    # Host-wide keyboard/security/signing providers, not application imports.
    injected = [p for p in outside if any(part in p.casefold() for part in (
        '\\punto switcher\\', '\\windows defender\\platform\\', '\\crypto pro\\'))]
    foreign = [p for p in outside if p not in injected]
    paths = [p for p in sys.path if p and not str(Path(p).resolve()).casefold().startswith(local)]
    report = {'executable': sys.executable, 'prefix': sys.prefix,
              'isolated': sys.flags.isolated, 'site_initialization_disabled': sys.flags.no_site,
              'user_site_disabled': sys.flags.no_user_site,
              'model': registry.get_source(whisper['model']), 'device': engine.device,
              'audio_sha256': hashlib.sha256(audio.tobytes()).hexdigest(),
              'runs': results, 'correction_variants': len(processor.replacements),
              'foreign_modules': foreign, 'foreign_python_paths': paths,
              'host_injected_modules': injected, 'loaded_modules': loaded}
    report['pass'] = not foreign and not paths and bool(sys.flags.isolated) and bool(sys.flags.no_site)
    (ROOT / 'logs/selftest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'loaded_modules'}, ensure_ascii=True))
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(run())
