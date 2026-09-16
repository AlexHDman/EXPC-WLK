# EXPC-WLK performance test results

Date: 2026-09-16

Fixture: bundled `app_ready.wav`, duration 0.450 s. Command-line tool:
`WhisperKey/config/benchmark.py`. Measurements include model construction and
transcription separately; beam size is 1.

| Backend | Model | Load | Transcription | Realtime factor |
|---|---|---:|---:|---:|
| CPU INT8 | small | 0.883 s | 2.384 s | 5.298 |
| NVIDIA CUDA FP16 | large-v3-turbo | 1.860 s | 22.881 s | 50.847 |

The fixture is a short application sound rather than a speech-quality benchmark.
The measurements ran from clean extracted v1.0.0 CPU/CUDA candidates. The CUDA
number is cold first-inference latency; the immediately following portable
self-test measured 21.2 s then 0.6 s for its two calls, showing substantial
one-time warm-up cost. These numbers verify the actual portable backends; they
must not be treated as general accuracy or long-audio performance results.
