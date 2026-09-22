"""Exercise real installed-mode model import without network access."""
import argparse
import hashlib
import json
from pathlib import Path

from whisper_key import model_import, model_store


parser = argparse.ArgumentParser()
parser.add_argument("--metadata-root", type=Path, required=True)
parser.add_argument("--model-root", type=Path, required=True)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--model", choices=("small", "large-v3-turbo"), required=True)
args = parser.parse_args()

manifest = model_store.manifest_for(args.metadata_root, args.model)
source_hashes = {
    item["name"]: hashlib.sha256((args.source / item["name"]).read_bytes()).hexdigest()
    for item in manifest["files"]
}
result = model_import.import_model(
    args.metadata_root, args.model_root, args.model, args.source)
after_hashes = {
    item["name"]: hashlib.sha256((args.source / item["name"]).read_bytes()).hexdigest()
    for item in manifest["files"]
}
status = model_store.model_status(
    args.metadata_root, args.model, verify_hashes=True, model_root=args.model_root)
print(json.dumps({
    "model": result["model"],
    "copied": result["copied"],
    "status": status,
    "source_unchanged": source_hashes == after_hashes,
    "metadata": (Path(result["path"]) / model_store.METADATA_NAME).is_file(),
}))
