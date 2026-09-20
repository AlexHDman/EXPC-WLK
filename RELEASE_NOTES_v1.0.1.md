# EXPC-WLK v1.0.1

Maintenance release for the portable CPU/CUDA packages and Windows installers.

## Changes

- Existing compatible models can be copied between portable and installed builds and reused without another download.
- Local model files are verified against the pinned project manifest using sizes and SHA-256 hashes; missing metadata is recreated after successful verification.
- CUDA builds validate NVIDIA/CUDA availability before using `large-v3-turbo` and offer the CPU `small` fallback when needed.
- Update checks, model checks, errors, and real download progress use compact RU/EN popups.
- A fixed 8.36-second WAV benchmark reports model, backend, CPU/GPU, inference time, and RTF without using the microphone.
- Portable and installed paths, model preservation, rollback, and the deterministic installed Ready handshake remain supported.

## Notes

- Models remain separate from application packages and installers.
- Builds are unsigned. Windows SmartScreen may show a warning on first launch.
- The installer preserves user settings and downloaded models during upgrades.
