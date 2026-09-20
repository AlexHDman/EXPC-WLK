# Changelog

EXPC-WLK uses semantic versioning. The canonical portable version is stored in
`WhisperKey/config/release.json`.

## [1.0.1] - Release candidate

- Added clear backend/model tray status and CPU performance guidance.
- Added local model Download, Select, Verify, and Remove controls.
- Added privacy-safe diagnostics and a reproducible CPU/CUDA benchmark tool.
- Embedded the existing multi-size product icon and VERSIONINFO in launcher/updater builds.
- Added Authenticode signing-ready documentation and script without credentials.
- Added verified adoption and offline reuse of compatible copied models.
- Added pinned SHA-256 model verification and clearer model/update popups.
- Added CUDA guard with CPU/small fallback for unsupported systems.
- Added the fixed-audio STT performance benchmark to the tray menu.
- Stabilized installed-mode paths and the deterministic updater Ready handshake.

## [1.0.0] - Release candidate

- Added a bundled CA certificate path for portable HTTPS model/update checks.
- Completed CPU/CUDA, Dynamic Vocabulary, updater, tray, and portable regression coverage.
- Polished concise Russian and English installation, hardware, warning, and update guidance.

## [0.9.6] - 2026-09-16

- Fixed pystray model-menu callbacks and deterministic model-loading status exits.
- Read the displayed version from canonical portable release metadata.
- Added startup-stage timings and separate STT latency reporting.
- Preserved verified pinned model downloads, atomic installation, and offline reuse.

## [0.9.2]

- Added pinned local installation for `small` and `large-v3-turbo` models.
- Model snapshots now download into staging, verify every required file, and
  install atomically without depending on Hugging Face cache.
- CPU/fallback prefers `small`; NVIDIA CUDA FP16 prefers `large-v3-turbo`.
- Added installed-model metadata plus offline, interruption, corruption, move,
  application update and rollback coverage.

## [0.9.1]

- Added automatic CPU INT8 fallback when NVIDIA CUDA is unavailable.
- Added `hardware.mode` with `auto`, `cpu`, and `cuda` options.
- Added the active transcription backend to the tray status.

## [0.9.0]

- First portable release for Windows x64, with bundled Python and CUDA/cuDNN.
- Separated large-v3-turbo from the release ZIP: pinned Hugging Face source,
  revision, SHA-256 and verified first-run download; existing models are reused.
- Application updates preserve the installed model manifest and model files.
- Added a repeatable full/update ZIP builder and SHA-256 checksums.
- Preserved the tested STT, Dynamic Vocabulary R1, RU/EN tray and autostart.
- The first real 0.9.0 to 0.9.1 update will be tested after laptop acceptance.

## [0.8.2] - 2026-09-12

- Built a self-contained Windows portable package with a private Python runtime,
  CUDA dependencies, and included `large-v3-turbo` model.
- Integrated Dynamic Vocabulary R1 behind a default-OFF feature flag, with up to
  30 dynamic hotwords and failure-safe fallback.
- Added tray status indication, RU/EN localization, HKCU autostart controls,
  restart, application-folder action, and duplicate-instance handling.
- Prepared manual GitHub Releases updates with semantic version comparison,
  official asset selection, SHA-256 verification, staged replacement, startup
  confirmation, and rollback.

[Unreleased]: https://github.com/AlexHDman/EXPC-WLK/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/AlexHDman/EXPC-WLK/releases/tag/v0.9.0
[0.8.2]: https://github.com/AlexHDman/EXPC-WLK/releases/tag/v0.8.2
