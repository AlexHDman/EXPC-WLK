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

# Development-only modules present in the bundled environment.  Keep the source
# runtime intact and omit these only from release archives.
PACKAGE_SKIP_PREFIXES = (
    "whisperkey/app/site-packages/onnxruntime/tools/",
    "whisperkey/app/site-packages/onnxruntime/transformers/",
    "whisperkey/app/site-packages/pythonwin/",
    "whisperkey/app/site-packages/ten_vad/lib/macos/",
    "whisperkey/app/site-packages/hf_xet/",
    "whisperkey/runtime/lib/venv/",
    "whisperkey/runtime/lib/lib2to3/",
    "whisperkey/runtime/lib/unittest/",
    "whisperkey/runtime/lib/turtledemo/",
    "whisperkey/runtime/lib/pydoc_data/",
)
PACKAGE_SKIP_FILES = {
    "whisperkey/app/site-packages/pywin32.chm",
    "whisperkey/runtime/dlls/tcl86t.dll",
    "whisperkey/runtime/dlls/tk86t.dll",
    "whisperkey/runtime/lib/pydoc.py",
    "whisperkey/runtime/lib/turtle.py",
    "whisperkey/runtime/lib/doctest.py",
}


def is_release_excluded(relative_path):
    normalized = relative_path.as_posix().lower()
    if normalized in PACKAGE_SKIP_FILES or normalized.startswith(PACKAGE_SKIP_PREFIXES):
        return True
    # hf_xet is an optional accelerated Hugging Face transfer client. EXPC-WLK's
    # pinned model downloader uses urllib, so its metadata is unnecessary too.
    return (normalized.startswith("whisperkey/app/site-packages/hf_xet-") and
            ".dist-info/" in normalized)


def build(kind, variant=None):
    metadata = json.loads((ROOT / "WhisperKey/config/release.json").read_text(encoding="utf-8"))
    version = metadata["version"]
    if variant not in (None, "cpu", "cuda"):
        raise ValueError("Unsupported package variant")
    if kind == "full" and variant:
        name = f"EXPC-WLK-portable-{variant.upper()}-v{version}.zip"
    else:
        name = f"EXPC-WLK-portable-v{version}.zip" if kind == "full" else metadata["asset_name"]
    release_metadata = dict(metadata)
    if variant:
        release_metadata["package_variant"] = variant
        release_metadata["asset_name"] = name
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
            if variant == "cpu":
                normalized = rel.as_posix().lower()
                if (normalized.startswith("whisperkey/runtime/native/") or
                        normalized == "whisperkey/app/site-packages/ctranslate2/cudnn64_9.dll"):
                    continue
            if any(p.lower() in SKIP_DIRS for p in rel.parts):
                continue
            if source.name.lower() in SKIP_NAMES or source.suffix.lower() in SKIP_SUFFIXES:
                continue
            if is_release_excluded(rel):
                continue
            entries.append((source, rel.as_posix()))
    for name in ("model-manifest.json", "model-catalog.json",
                 "PortableUpdater.exe", "native-model-manifest.json", "benchmark.py"):
        entries.append((ROOT / "WhisperKey/config" / name, "WhisperKey/config/" + name))
    if kind == "full":
        entries.append((ROOT / "docs/CODE_SIGNING.md", "docs/CODE_SIGNING.md"))
    for source, _ in entries:
        if not source.is_file():
            raise FileNotFoundError(source)
    print(f"Building {archive.name}: {len(entries)} files", flush=True)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as package:
        package.writestr("WhisperKey/config/release.json",
                         json.dumps(release_metadata, indent=2) + "\n")
        if variant:
            package.writestr("WhisperKey/config/package-profile.json",
                             json.dumps({"format": 1, "variant": variant}, indent=2) + "\n")
        for index, (source, member) in enumerate(entries):
            package.write(source, member)
            if index % 500 == 0 or source.stat().st_size > 100 * 1024**2:
                print(f"Packed {index + 1}/{len(entries)}: {member}", flush=True)
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    checksum = archive.with_name(archive.name + ".sha256")
    checksum.write_text(digest + "  " + archive.name + "\n", encoding="ascii")
    report = {"version": version, "kind": kind, "variant": variant, "file": archive.name,
              "bytes": archive.stat().st_size, "sha256": digest,
              "entries": len(entries) + 1 + bool(variant),
              "github_asset_under_2gib": archive.stat().st_size < 2 * 1024**3}
    report_name = f"{kind}-{variant}-build.json" if variant else f"{kind}-build.json"
    (output / report_name).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("full", "update"), required=True)
    parser.add_argument("--variant", choices=("cpu", "cuda"))
    args = parser.parse_args()
    build(args.kind, args.variant)
