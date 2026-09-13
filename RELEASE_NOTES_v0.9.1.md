# EXPC-WLK v0.9.1

## English

- Added `hardware.mode`: `auto`, `cpu`, or `cuda`.
- AUTO prefers NVIDIA CUDA with FP16 inference.
- AUTO falls back automatically to CPU with INT8 inference when CUDA is unavailable.
- EXPC-WLK no longer refuses to start on systems without NVIDIA CUDA when AUTO is selected.
- The tray status shows the active inference backend: `NVIDIA CUDA (FP16)` or `CPU (INT8)`.
- Existing STT behavior, Dynamic Vocabulary R1, updater compatibility, and user data remain unchanged.

The versioned ZIP is the portable package for manual installation. The fixed-name
`EXPC-WLK-portable.zip` asset is the identical v0.9.1 application payload used by
the existing updater. The Whisper model remains separate and pinned by revision
and SHA-256.

## Русский

- Добавлен `hardware.mode`: `auto`, `cpu` или `cuda`.
- AUTO предпочитает NVIDIA CUDA с вычислениями FP16.
- Если CUDA недоступна, AUTO автоматически использует CPU с вычислениями INT8.
- В режиме AUTO EXPC-WLK больше не отказывается запускаться на системах без NVIDIA CUDA.
- В трее отображается активный backend: `NVIDIA CUDA (FP16)` или `CPU (INT8)`.
- Существующие STT, Dynamic Vocabulary R1, updater и пользовательские данные остаются совместимыми.

Versioned ZIP предназначен для ручной portable-установки. Fixed-name файл
`EXPC-WLK-portable.zip` содержит тот же код v0.9.1 и используется существующим
updater. Модель Whisper остаётся отдельной и закреплена по revision и SHA-256.
