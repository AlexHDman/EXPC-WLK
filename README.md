<p align="center">
  <img src="assets/github-header.png" width="100%" alt="WhisperKey WLK">
</p>
# EXPC-WLK

English | [╨а╤Г╤Б╤Б╨║╨╕╨╣](#╤А╤Г╤Б╤Б╨║╨╕╨╣)

> **RU:** EXPC-WLK ╤А╨░╨▒╨╛╤В╨░╨╡╤В ╨╜╨░ CPU, ╨╜╨╛ ╨┤╨╗╤П ╨║╨╛╨╝╤Д╨╛╤А╤В╨╜╨╛╨╣ ╤А╨░╨▒╨╛╤В╤Л ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╤В╤Б╤П NVIDIA GPU ╤Б CUDA. CPU-╤А╨╡╨╢╨╕╨╝ ╨╝╨╛╨╢╨╡╤В ╨▒╤Л╤В╤М ╨╖╨╜╨░╤З╨╕╤В╨╡╨╗╤М╨╜╨╛ ╨╝╨╡╨┤╨╗╨╡╨╜╨╜╨╡╨╡.
>
> **EN:** EXPC-WLK works on CPU, but an NVIDIA GPU with CUDA is recommended for comfortable use. CPU mode can be significantly slower.

## English

EXPC-WLK is portable local speech-to-text for Windows based on Whisper and
faster-whisper. It provides fast dictation from any application while keeping
speech processing on the local computer.

### Features

- Local STT with pinned `small` and `large-v3-turbo` CTranslate2 models.
- Automatic NVIDIA CUDA FP16 acceleration with CPU INT8 fallback.
- Mixed Russian-English speech and English technical-term preservation.
- Dynamic Vocabulary R1, disabled by default, plus permanent hotwords and corrections.
- Russian and English tray interface, status indicator, and optional user autostart.
- Self-contained portable runtime; no separate Python, venv, or `pip install` is required.
- Separately downloaded CTranslate2 model, pinned to an immutable revision and SHA-256.
- Manual GitHub Releases updates with SHA-256 verification, safe staging, and rollback.

### System requirements

- Windows 10/11 x64, Windows UCRT, and .NET Framework 4.x.
- An NVIDIA GPU and compatible driver are optional. `hardware.mode: auto` uses
  CUDA FP16 when available and otherwise starts on CPU INT8.
- Microphone and Windows microphone permission.

The NVIDIA driver is required only for GPU acceleration. Python, the CUDA Toolkit, and
development tools are not required on the target PC.

| Package | Model | Backend | Choose it when |
|---|---|---|---|
| CPU | `small` | CPU INT8 | No compatible NVIDIA GPU, or maximum portability matters |
| CUDA | `large-v3-turbo` | NVIDIA CUDA FP16 | A compatible NVIDIA GPU and current driver are available |

The CPU ZIP excludes CUDA/cuDNN. The CUDA ZIP includes its native runtime; only
the NVIDIA driver is required separately. CPU transcription can be substantially
slower than realtime on older processors.

### Portable usage

### Downloads

- [Download CPU/CUDA application](https://github.com/AlexHDman/EXPC-WLK/releases)
- [Download small model](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-small.zip) тАФ recommended for CPU
- [Download large-v3-turbo model](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-large-v3-turbo.zip) тАФ recommended for NVIDIA CUDA

These published v0.9.2 model ZIPs are optional:
extract one into the application's `WhisperKey` directory so its `models` folder
merges there. If the selected model is absent, EXPC-WLK instead offers to download
the pinned snapshot from Hugging Face, verifies it, and installs it atomically.

Download the complete package from GitHub Releases, extract it to a writable
folder such as `D:\Portable\EXPC-WLK`, and run `EXPC-WLK.exe`. Keep the adjacent
`WhisperKey` folder intact. On first use, accept the requested model download
from its pinned Hugging Face revision. CPU/fallback prefers `small`; CUDA prefers
`large-v3-turbo`. A complete snapshot is verified and atomically installed under
`WhisperKey/models/<model-id>`. Existing verified models are reused without cache access.
After this one-time download, dictation needs no internet. The app runs in the
tray and prevents duplicate instances.

The tray shows the active backend and model. The model menu provides Download,
Select, Verify, and Remove actions. Application updates preserve `WhisperKey/models`.
Development builds are unsigned and Windows SmartScreen may display a warning;
verify the adjacent SHA-256 file and download only from the official repository.
The optional production-signing process is documented in `docs/CODE_SIGNING.md`.
If no microphone is available, startup reports an input-device error; check the
Windows microphone privacy permission and the selected sound input.

This source repository intentionally excludes the Python runtime, third-party
binary dependencies, CUDA/cuDNN libraries, built EXEs, and model. Those large
runtime artifacts belong in the portable ZIP attached to a GitHub Release.
The model is distributed separately from its pinned Hugging Face source.

### User data

User settings and local data remain outside the application folder:

```text
%APPDATA%\whisperkey\user_settings.yaml
%APPDATA%\whisperkey\commands.yaml
%APPDATA%\whisperkey\vocabulary.db
```

Updates never overwrite these files. UI language is stored in
`system_tray.language` without changing vocabulary, hotwords, or corrections.

### Updates

Checks are manual and do not block startup or STT. Only the configured official
repository, stable semantic version, exact release asset, and GitHub SHA-256
digest are accepted. A separate helper stages a complete app, temporarily keeps
the previous version, confirms the updated app reaches Ready, and rolls back on
failure. Model directories and installed metadata are preserved independently of
application updates. See [UPDATING.md](UPDATING.md).

## ╨а╤Г╤Б╤Б╨║╨╕╨╣

EXPC-WLK тАФ ╨┐╨╛╤А╤В╨░╤В╨╕╨▓╨╜╨░╤П ╨╗╨╛╨║╨░╨╗╤М╨╜╨░╤П ╤Б╨╕╤Б╤В╨╡╨╝╨░ ╨┐╤А╨╡╨╛╨▒╤А╨░╨╖╨╛╨▓╨░╨╜╨╕╤П ╤А╨╡╤З╨╕ ╨▓ ╤В╨╡╨║╤Б╤В ╨┤╨╗╤П Windows
╨╜╨░ ╨▒╨░╨╖╨╡ Whisper ╨╕ faster-whisper. ╨Ю╨╜╨░ ╨╛╨▒╨╡╤Б╨┐╨╡╤З╨╕╨▓╨░╨╡╤В ╨▒╤Л╤Б╤В╤А╤Г╤О ╨┤╨╕╨║╤В╨╛╨▓╨║╤Г ╨▓ ╨╗╤О╨▒╨╛╨╝
╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╕ ╤Б ╨╛╨▒╤А╨░╨▒╨╛╤В╨║╨╛╨╣ ╤А╨╡╤З╨╕ ╨╜╨░ ╨║╨╛╨╝╨┐╤М╤О╤В╨╡╤А╨╡ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П.

### ╨Т╨╛╨╖╨╝╨╛╨╢╨╜╨╛╤Б╤В╨╕

- ╨Ы╨╛╨║╨░╨╗╤М╨╜╨╛╨╡ STT ╤Б ╨╖╨░╨║╤А╨╡╨┐╨╗╤С╨╜╨╜╤Л╨╝╨╕ CTranslate2-╨╝╨╛╨┤╨╡╨╗╤П╨╝╨╕ `small` ╨╕ `large-v3-turbo`.
- ╨Р╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╛╨╡ ╤Г╤Б╨║╨╛╤А╨╡╨╜╨╕╨╡ NVIDIA CUDA FP16 ╤Б ╨┐╨╡╤А╨╡╤Е╨╛╨┤╨╛╨╝ ╨╜╨░ CPU INT8.
- ╨б╨╝╨╡╤И╨░╨╜╨╜╨░╤П ╤А╤Г╤Б╤Б╨║╨╛-╨░╨╜╨│╨╗╨╕╨╣╤Б╨║╨░╤П ╤А╨╡╤З╤М ╨╕ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡ ╨░╨╜╨│╨╗╨╕╨╣╤Б╨║╨╕╤Е ╤В╨╡╤Е╨╜╨╕╤З╨╡╤Б╨║╨╕╤Е ╤В╨╡╤А╨╝╨╕╨╜╨╛╨▓.
- Dynamic Vocabulary R1, ╨▓╤Л╨║╨╗╤О╤З╨╡╨╜╨╜╤Л╨╣ ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О, ╨┐╨╛╤Б╤В╨╛╤П╨╜╨╜╤Л╨╡ hotwords ╨╕ corrections.
- ╨а╤Г╤Б╤Б╨║╨╕╨╣ ╨╕ ╨░╨╜╨│╨╗╨╕╨╣╤Б╨║╨╕╨╣ ╨╕╨╜╤В╨╡╤А╤Д╨╡╨╣╤Б ╤В╤А╨╡╤П, ╨╕╨╜╨┤╨╕╨║╨░╤В╨╛╤А ╤Б╤В╨░╤В╤Г╤Б╨░ ╨╕ ╨░╨▓╤В╨╛╨╖╨░╨┐╤Г╤Б╨║ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П.
- ╨б╨░╨╝╨╛╨┤╨╛╤Б╤В╨░╤В╨╛╤З╨╜╤Л╨╣ portable runtime: ╨╛╤В╨┤╨╡╨╗╤М╨╜╤Л╨╣ Python, venv ╨╕ `pip install` ╨╜╨╡ ╨╜╤Г╨╢╨╜╤Л.
- ╨Ю╤В╨┤╨╡╨╗╤М╨╜╨░╤П CTranslate2-╨╝╨╛╨┤╨╡╨╗╤М ╤Б ╨╖╨░╨║╤А╨╡╨┐╨╗╤С╨╜╨╜╤Л╨╝╨╕ revision ╨╕ SHA-256.
- ╨а╤Г╤З╨╜╨╛╨╡ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡ ╤З╨╡╤А╨╡╨╖ GitHub Releases ╤Б SHA-256, staging ╨╕ ╨╛╤В╨║╨░╤В╨╛╨╝.

### ╨б╨╕╤Б╤В╨╡╨╝╨╜╤Л╨╡ ╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╤П

- Windows 10/11 x64, Windows UCRT ╨╕ .NET Framework 4.x.
- ╨Т╨╕╨┤╨╡╨╛╨║╨░╤А╤В╨░ NVIDIA ╨╕ ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╤Л╨╣ ╨┤╤А╨░╨╣╨▓╨╡╤А ╨╜╨╡╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л. ╨а╨╡╨╢╨╕╨╝
  `hardware.mode: auto` ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В CUDA FP16 ╨┐╤А╨╕ ╨╜╨░╨╗╨╕╤З╨╕╨╕ ╨╕ ╨╕╨╜╨░╤З╨╡ ╨╖╨░╨┐╤Г╤Б╨║╨░╨╡╤В CPU INT8.
- ╨Ь╨╕╨║╤А╨╛╤Д╨╛╨╜ ╨╕ ╤А╨░╨╖╤А╨╡╤И╨╡╨╜╨╕╨╡ Windows ╨╜╨░ ╨╡╨│╨╛ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╡.

╨Ф╤А╨░╨╣╨▓╨╡╤А NVIDIA ╤В╤А╨╡╨▒╤Г╨╡╤В╤Б╤П ╤В╨╛╨╗╤М╨║╨╛ ╨┤╨╗╤П GPU-╤Г╤Б╨║╨╛╤А╨╡╨╜╨╕╤П. Python, CUDA Toolkit ╨╕ ╤Б╤А╨╡╨┤╤Б╤В╨▓╨░
╤А╨░╨╖╤А╨░╨▒╨╛╤В╨║╨╕ ╨╜╨░ ╤Ж╨╡╨╗╨╡╨▓╨╛╨╝ ╨Я╨Ъ ╨╜╨╡ ╨╜╤Г╨╢╨╜╤Л.

| ╨Я╨░╨║╨╡╤В | ╨Ь╨╛╨┤╨╡╨╗╤М | Backend | ╨Ъ╨╛╨│╨┤╨░ ╨▓╤Л╨▒╨╕╤А╨░╤В╤М |
|---|---|---|---|
| CPU | `small` | CPU INT8 | ╨Э╨╡╤В ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╨╛╨╣ NVIDIA GPU ╨╕╨╗╨╕ ╨▓╨░╨╢╨╜╨░ ╨╝╨░╨║╤Б╨╕╨╝╨░╨╗╤М╨╜╨░╤П ╨┐╨╡╤А╨╡╨╜╨╛╤Б╨╕╨╝╨╛╤Б╤В╤М |
| CUDA | `large-v3-turbo` | NVIDIA CUDA FP16 | ╨Х╤Б╤В╤М ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╨░╤П NVIDIA GPU ╨╕ ╨░╨║╤В╤Г╨░╨╗╤М╨╜╤Л╨╣ ╨┤╤А╨░╨╣╨▓╨╡╤А |

CPU ZIP ╨╜╨╡ ╤Б╨╛╨┤╨╡╤А╨╢╨╕╤В CUDA/cuDNN. CUDA ZIP ╤Б╨╛╨┤╨╡╤А╨╢╨╕╤В ╨╜╨╡╨╛╨▒╤Е╨╛╨┤╨╕╨╝╤Л╨╣ native runtime;
╨╛╤В╨┤╨╡╨╗╤М╨╜╨╛ ╨╜╤Г╨╢╨╡╨╜ ╤В╨╛╨╗╤М╨║╨╛ ╨┤╤А╨░╨╣╨▓╨╡╤А NVIDIA. ╨Э╨░ ╤Б╤В╨░╤А╤Л╤Е CPU ╤А╨░╤Б╨┐╨╛╨╖╨╜╨░╨▓╨░╨╜╨╕╨╡ ╨╝╨╛╨╢╨╡╤В ╨▒╤Л╤В╤М
╨╖╨╜╨░╤З╨╕╤В╨╡╨╗╤М╨╜╨╛ ╨╝╨╡╨┤╨╗╨╡╨╜╨╜╨╡╨╡ ╤А╨╡╨░╨╗╤М╨╜╨╛╨│╨╛ ╨▓╤А╨╡╨╝╨╡╨╜╨╕.

### ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╡ portable-╨▓╨╡╤А╤Б╨╕╨╕

### ╨Ч╨░╨│╤А╤Г╨╖╨║╨╕

- [╨б╨║╨░╤З╨░╤В╤М CPU/CUDA ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╡](https://github.com/AlexHDman/EXPC-WLK/releases)
- [╨б╨║╨░╤З╨░╤В╤М ╨╝╨╛╨┤╨╡╨╗╤М small](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-small.zip) тАФ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╤В╤Б╤П ╨┤╨╗╤П CPU
- [╨б╨║╨░╤З╨░╤В╤М ╨╝╨╛╨┤╨╡╨╗╤М large-v3-turbo](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-large-v3-turbo.zip) тАФ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╤В╤Б╤П ╨┤╨╗╤П NVIDIA CUDA

╨Ю╨┐╤Г╨▒╨╗╨╕╨║╨╛╨▓╨░╨╜╨╜╤Л╨╡ model ZIP v0.9.2 ╨╜╨╡╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л: ╤А╨░╤Б╨┐╨░╨║╤Г╨╣╤В╨╡
╨▓╤Л╨▒╤А╨░╨╜╨╜╤Л╨╣ ╨░╤А╤Е╨╕╨▓ ╨▓ ╨║╨░╤В╨░╨╗╨╛╨│ ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╤П `WhisperKey`, ╨╛╨▒╤К╨╡╨┤╨╕╨╜╨╕╨▓ ╨╡╨│╨╛ ╨┐╨░╨┐╨║╤Г `models`.
╨Х╤Б╨╗╨╕ ╨▓╤Л╨▒╤А╨░╨╜╨╜╨╛╨╣ ╨╝╨╛╨┤╨╡╨╗╨╕ ╨╜╨╡╤В, EXPC-WLK ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╕╤В ╤Б╨║╨░╤З╨░╤В╤М ╨╖╨░╨║╤А╨╡╨┐╨╗╤С╨╜╨╜╤Л╨╣ snapshot ╤Б
Hugging Face, ╨┐╤А╨╛╨▓╨╡╤А╨╕╤В ╨╡╨│╨╛ ╨╕ ╤Г╤Б╤В╨░╨╜╨╛╨▓╨╕╤В ╨░╤В╨╛╨╝╨░╤А╨╜╨╛.

╨б╨║╨░╤З╨░╨╣╤В╨╡ ╨┐╨╛╨╗╨╜╤Л╨╣ ╨┐╨░╨║╨╡╤В ╨╕╨╖ GitHub Releases, ╤А╨░╤Б╨┐╨░╨║╤Г╨╣╤В╨╡ ╨╡╨│╨╛ ╨▓ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╣ ╨┤╨╗╤П ╨╖╨░╨┐╨╕╤Б╨╕
╨║╨░╤В╨░╨╗╨╛╨│, ╨╜╨░╨┐╤А╨╕╨╝╨╡╤А `D:\Portable\EXPC-WLK`, ╨╕ ╨╖╨░╨┐╤Г╤Б╤В╨╕╤В╨╡ `EXPC-WLK.exe`. ╨б╨╛╤Е╤А╨░╨╜╨╕╤В╨╡
╤А╤П╨┤╨╛╨╝ ╨▓╨╡╤Б╤М ╨║╨░╤В╨░╨╗╨╛╨│ `WhisperKey`. ╨Я╤А╨╕ ╨┐╨╡╤А╨▓╨╛╨╝ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╕ ╨▓╤Л╨▒╤А╨░╨╜╨╜╨╛╨╣ ╨╝╨╛╨┤╨╡╨╗╨╕
╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╡ ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╕╤В ╤Б╨║╨░╤З╨░╤В╤М ╨╡╤С ╨╕╨╖ ╨╖╨░╨║╤А╨╡╨┐╨╗╤С╨╜╨╜╨╛╨╣ ╤А╨╡╨▓╨╕╨╖╨╕╨╕ Hugging Face. CPU/fallback
╨┐╤А╨╡╨┤╨┐╨╛╤З╨╕╤В╨░╨╡╤В `small`, CUDA тАФ `large-v3-turbo`. ╨Я╨╛╨╗╨╜╤Л╨╣ snapshot ╨┐╤А╨╛╨▓╨╡╤А╤П╨╡╤В╤Б╤П ╨╕
╨░╤В╨╛╨╝╨░╤А╨╜╨╛ ╤Г╤Б╤В╨░╨╜╨░╨▓╨╗╨╕╨▓╨░╨╡╤В╤Б╤П ╨▓ `WhisperKey/models/<model-id>`. ╨Я╤А╨╛╨▓╨╡╤А╨╡╨╜╨╜╤Л╨╡ ╨╗╨╛╨║╨░╨╗╤М╨╜╤Л╨╡
╨╝╨╛╨┤╨╡╨╗╨╕ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╤О╤В╤Б╤П ╨▒╨╡╨╖ ╨╛╨▒╤А╨░╤Й╨╡╨╜╨╕╤П ╨║ cache. ╨Я╨╛╤Б╨╗╨╡ ╨╖╨░╨│╤А╤Г╨╖╨║╨╕ ╨┤╨╕╨║╤В╨╛╨▓╨║╨░ ╤А╨░╨▒╨╛╤В╨░╨╡╤В ╨▒╨╡╨╖ ╨╕╨╜╤В╨╡╤А╨╜╨╡╤В╨░. ╨Я╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╡ ╤А╨░╨▒╨╛╤В╨░╨╡╤В
╨▓ ╤В╤А╨╡╨╡ ╨╕ ╨▒╨╗╨╛╨║╨╕╤А╤Г╨╡╤В ╨┤╤Г╨▒╨╗╨╕╨║╨░╤В╤Л.

╨Т ╤В╤А╨╡╨╡ ╨┐╨╛╨║╨░╨╖╨░╨╜╤Л ╨░╨║╤В╨╕╨▓╨╜╤Л╨╡ backend ╨╕ ╨╝╨╛╨┤╨╡╨╗╤М. ╨Ь╨╡╨╜╤О ╨╝╨╛╨┤╨╡╨╗╨╡╨╣ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╤П╨╡╤В ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П
╨б╨║╨░╤З╨░╤В╤М, ╨Т╤Л╨▒╤А╨░╤В╤М, ╨Я╤А╨╛╨▓╨╡╤А╨╕╤В╤М ╨╕ ╨г╨┤╨░╨╗╨╕╤В╤М. ╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╤П ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╤П ╤Б╨╛╤Е╤А╨░╨╜╤П╤О╤В
`WhisperKey/models`. Development-╤Б╨▒╨╛╤А╨║╨╕ ╨╜╨╡ ╨┐╨╛╨┤╨┐╨╕╤Б╨░╨╜╤Л, ╨┐╨╛╤Н╤В╨╛╨╝╤Г Windows SmartScreen
╨╝╨╛╨╢╨╡╤В ╨┐╨╛╨║╨░╨╖╨░╤В╤М ╨┐╤А╨╡╨┤╤Г╨┐╤А╨╡╨╢╨┤╨╡╨╜╨╕╨╡; ╨┐╤А╨╛╨▓╨╡╤А╤П╨╣╤В╨╡ ╤Б╨╛╤Б╨╡╨┤╨╜╨╕╨╣ SHA-256 ╨╕ ╤Б╨║╨░╤З╨╕╨▓╨░╨╣╤В╨╡ ╤В╨╛╨╗╤М╨║╨╛ ╨╕╨╖
╨╛╤Д╨╕╤Ж╨╕╨░╨╗╤М╨╜╨╛╨│╨╛ ╤А╨╡╨┐╨╛╨╖╨╕╤В╨╛╤А╨╕╤П. ╨Э╨╡╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╨░╤П production-╨┐╨╛╨┤╨┐╨╕╤Б╤М ╨╛╨┐╨╕╤Б╨░╨╜╨░ ╨▓
`docs/CODE_SIGNING.md`. ╨Х╤Б╨╗╨╕ ╨╝╨╕╨║╤А╨╛╤Д╨╛╨╜ ╨╛╤В╤Б╤Г╤В╤Б╤В╨▓╤Г╨╡╤В, ╨┐╤А╨╕ ╨╖╨░╨┐╤Г╤Б╨║╨╡ ╨▒╤Г╨┤╨╡╤В ╨┐╨╛╨║╨░╨╖╨░╨╜╨░
╨╛╤И╨╕╨▒╨║╨░ input device; ╨┐╤А╨╛╨▓╨╡╤А╤М╤В╨╡ ╨┤╨╛╤Б╤В╤Г╨┐ ╨║ ╨╝╨╕╨║╤А╨╛╤Д╨╛╨╜╤Г ╨╕ ╨▓╤Л╨▒╤А╨░╨╜╨╜╤Л╨╣ ╨▓╤Е╨╛╨┤ Windows.

╨Ш╤Б╤Е╨╛╨┤╨╜╤Л╨╣ ╤А╨╡╨┐╨╛╨╖╨╕╤В╨╛╤А╨╕╨╣ ╨╜╨░╨╝╨╡╤А╨╡╨╜╨╜╨╛ ╨╜╨╡ ╤Б╨╛╨┤╨╡╤А╨╢╨╕╤В Python runtime, ╤Б╤В╨╛╤А╨╛╨╜╨╜╨╕╨╡ ╨▒╨╕╨╜╨░╤А╨╜╤Л╨╡
╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛╤Б╤В╨╕, CUDA/cuDNN, ╤Б╨╛╨▒╤А╨░╨╜╨╜╤Л╨╡ EXE ╨╕ ╨╝╨╛╨┤╨╡╨╗╤М. Runtime ╨╕ ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╡ ╨┐╨╛╤Б╤В╨░╨▓╨╗╤П╤О╤В╤Б╤П
╨▓ portable ZIP GitHub Releases; ╨╝╨╛╨┤╨╡╨╗╤М ╨╖╨░╨│╤А╤Г╨╢╨░╨╡╤В╤Б╤П ╨╛╤В╨┤╨╡╨╗╤М╨╜╨╛ ╨╕╨╖ ╨╖╨░╨║╤А╨╡╨┐╨╗╤С╨╜╨╜╨╛╨│╨╛
╨╕╤Б╤В╨╛╤З╨╜╨╕╨║╨░ Hugging Face.

### ╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М╤Б╨║╨╕╨╡ ╨┤╨░╨╜╨╜╤Л╨╡

╨Э╨░╤Б╤В╤А╨╛╨╣╨║╨╕ ╨╕ ╨╗╨╛╨║╨░╨╗╤М╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╜╨░╤Е╨╛╨┤╤П╤В╤Б╤П ╨▓╨╜╨╡ ╨║╨░╤В╨░╨╗╨╛╨│╨░ ╨┐╤А╨╛╨│╤А╨░╨╝╨╝╤Л:

```text
%APPDATA%\whisperkey\user_settings.yaml
%APPDATA%\whisperkey\commands.yaml
%APPDATA%\whisperkey\vocabulary.db
```

╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╤П ╨╜╨╡ ╨┐╨╡╤А╨╡╨╖╨░╨┐╨╕╤Б╤Л╨▓╨░╤О╤В ╤Н╤В╨╕ ╤Д╨░╨╣╨╗╤Л. ╨п╨╖╤Л╨║ ╨╕╨╜╤В╨╡╤А╤Д╨╡╨╣╤Б╨░ ╤Е╤А╨░╨╜╨╕╤В╤Б╤П ╨▓
`system_tray.language` ╨╕ ╨╜╨╡ ╨╝╨╡╨╜╤П╨╡╤В ╤Б╨╗╨╛╨▓╨░╤А╤М, hotwords ╨╕╨╗╨╕ corrections.

### ╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡

╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨╖╨░╨┐╤Г╤Б╨║╨░╨╡╤В╤Б╤П ╨▓╤А╤Г╤З╨╜╤Г╤О ╨╕ ╨╜╨╡ ╨▒╨╗╨╛╨║╨╕╤А╤Г╨╡╤В ╤Б╤В╨░╤А╤В ╨╕╨╗╨╕ STT. ╨Я╤А╨╕╨╜╨╕╨╝╨░╤О╤В╤Б╤П ╤В╨╛╨╗╤М╨║╨╛
╨╛╤Д╨╕╤Ж╨╕╨░╨╗╤М╨╜╤Л╨╣ ╨╖╨░╨┤╨░╨╜╨╜╤Л╨╣ ╤А╨╡╨┐╨╛╨╖╨╕╤В╨╛╤А╨╕╨╣, ╤Б╤В╨░╨▒╨╕╨╗╤М╨╜╨░╤П semantic version, ╤В╨╛╤З╨╜╤Л╨╣ release
asset ╨╕ SHA-256 ╨╛╤В GitHub. ╨Ю╤В╨┤╨╡╨╗╤М╨╜╤Л╨╣ helper ╨┐╨╛╨┤╨│╨╛╤В╨░╨▓╨╗╨╕╨▓╨░╨╡╤В ╨┐╨╛╨╗╨╜╤Г╤О ╨╜╨╛╨▓╤Г╤О ╨▓╨╡╤А╤Б╨╕╤О,
╨▓╤А╨╡╨╝╨╡╨╜╨╜╨╛ ╤Б╨╛╤Е╤А╨░╨╜╤П╨╡╤В ╨┐╤А╨╡╨┤╤Л╨┤╤Г╤Й╤Г╤О, ╨╢╨┤╤С╤В ╤Б╨╛╤Б╤В╨╛╤П╨╜╨╕╤П ┬л╨У╨╛╤В╨╛╨▓┬╗ ╨╕ ╨╛╤В╨║╨░╤В╤Л╨▓╨░╨╡╤В ╨╕╨╖╨╝╨╡╨╜╨╡╨╜╨╕╤П ╨┐╤А╨╕
╨╛╤И╨╕╨▒╨║╨╡. ╨Ъ╨░╤В╨░╨╗╨╛╨│╨╕ ╨╝╨╛╨┤╨╡╨╗╨╡╨╣ ╨╕ ╨╕╤Е installed metadata ╤Б╨╛╤Е╤А╨░╨╜╤П╤О╤В╤Б╤П ╨╜╨╡╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛ ╨╛╤В
╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╤П ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╤П. ╨Я╨╛╨┤╤А╨╛╨▒╨╜╨╛╤Б╤В╨╕: [UPDATING.md](UPDATING.md).

