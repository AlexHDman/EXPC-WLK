"""Verify model ZIP layout and every payload against the pinned catalog."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "WhisperKey/app/site-packages"))

from whisper_key import model_store  # noqa: E402


def verify(archive, model_id):
    manifest = model_store.manifest_for(ROOT / "WhisperKey", model_id)
    expected_archive = f"EXPC-WLK-model-{model_id}.zip"
    if archive.name != expected_archive:
        raise ValueError("Model asset name mismatch")
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    expected_digest = archive.with_name(archive.name + ".sha256").read_text(
        encoding="ascii"
    ).split()[0]
    if digest != expected_digest:
        raise ValueError("Model asset checksum mismatch")
    prefix = f"models/{model_id}/"
    expected = {prefix + item["name"] for item in manifest["files"]}
    expected.add(prefix + model_store.METADATA_NAME)
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        if len(names) != len(set(name.lower() for name in names)) or set(names) != expected:
            raise ValueError("Unexpected model asset layout")
        for item in manifest["files"]:
            member = prefix + item["name"]
            info = package.getinfo(member)
            if info.file_size != item["bytes"]:
                raise ValueError("Model asset size mismatch: " + item["name"])
            digest_file = hashlib.sha256()
            with package.open(member) as stream:
                while chunk := stream.read(1024**2):
                    digest_file.update(chunk)
            if digest_file.hexdigest() != item["sha256"]:
                raise ValueError("Model asset SHA-256 mismatch: " + item["name"])
        metadata = json.loads(package.read(prefix + model_store.METADATA_NAME))
        if metadata != model_store._metadata(manifest):
            raise ValueError("Installed-model metadata mismatch")
        if package.testzip() is not None:
            raise ValueError("Corrupt model ZIP")
    report = {
        "model": model_id,
        "file": archive.name,
        "bytes": archive.stat().st_size,
        "sha256": digest,
        "entries": len(expected),
        "pass": True,
    }
    print(json.dumps(report), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("model", choices=("small", "large-v3-turbo"))
    args = parser.parse_args()
    verify(args.archive.resolve(), args.model)
