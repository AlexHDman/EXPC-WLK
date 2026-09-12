# EXPC-WLK

English | [Русский](#русский)

## English

EXPC-WLK is portable local speech-to-text for Windows based on Whisper and
faster-whisper. It provides fast dictation from any application while keeping
speech processing on the local computer.

### Features

- Local STT with the `large-v3-turbo` model.
- NVIDIA CUDA acceleration and an explicit error if the required GPU path is unavailable.
- Mixed Russian-English speech and English technical-term preservation.
- Dynamic Vocabulary R1, disabled by default, plus permanent hotwords and corrections.
- Russian and English tray interface, status indicator, and optional user autostart.
- Self-contained portable runtime; no separate Python, venv, or `pip install` is required.
- Built-in model in the portable release package.
- Manual GitHub Releases updates with SHA-256 verification, safe staging, and rollback.

### System requirements

- Windows 10/11 x64, Windows UCRT, and .NET Framework 4.x.
- NVIDIA GPU and a driver compatible with the bundled CUDA 12 libraries for the
  default CUDA/float16 configuration.
- Microphone and Windows microphone permission.

The NVIDIA driver is an external dependency. Python, the CUDA Toolkit, and
development tools are not required on the target PC. The launcher is not signed yet.

### Portable usage

Download the complete package from GitHub Releases, extract it to a writable
folder such as `D:\Portable\EXPC-WLK`, and run `EXPC-WLK.exe`. Keep the adjacent
`WhisperKey` folder intact. The app runs in the tray and prevents duplicate instances.

This source repository intentionally excludes the Python runtime, third-party
binary dependencies, CUDA/cuDNN libraries, built EXEs, and model. Those large
artifacts belong in the portable ZIP attached to a GitHub Release.

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

The current baseline is `0.8.2`. Portable startup, CUDA transcription, tray
controls, autostart, Dynamic Vocabulary OFF/ON, and local update transactions
have passed. The first portable Release and a real GitHub update remain to be tested.

### Update model

Checks are manual and do not block startup or STT. Only the configured official
repository, stable semantic version, exact release asset, and GitHub SHA-256
digest are accepted. A separate helper stages a complete app, temporarily keeps
the previous version, confirms the updated app reaches Ready, and rolls back on
failure. See [UPDATING.md](UPDATING.md).

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

- Локальное STT с моделью `large-v3-turbo`.
- Ускорение NVIDIA CUDA и явная ошибка, если требуемый GPU-режим недоступен.
- Смешанная русско-английская речь и сохранение английских технических терминов.
- Dynamic Vocabulary R1, выключенный по умолчанию, постоянные hotwords и corrections.
- Русский и английский интерфейс трея, индикатор статуса и автозапуск пользователя.
- Самодостаточный portable runtime: отдельный Python, venv и `pip install` не нужны.
- Встроенная модель в portable-релизе.
- Ручное обновление через GitHub Releases с SHA-256, staging и откатом.

### Системные требования

- Windows 10/11 x64, Windows UCRT и .NET Framework 4.x.
- Видеокарта NVIDIA и совместимый с CUDA 12 драйвер для стандартного CUDA/float16.
- Микрофон и разрешение Windows на его использование.

Драйвер NVIDIA остаётся внешней зависимостью. Python, CUDA Toolkit и средства
разработки на целевом ПК не нужны. Launcher пока не подписан.

### Использование portable-версии

Скачайте полный пакет из GitHub Releases, распакуйте его в доступный для записи
каталог, например `D:\Portable\EXPC-WLK`, и запустите `EXPC-WLK.exe`. Сохраните
рядом весь каталог `WhisperKey`. Приложение работает в трее и блокирует дубликаты.

Исходный репозиторий намеренно не содержит Python runtime, сторонние бинарные
зависимости, CUDA/cuDNN, собранные EXE и модель. Они поставляются отдельным
portable ZIP в GitHub Releases.

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

Текущая база — `0.8.2`. Проверены portable-запуск, CUDA STT, трей, автозапуск,
Dynamic Vocabulary OFF/ON и локальные update-транзакции. Первый portable Release
и реальное обновление через GitHub ещё нужно проверить.

### Модель обновления

Проверка запускается вручную и не блокирует старт или STT. Принимаются только
официальный заданный репозиторий, стабильная semantic version, точный release
asset и SHA-256 от GitHub. Отдельный helper подготавливает полную новую версию,
временно сохраняет предыдущую, ждёт состояния «Готов» и откатывает изменения при
ошибке. Подробности: [UPDATING.md](UPDATING.md).

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
