"""Package a trained model directory as a Release asset (Task 2, steps 3-4). Never invents anything.

Usage: python scripts/package_model.py --model-dir training/output/v1 --version v1 --out-dir dist
Writes dist/<version>.tar.gz, dist/<version>.tar.gz.sha256 and dist/release_manifest.json (one entry per version).
Refuses to run if the directory has no model.safetensors / config.json, so an empty or placeholder archive can never be produced.
Archives are deterministic (sorted names, zeroed mtime and owner), so the same weights always give the same SHA-256.
"""
import argparse
import gzip
import hashlib
import json
import pathlib
import tarfile


def package(model_dir: pathlib.Path, version: str, out_dir: pathlib.Path) -> dict:
    if not (model_dir / "model.safetensors").is_file() or not (model_dir / "config.json").is_file():
        raise SystemExit(f"{model_dir} has no model.safetensors/config.json: refusing to package (train a model first)")
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{version}.tar.gz"

    def clean(ti: tarfile.TarInfo) -> tarfile.TarInfo:
        ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = 0, 0, 0, "", ""
        return ti

    with open(archive, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz, tarfile.open(fileobj=gz, mode="w") as tar:
        for f in sorted(p for p in model_dir.rglob("*") if p.is_file()):
            tar.add(f, arcname=f"{version}/{f.relative_to(model_dir).as_posix()}", filter=clean)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (out_dir / f"{archive.name}.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    manifest_path = out_dir / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest[version] = {
        "archive": archive.name,
        "sha256": digest,
        "size_bytes": archive.stat().st_size,
        "model_safetensors_sha256": hashlib.sha256((model_dir / "model.safetensors").read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest[version]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--out-dir", default="dist")
    a = ap.parse_args()
    print(json.dumps(package(pathlib.Path(a.model_dir), a.version, pathlib.Path(a.out_dir)), indent=2))
