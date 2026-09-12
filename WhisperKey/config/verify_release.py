"""Validate a built full release and extract it into a new clean-test folder."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile


def verify(archive, destination):
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    expected = archive.with_name(archive.name + ".sha256").read_text(encoding="ascii").split()[0]
    if digest != expected:
        raise ValueError("Release checksum mismatch")
    if destination.exists():
        raise FileExistsError("Clean-test destination must not exist")
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        if len(names) != len(set(n.lower() for n in names)):
            raise ValueError("Duplicate ZIP member")
        for name in names:
            parts = PurePosixPath(name).parts
            if name.startswith("/") or "\\" in name or ":" in name or ".." in parts:
                raise ValueError("Unsafe ZIP member")
            if any(p.lower() in {".git", "__pycache__", "user_settings.yaml", "commands.yaml", "vocabulary.db", "direct_url.json"} for p in parts):
                raise ValueError("Development/personal artifact in release: " + name)
            if name.lower().startswith("whisperkey/logs/"):
                raise ValueError("Local log in release")
        required = {"EXPC-WLK.exe", "WhisperKey/runtime/pythonw.exe", "WhisperKey/runtime/python.exe",
                    "WhisperKey/runtime/python312.dll", "WhisperKey/runtime/python312._pth",
                    "WhisperKey/config/PortableUpdater.exe", "WhisperKey/config/release.json",
                    "WhisperKey/config/model-manifest.json", "WhisperKey/app/portable_boot.py"}
        if not required <= set(names):
            raise ValueError("Incomplete full portable release")
        if any(name.startswith("WhisperKey/models/") for name in names):
            raise ValueError("Application release must not bundle model files")
        version = json.loads(package.read("WhisperKey/config/release.json"))["version"]
        if archive.name != f"EXPC-WLK-portable-v{version}.zip":
            raise ValueError("Archive name/version mismatch")
        # Inspect app-owned text; third-party license/metadata content is retained.
        scanned = 0
        for name in names:
            if not (name.startswith("WhisperKey/app/site-packages/whisper_key/") or
                    name.startswith("WhisperKey/config/") or name in ("README.md", "UPDATING.md")):
                continue
            if not name.endswith((".py", ".json", ".yaml", ".md")):
                continue
            text = package.read(name).decode("utf-8-sig")
            if re.search(r"[A-Za-z]:\\Users\\|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|-----BEGIN .*PRIVATE KEY", text):
                raise ValueError("Private path or secret pattern: " + name)
            scanned += 1
        bad = package.testzip()
        if bad is not None:
            raise ValueError("Corrupt ZIP member: " + bad)
        destination.mkdir(parents=True)
        package.extractall(destination)
    print(json.dumps({"version": version, "sha256": digest, "entries": len(names),
                      "scanned_app_text_files": scanned, "extracted": str(destination), "pass": True}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    verify(args.archive.resolve(), args.destination.resolve())
