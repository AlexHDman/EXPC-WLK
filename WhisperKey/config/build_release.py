"""Build an install/update ZIP from the existing portable runtime, without backups."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", ".ruff_cache"}
SKIP_NAMES = {"user_settings.yaml", "commands.yaml", "vocabulary.db", "direct_url.json"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log", ".dmp", ".tmp", ".db", ".db-wal", ".db-shm"}


def build(kind):
    metadata = json.loads((ROOT / "WhisperKey/config/release.json").read_text(encoding="utf-8"))
    version = metadata["version"]
    name = f"EXPC-WLK-portable-v{version}.zip" if kind == "full" else metadata["asset_name"]
    output = ROOT / "dist" / version / "application"
    output.mkdir(parents=True, exist_ok=True)
    archive = output / name
    if archive.exists():
        raise FileExistsError(f"Refusing to overwrite built release: {archive}")
    entries = [(ROOT / "WhisperKey/config/EXPC-WLK.new.exe", "EXPC-WLK.exe")]
    root_docs = ("README.md", "LICENSE", "CHANGELOG.md", "UPDATING.md",
                 "PERFORMANCE_TEST_RESULTS.md", "REGRESSION_TEST_RESULTS.md") if kind == "full" else ("README.md",)
    entries += [(ROOT / name, name) for name in root_docs]
    trees = ["WhisperKey/app", "WhisperKey/runtime"]
    for tree in trees:
        for source in sorted((ROOT / tree).rglob("*")):
            if source.is_symlink():
                raise ValueError(f"Release source is a link: {source}")
            if not source.is_file():
                continue
            rel = source.relative_to(ROOT)
            if any(p.lower() in SKIP_DIRS for p in rel.parts):
                continue
            if source.name.lower() in SKIP_NAMES or source.suffix.lower() in SKIP_SUFFIXES:
                continue
            entries.append((source, rel.as_posix()))
    for name in ("release.json", "model-manifest.json", "model-catalog.json",
                 "PortableUpdater.exe", "native-model-manifest.json", "benchmark.py"):
        entries.append((ROOT / "WhisperKey/config" / name, "WhisperKey/config/" + name))
    if kind == "full":
        entries.append((ROOT / "docs/CODE_SIGNING.md", "docs/CODE_SIGNING.md"))
    for source, _ in entries:
        if not source.is_file():
            raise FileNotFoundError(source)
    print(f"Building {archive.name}: {len(entries)} files", flush=True)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as package:
        for index, (source, member) in enumerate(entries):
            package.write(source, member)
            if index % 500 == 0 or source.stat().st_size > 100 * 1024**2:
                print(f"Packed {index + 1}/{len(entries)}: {member}", flush=True)
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    checksum = archive.with_name(archive.name + ".sha256")
    checksum.write_text(digest + "  " + archive.name + "\n", encoding="ascii")
    report = {"version": version, "kind": kind, "file": archive.name, "bytes": archive.stat().st_size,
              "sha256": digest, "entries": len(entries), "github_asset_under_2gib": archive.stat().st_size < 2 * 1024**3}
    (output / (kind + "-build.json")).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("full", "update"), required=True)
    build(parser.parse_args().kind)
