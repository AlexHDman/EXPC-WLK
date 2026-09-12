# Changelog

EXPC-WLK uses semantic versioning. The canonical portable version is stored in
`WhisperKey/config/release.json`.

## [Unreleased]

- Added the source-repository baseline and release-asset packaging policy.

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

[Unreleased]: https://github.com/AlexHDman/EXPC-WLK/compare/v0.8.2...HEAD
[0.8.2]: https://github.com/AlexHDman/EXPC-WLK/releases/tag/v0.8.2
