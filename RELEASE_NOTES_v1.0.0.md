# EXPC-WLK v1.0.0

Status: public stable release. CPU and CUDA application packages remain model-free.

## Scope

- Portable Windows CPU package using `small` with CPU INT8.
- Portable Windows CUDA package using `large-v3-turbo` with NVIDIA CUDA FP16.
- Separate pinned model assets with SHA-256 verification, staging, atomic installation, offline reuse, and safe updater preservation.
- RU/EN tray, hotkeys, clipboard/paste, Dynamic Vocabulary OFF/ON, autostart, diagnostics, and updater rollback retained from v0.9.6.
- Bundled CA certificate store is selected explicitly for portable HTTPS model and update checks.

## Validation

- Clean CPU/CUDA extraction and package layout verification.
- Physical CPU and CUDA transcription with the bundled smoke-test fixture.
- Dynamic Vocabulary OFF/ON in both extracted portable runtimes.
- Model download, corruption, interruption, offline reuse, move, and atomic rollback fixtures.
- Tray RU/EN, model actions, hotkeys, clipboard/paste, no-microphone error, duplicate-instance guard, autostart, updater rollback, diagnostics, icons, VERSIONINFO, privacy, CRC, and SHA-256 checks.

The bundled audio fixture is a smoke test, not a representative accuracy or throughput benchmark.

These builds are unsigned. Windows SmartScreen may show an unknown-publisher warning. Verify the matching SHA-256 file and download only from the official GitHub release.
