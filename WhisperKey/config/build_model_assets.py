"""Build independently downloadable, verified model ZIP assets."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "WhisperKey/app/site-packages"))

from whisper_key import model_store  # noqa: E402


def build(model_ids):
    version = json.loads(
        (ROOT / "WhisperKey/config/release.json").read_text(encoding="utf-8")
    )["version"]
    output = ROOT / "dist" / version / "models"
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    forbidden = lambda *args, **kwargs: (_ for _ in ()).throw(  # noqa: E731
        RuntimeError("Model asset source must already be installed and verified")
    )
    for model_id in model_ids:
        manifest = model_store.manifest_for(ROOT / "WhisperKey", model_id)
        source = model_store.ensure_model(
            ROOT / "WhisperKey", model_id, consent=forbidden, opener=forbidden
        )
        archive = output / f"EXPC-WLK-model-{model_id}.zip"
        if archive.exists():
            raise FileExistsError(f"Refusing to overwrite model asset: {archive}")
        names = [item["name"] for item in manifest["files"]] + [model_store.METADATA_NAME]
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED, allowZip64=True) as package:
            for name in names:
                package.write(source / name, f"models/{model_id}/{name}")
        with archive.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        checksum = archive.with_name(archive.name + ".sha256")
        checksum.write_text(digest + "  " + archive.name + "\n", encoding="ascii")
        report = {
            "model": model_id,
            "source": manifest["source"],
            "revision": manifest["revision"],
            "file": archive.name,
            "bytes": archive.stat().st_size,
            "sha256": digest,
            "entries": len(names),
            "github_asset_under_2gib": archive.stat().st_size < 2 * 1024**3,
        }
        reports.append(report)
        print(json.dumps(report), flush=True)
    (output / "models-build.json").write_text(
        json.dumps(reports, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "models", nargs="*", choices=("small", "large-v3-turbo"),
    )
    selected = parser.parse_args().models or ["small", "large-v3-turbo"]
    build(selected)
