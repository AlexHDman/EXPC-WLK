"""Publish explicitly selected Release assets using existing Git credentials."""
import argparse
import hashlib
import http.client
import json
from pathlib import Path
import subprocess
from urllib.parse import quote


REPOSITORY = "AlexHDman/EXPC-WLK"


def credential():
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                            text=True, capture_output=True, check=True)
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if not fields.get("password"):
        raise RuntimeError("No GitHub credential available")
    return fields["password"]


def api(token, method, path, payload=None, missing_ok=False):
    conn = http.client.HTTPSConnection("api.github.com", timeout=60)
    try:
        conn.request(method, path, json.dumps(payload).encode() if payload is not None else None,
                     {"Authorization": "Bearer " + token, "User-Agent": "EXPC-WLK-release",
                      "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        if response.status == 404 and missing_ok:
            return None
        if not 200 <= response.status < 300:
            raise RuntimeError(f"GitHub API {method} failed: HTTP {response.status}")
        return json.loads(data) if data else None
    finally:
        conn.close()


def upload(token, release_id, path):
    size = path.stat().st_size
    if size >= 2 * 1024**3:
        raise ValueError("GitHub asset must be smaller than 2 GiB: " + path.name)
    conn = http.client.HTTPSConnection("uploads.github.com", timeout=180)
    digest = hashlib.sha256()
    try:
        conn.putrequest("POST", f"/repos/{REPOSITORY}/releases/{release_id}/assets?name={quote(path.name, safe='')}")
        conn.putheader("Authorization", "Bearer " + token)
        conn.putheader("User-Agent", "EXPC-WLK-release")
        conn.putheader("Content-Type", "application/octet-stream")
        conn.putheader("Content-Length", str(size))
        conn.endheaders()
        sent = 0
        with path.open("rb") as source:
            while chunk := source.read(1024**2):
                conn.send(chunk)
                digest.update(chunk)
                sent += len(chunk)
                if sent % (64 * 1024**2) == 0:
                    print(f"Upload {path.name}: {sent}/{size}", flush=True)
        response = conn.getresponse()
        data = response.read()
        if response.status != 201:
            raise RuntimeError(f"Asset upload failed: HTTP {response.status}")
        result = json.loads(data)
        if result.get("size") != size or result.get("digest") != "sha256:" + digest.hexdigest():
            raise ValueError("GitHub asset digest/size did not match local file")
        print("Verified uploaded asset: " + path.name, flush=True)
        return result
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--notes", required=True, type=Path)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("assets", nargs="+", type=Path)
    args = parser.parse_args()
    local = {}
    for path in args.assets:
        if path.name in local or not path.is_file() or path.stat().st_size >= 2 * 1024**3:
            raise ValueError("Missing, duplicate or oversized release asset: " + str(path))
        with path.open("rb") as source:
            local[path.name] = hashlib.file_digest(source, "sha256").hexdigest()
    token = credential()
    prefix = f"/repos/{REPOSITORY}/releases"
    releases = api(token, "GET", prefix + "?per_page=100")
    matches = [r for r in releases if r["tag_name"] == args.tag]
    if len(matches) > 1:
        raise ValueError("Ambiguous release")
    if matches:
        release = matches[0]
        if not release["draft"]:
            raise ValueError("Release is already published; refusing to modify it")
    else:
        release = api(token, "POST", prefix, {"tag_name": args.tag, "target_commitish": args.commit,
                      "name": "EXPC-WLK " + args.tag, "body": args.notes.read_text(encoding="utf-8"),
                      "draft": True, "prerelease": False})
    print(f"Draft release: id={release['id']}, tag={args.tag}", flush=True)
    remote = {a["name"]: a for a in release.get("assets", [])}
    for path in args.assets:
        if path.name in remote:
            if remote[path.name].get("digest") != "sha256:" + local[path.name]:
                raise ValueError("Existing asset differs; no asset was overwritten")
            print("Matching asset already uploaded: " + path.name, flush=True)
        else:
            remote[path.name] = upload(token, release["id"], path)
    if args.publish:
        result = api(token, "PATCH", prefix + "/" + str(release["id"]),
                     {"draft": False, "make_latest": "true", "body": args.notes.read_text(encoding="utf-8")})
        print("Published: " + result["html_url"], flush=True)
    else:
        print("Assets verified; release remains a draft.", flush=True)


if __name__ == "__main__":
    main()
