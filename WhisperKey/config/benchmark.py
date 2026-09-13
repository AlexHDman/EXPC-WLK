"""Reproducible local faster-whisper benchmark using installed portable models."""
import argparse
import json
from pathlib import Path
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from portable_boot import configure  # noqa: E402
configure()
sys.path.insert(0, str(ROOT / "app/site-packages"))

from faster_whisper import WhisperModel  # noqa: E402
from whisper_key.model_store import manifest_for, model_status  # noqa: E402


def benchmark(model_id, device, compute_type, fixture):
    if model_status(ROOT, model_id) != "valid":
        raise RuntimeError(f"Verified local model is required: {model_id}")
    manifest = manifest_for(ROOT, model_id)
    model_path = ROOT / "models" / manifest["directory"]
    with wave.open(str(fixture), "rb") as stream:
        audio_seconds = stream.getnframes() / stream.getframerate()
    started = time.perf_counter()
    model = WhisperModel(str(model_path), device=device, compute_type=compute_type)
    load_seconds = time.perf_counter() - started
    started = time.perf_counter()
    segments, _ = model.transcribe(str(fixture), beam_size=1, condition_on_previous_text=False)
    text = "".join(segment.text for segment in segments).strip()
    transcription_seconds = time.perf_counter() - started
    return {
        "fixture": fixture.name, "audio_seconds": round(audio_seconds, 3),
        "model": model_id, "backend": device, "compute_type": compute_type,
        "model_load_seconds": round(load_seconds, 3),
        "transcription_seconds": round(transcription_seconds, 3),
        "realtime_factor": round(transcription_seconds / audio_seconds, 3),
        "transcript": text,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=("small", "large-v3-turbo"))
    parser.add_argument("--device", required=True, choices=("cpu", "cuda"))
    parser.add_argument("--compute-type", required=True, choices=("int8", "float16"))
    parser.add_argument("--fixture", type=Path, default=ROOT / "app/site-packages/whisper_key/assets/sounds/app_ready.wav")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = benchmark(args.model, args.device, args.compute_type, args.fixture)
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    print(payload, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
