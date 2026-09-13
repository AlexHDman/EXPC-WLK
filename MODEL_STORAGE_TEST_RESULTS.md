# EXPC-WLK v0.9.2 model storage test results

Date: 2026-09-13

Status: PASS. Release candidate only; not published.

## Implementation

- Supported models: `small`, `large-v3-turbo`.
- Production sources use public HTTPS Hugging Face repositories and exact
  40-character commit revisions from `WhisperKey/config/model-catalog.json`.
- Every required file has an exact byte count and SHA-256.
- Downloads use a same-volume staging directory. The verified complete snapshot
  is atomically installed into `WhisperKey/models/<model-id>`.
- Runtime model sources resolve only to the installed local directory.
- Each model has `.installed-model.json` containing its source, revision,
  compatibility metadata and deterministic manifest hash.
- CPU/fallback selects `small`; NVIDIA CUDA FP16 selects `large-v3-turbo`.

## Test matrix

| Test | Result |
|---|---|
| Fresh `small` download from pinned Hugging Face commit | PASS |
| Fresh `large-v3-turbo` download from pinned Hugging Face commit | PASS |
| Required-file size and SHA-256 validation | PASS |
| Interrupted download cleanup | PASS |
| Corrupt installed-file detection | PASS |
| Failed repair leaves previous target untouched | PASS |
| Atomic swap failure restores previous directory | PASS |
| Existing valid model reused with network forbidden | PASS |
| Restart with `HF_HUB_OFFLINE=1` | PASS |
| Reuse with a nonexistent `HF_HOME` cache path | PASS |
| Complete portable folder moved to a new path | PASS |
| Moved portable starts offline with local `small` on CPU INT8 | PASS |
| Local `small` CPU transcription | PASS (`Hello.`) |
| Local `large-v3-turbo` CUDA FP16 transcription | PASS (`Hello`) |
| Dynamic Vocabulary OFF and ON on CPU and CUDA | PASS |
| App update success preserves model files and installed metadata | PASS |
| App update rollback preserves model files and installed metadata | PASS |
| Tray download progress on startup and runtime model selection | PASS |
| Tray, RU/EN UI, autostart, updater regressions | PASS |
| Bundled runtime isolation; no foreign Python paths | PASS |
| Release ZIP checksum, CRC, path/privacy scan | PASS |

## Portable artifact

- File: `dist/0.9.2/application/EXPC-WLK-portable-v0.9.2.zip`
- Size: 1,331,724,760 bytes
- SHA-256: `7b72b2e791bba5ce330830e0cc0dc919f6586b24c44321d4e891a7f7dd1c82d7`
- Launcher version: `0.9.2.0`
- Model files bundled: none

## Separate model assets

- `EXPC-WLK-model-small.zip`: 486,213,429 bytes; SHA-256
  `49b7072f98ce737e8264fa8349e177d06b942e91ed06b2c02badb2a9c943b91f`
- `EXPC-WLK-model-large-v3-turbo.zip`: 1,621,667,327 bytes; SHA-256
  `909a8c1cb12454e1c2b1df54c5cf5556e2493b2f279f2eae50d40e0378fe3027`

Both model assets contain only `models/<model-id>` files and installed metadata.
Both passed full pinned-file SHA-256, CRC and layout verification.

The test does not publish, tag, commit, or create a GitHub Release.
