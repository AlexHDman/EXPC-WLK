# EXPC-WLK performance test results

Date: 2026-09-14

Fixture: bundled `app_ready.wav`, duration 0.450 s. Command-line tool:
`WhisperKey/config/benchmark.py`. Measurements include model construction and
transcription separately; beam size is 1.

| Backend | Model | Load | Transcription | Realtime factor |
|---|---|---:|---:|---:|
| CPU INT8 | small | 0.788 s | 2.326 s | 5.170 |
| NVIDIA CUDA FP16 | large-v3-turbo | 1.504 s | 1.149 s | 2.554 |

The fixture is a short application sound rather than a speech-quality benchmark.
The final measurements ran from the clean extracted v0.9.3 candidate under
`C:\Temp\Test-WLK-0.9.3`. These numbers verify the actual portable backends; they
must not be treated as general accuracy or long-audio performance results.
