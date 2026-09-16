# EXPC-WLK regression matrix

Date: 2026-09-16

| # | Scenario | Result |
|---:|---|---|
| 1 | CUDA AUTO | PASS |
| 2 | CPU AUTO | PASS |
| 3 | Forced CPU | PASS |
| 4 | Forced CUDA available | PASS |
| 5 | Forced CUDA unavailable | PASS |
| 6 | small installed | PASS |
| 7 | large-v3-turbo installed | PASS |
| 8 | Selected model missing | PASS |
| 9 | Corrupt model | PASS |
| 10 | Interrupted download | PASS |
| 11 | Offline launch / HF_HUB_OFFLINE=1 | PASS |
| 12 | Moved portable directory | PASS |
| 13 | Duplicate process prevention | PASS |
| 14 | RU tray | PASS |
| 15 | EN tray | PASS |
| 16 | Hotkey | PASS |
| 17 | Clipboard paste | PASS |
| 18 | Corrections | PASS |
| 19 | Dynamic Vocabulary OFF | PASS |
| 20 | Dynamic Vocabulary ON | PASS |
| 21 | Updater preserves models | PASS |
| 22 | Rollback preserves models | PASS |
| 23 | Autostart path after move | PASS |
| 24 | Diagnostics privacy | PASS |
| 25 | Model-free application package | PASS |
| 26 | No-microphone error path | PASS |
| 27 | Bundled TLS CA / Hugging Face HTTPS | PASS |
| 28 | ZIP CRC/layout/SHA-256 | PASS |
| 29 | Icon and VERSIONINFO 1.0.0.0 | PASS |
| 30 | Optional signing guard / no credentials | PASS |

Automated coverage is in `WhisperKey/config/test_*.py`, `verify_release.py`,
`verify_model_assets.py`, and `portable_selftest.py`. CPU/CUDA transcription and
Dynamic Vocabulary OFF/ON were rerun from clean extracted v1.0.0 candidates with
separate verified model assets. Hotkey, clipboard/paste, microphone failure and
duplicate-instance paths have controlled regressions; OS mutex, autostart and
native updater rollback were also exercised.
