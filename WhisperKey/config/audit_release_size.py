"""Report portable ZIP size composition without extracting its contents."""
import argparse
import json
from pathlib import Path
import zipfile


def audit(path):
    with zipfile.ZipFile(path) as package:
        files = [item for item in package.infolist() if not item.is_dir()]
        names = [item.filename.lower() for item in files]
        forbidden = [name for name in names if (
            name.startswith("whisperkey/models/")
            or "/.staging-" in name
            or name.startswith("whisperkey/cache/")
            or "/huggingface/hub/" in name
        )]
        groups = {}
        for item in files:
            parts = item.filename.split("/")
            key = "/".join(parts[:3]) if len(parts) >= 3 else parts[0]
            entry = groups.setdefault(key, {"files": 0, "bytes": 0, "compressed_bytes": 0})
            entry["files"] += 1
            entry["bytes"] += item.file_size
            entry["compressed_bytes"] += item.compress_size
        return {
            "archive": str(path.resolve()),
            "archive_bytes": path.stat().st_size,
            "entries": len(files),
            "uncompressed_bytes": sum(item.file_size for item in files),
            "forbidden_model_cache_staging": forbidden,
            "groups": dict(sorted(groups.items(), key=lambda pair: pair[1]["compressed_bytes"], reverse=True)),
            "top_50": [
                {"path": item.filename, "bytes": item.file_size, "compressed_bytes": item.compress_size}
                for item in sorted(files, key=lambda item: item.file_size, reverse=True)[:50]
            ],
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.archive)
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
