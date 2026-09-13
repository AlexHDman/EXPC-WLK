# EXPC-WLK v0.9.2

## Downloads

- [Download application](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-portable-v0.9.2.zip)
- [Download small model](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-small.zip) — recommended for CPU
- [Download large-v3-turbo model](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-large-v3-turbo.zip) — recommended for NVIDIA CUDA

The application ZIP contains no model files. A model ZIP can be extracted into
the application's `WhisperKey` directory, producing `models/<model-id>`. Model
files remain separate from application updates.

If the selected model is missing, EXPC-WLK offers an anonymous HTTPS download
from its exact pinned Hugging Face commit. It downloads the complete snapshot to
staging, verifies required files, sizes and SHA-256, then installs atomically.
After installation the runtime loads only the local model path and does not
depend on Hugging Face cache or Internet access.

## Загрузки

- [Скачать приложение](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-portable-v0.9.2.zip)
- [Скачать модель small](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-small.zip) — рекомендуется для CPU
- [Скачать модель large-v3-turbo](https://github.com/AlexHDman/EXPC-WLK/releases/download/v0.9.2/EXPC-WLK-model-large-v3-turbo.zip) — рекомендуется для NVIDIA CUDA

ZIP приложения не содержит файлов моделей. Model ZIP распаковывается в каталог
`WhisperKey`, создавая `models/<model-id>`. Обновление приложения не изменяет модели.

Если выбранной модели нет, EXPC-WLK предлагает анонимную HTTPS-загрузку из точного
закреплённого commit Hugging Face. Полный snapshot загружается в staging, проходит
проверку списка файлов, размеров и SHA-256, после чего устанавливается атомарно.
После установки runtime использует только локальный путь и не зависит от HF cache
или доступа к Интернету.
