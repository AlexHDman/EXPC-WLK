# EXPC-WLK v0.9.6 test release

Status: local test-release candidate; not published, committed, pushed, tagged, or released.

## Changes

- Fixed pystray model Verify, Remove, and Download callback signatures.
- Ensured model-loading UI state exits on success, failure, cancellation, timeout, callback error, and synchronous no-op.
- Kept `small` and `large-v3-turbo` in separate pinned, SHA-256 verified local model directories with staging, atomic replacement, and offline reuse.
- Displayed the canonical version from `WhisperKey/config/release.json` instead of stale bundled package metadata.
- Added per-stage startup timings and a separate STT-only latency measurement.

## Local validation

- Python tests: tray/menu 13, model-loading exits 2, model store 9, hardware fallback 6, localization/updater 12, diagnostics 1.
- Native updater: 3 scenarios passed, including rollback and preservation of logs/models.
- Autostart: 16 live HKCU checks passed; original registry values restored.
- CPU benchmark (`small`, INT8): 2.198 s transcription for the bundled 0.450 s fixture.
- CUDA benchmark (`large-v3-turbo`, FP16): 23.169 s transcription for the bundled 0.450 s fixture.
- CPU and CUDA ZIP structure, internal CRCs, exclusion rules, version metadata, package profiles, and SHA-256 checks passed.

The short bundled sound is a smoke-test fixture, not an accuracy or representative performance benchmark. Physical microphone/hotkey/clipboard use and clean-machine launch still require manual validation.

## Artifacts

- `EXPC-WLK-portable-CPU-v0.9.6.zip` — SHA-256 `a99e576c69e08821a740756df32a6a48705b8c15b410640fc65fe8c92ed18e42`
- `EXPC-WLK-portable-CUDA-v0.9.6.zip` — SHA-256 `f2207b92518e9ed17a802060c3fb34ee476213f4adbc6cf2f96c4cdf0e15d0b6`
