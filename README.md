<p align="center">
  <img src="assets/github-header.png" width="100%" alt="WhisperKey WLK">
</p>
# EXPC-WLK

English | [Русский](#русский)

> **RU:** EXPC-WLK работает на CPU, но для комфортной работы рекомендуется NVIDIA GPU с CUDA. CPU-режим может быть значительно медленнее.
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
development tools are not required on the target PC. The launcher is not signed yet.

### Portable usage

### Downloads for v0.9.2

- [Download application](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-portable-v0.9.2.zip)
- [Download small model](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-small.zip) — recommended for CPU
- [Download large-v3-turbo model](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-large-v3-turbo.zip) — recommended for NVIDIA CUDA

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
the future production-signing process is documented in `docs/CODE_SIGNING.md`.

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

### Current status

The current development release candidate is `0.9.3`. Portable startup, CUDA and CPU transcription, tray
controls, autostart, Dynamic Vocabulary OFF/ON, and local update transactions
have passed locally. Laptop acceptance and a real 0.9.0 to 0.9.1 GitHub update
remain to be tested.

### Update model

Checks are manual and do not block startup or STT. Only the configured official
repository, stable semantic version, exact release asset, and GitHub SHA-256
digest are accepted. A separate helper stages a complete app, temporarily keeps
the previous version, confirms the updated app reaches Ready, and rolls back on
failure. Model directories and installed metadata are preserved independently of
application updates. See [UPDATING.md](UPDATING.md).

### Roadmap

- Publish and test the first complete portable GitHub Release.
- Add signed release provenance when signing is available.
- R2: opt-in learning from explicit corrections.
- R3: context-aware post-correction.
- R4: optional online terminology resolver.

R2-R4 are outside the current baseline.

### Development principle

Build the smallest practical offline change, test it with the real STT pipeline,
measure the result, and expand only after it is proven. Keep working STT, GPU,
hotword, correction, and model-loading behavior stable.

## Русский

EXPC-WLK — портативная локальная система преобразования речи в текст для Windows
на базе Whisper и faster-whisper. Она обеспечивает быструю диктовку в любом
приложении с обработкой речи на компьютере пользователя.

### Возможности

- Локальное STT с закреплёнными CTranslate2-моделями `small` и `large-v3-turbo`.
- Автоматическое ускорение NVIDIA CUDA FP16 с переходом на CPU INT8.
- Смешанная русско-английская речь и сохранение английских технических терминов.
- Dynamic Vocabulary R1, выключенный по умолчанию, постоянные hotwords и corrections.
- Русский и английский интерфейс трея, индикатор статуса и автозапуск пользователя.
- Самодостаточный portable runtime: отдельный Python, venv и `pip install` не нужны.
- Отдельная CTranslate2-модель с закреплёнными revision и SHA-256.
- Ручное обновление через GitHub Releases с SHA-256, staging и откатом.

### Системные требования

- Windows 10/11 x64, Windows UCRT и .NET Framework 4.x.
- Видеокарта NVIDIA и совместимый драйвер необязательны. Режим
  `hardware.mode: auto` использует CUDA FP16 при наличии и иначе запускает CPU INT8.
- Микрофон и разрешение Windows на его использование.

Драйвер NVIDIA требуется только для GPU-ускорения. Python, CUDA Toolkit и средства
разработки на целевом ПК не нужны. Launcher пока не подписан.

### Использование portable-версии

### Загрузки для v0.9.2

- [Скачать приложение](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-portable-v0.9.2.zip)
- [Скачать модель small](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-small.zip) — рекомендуется для CPU
- [Скачать модель large-v3-turbo](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-large-v3-turbo.zip) — рекомендуется для NVIDIA CUDA

Опубликованные model ZIP v0.9.2 необязательны: распакуйте
выбранный архив в каталог приложения `WhisperKey`, объединив его папку `models`.
Если выбранной модели нет, EXPC-WLK предложит скачать закреплённый snapshot с
Hugging Face, проверит его и установит атомарно.

Скачайте полный пакет из GitHub Releases, распакуйте его в доступный для записи
каталог, например `D:\Portable\EXPC-WLK`, и запустите `EXPC-WLK.exe`. Сохраните
рядом весь каталог `WhisperKey`. При первом использовании выбранной модели
приложение предложит скачать её из закреплённой ревизии Hugging Face. CPU/fallback
предпочитает `small`, CUDA — `large-v3-turbo`. Полный snapshot проверяется и
атомарно устанавливается в `WhisperKey/models/<model-id>`. Проверенные локальные
модели используются без обращения к cache. После загрузки диктовка работает без интернета. Приложение работает
в трее и блокирует дубликаты.

В трее показаны активные backend и модель. Меню моделей предоставляет действия
Скачать, Выбрать, Проверить и Удалить. Обновления приложения сохраняют
`WhisperKey/models`. Development-сборки не подписаны, поэтому Windows SmartScreen
может показать предупреждение; процесс будущей production-подписи описан в
`docs/CODE_SIGNING.md`.

Исходный репозиторий намеренно не содержит Python runtime, сторонние бинарные
зависимости, CUDA/cuDNN, собранные EXE и модель. Runtime и приложение поставляются
в portable ZIP GitHub Releases; модель загружается отдельно из закреплённого
источника Hugging Face.

### Пользовательские данные

Настройки и локальные данные находятся вне каталога программы:

```text
%APPDATA%\whisperkey\user_settings.yaml
%APPDATA%\whisperkey\commands.yaml
%APPDATA%\whisperkey\vocabulary.db
```

Обновления не перезаписывают эти файлы. Язык интерфейса хранится в
`system_tray.language` и не меняет словарь, hotwords или corrections.

### Текущее состояние

Текущий development release candidate — `0.9.3`. Проверены portable-запуск, CUDA и CPU STT, трей,
автозапуск, Dynamic Vocabulary OFF/ON и локальные update-транзакции. Проверка на
ноутбуке и реальное обновление 0.9.0 → 0.9.1 через GitHub ещё предстоят.

### Модель обновления

Проверка запускается вручную и не блокирует старт или STT. Принимаются только
официальный заданный репозиторий, стабильная semantic version, точный release
asset и SHA-256 от GitHub. Отдельный helper подготавливает полную новую версию,
временно сохраняет предыдущую, ждёт состояния «Готов» и откатывает изменения при
ошибке. Каталоги моделей и их installed metadata сохраняются независимо от
обновления приложения. Подробности: [UPDATING.md](UPDATING.md).

### План развития

- Опубликовать и проверить первый полный portable-релиз GitHub.
- Добавить подписанное подтверждение происхождения релизов после настройки подписи.
- R2: опциональное обучение на явных исправлениях.
- R3: контекстная посткоррекция.
- R4: опциональный online resolver терминов.

R2-R4 не входят в текущую версию.

### Принцип разработки

Сначала реализовать минимальное практическое offline-изменение, проверить его на
реальном STT pipeline и измерить результат. Расширять только после подтверждения,
сохраняя рабочую логику STT, GPU, hotwords, corrections и загрузки модели.

