# EXPC-WLK v0.9.0

## Русский

Portable-приложение для локальной диктовки в Windows x64. Python runtime,
faster-whisper и CUDA/cuDNN включены в ZIP. Отдельная установка Python не нужна.

1. Скачайте `EXPC-WLK-portable-v0.9.0.zip` и файл `.zip.sha256` ниже.
2. Проверьте SHA-256: `Get-FileHash .\EXPC-WLK-portable-v0.9.0.zip -Algorithm SHA256`.
3. Распакуйте ZIP полностью в доступную для записи папку.
4. Запустите `EXPC-WLK.exe`. При отсутствии модели подтвердите её загрузку с
   Hugging Face (около 1.51 GiB). Точная revision и SHA-256 закреплены в
   `WhisperKey/config/model-manifest.json`.
5. Дождитесь зелёного индикатора. Проверьте диктовку в Блокноте: удерживайте
   Ctrl+Win, произнесите фразу и отпустите клавиши; текст должен вставиться.

Если проверенная модель уже лежит в `WhisperKey/models/large-v3-turbo`, повторная
загрузка не нужна. После первой загрузки распознавание работает без интернета.
Настройки пользователя: `%APPDATA%\whisperkey`.

Требуются Windows 10/11 x64, .NET Framework 4.x, микрофон и видеокарта NVIDIA с
драйвером для CUDA 12. Без подходящего GPU/драйвера выводится явная ошибка;
автоматического перехода на CPU нет. Launcher пока не подписан.

RU/EN трей, автозапуск и Dynamic Vocabulary R1 сохранены. Автозапуск и R1
выключены по умолчанию. В этом релизе нет R2 или online resolver терминов.

Приложение и модель обновляются независимо: application updater сохраняет
установленные файлы модели и её manifest. Для проверки настоящего обновления
0.9.0 → 0.9.1 сначала подтвердите работу 0.9.0 на ноутбуке; затем будет опубликован
тестовый patch release. Успешное обновление на ноутбуке пока не заявляется.

## English

Portable local dictation for Windows x64. Python, faster-whisper and CUDA/cuDNN
are bundled. Download the ZIP and its SHA-256 file, verify the checksum, extract
the entire ZIP to a writable folder and run `EXPC-WLK.exe`.

The model is separate from the application ZIP. On first launch, accept the
approximately 1.51 GiB Hugging Face download if requested. Source, immutable
revision and SHA-256 are pinned in `WhisperKey/config/model-manifest.json`.
An existing verified local model is reused; subsequent dictation works offline.

Requires Windows 10/11 x64, .NET Framework 4.x, a microphone and an NVIDIA GPU
with a CUDA 12-compatible driver. No separate Python installation is required.
The launcher is unsigned. User data lives in `%APPDATA%\whisperkey`.

RU/EN tray, user autostart and Dynamic Vocabulary R1 are available. Autostart
and R1 default to OFF. No R2 or online terminology resolver is included.
Application updates preserve the installed model and its manifest. A real
0.9.0 to 0.9.1 update will be checked after laptop acceptance of this release.
