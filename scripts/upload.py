"""Upload a file or a model directory to SeaweedFS (S3). NOT RUN yet.

Usage: python scripts/upload.py --bucket datasets --src data/commands_pool.jsonl --key commands_pool.jsonl
       python scripts/upload.py --bucket models --src training/output/v1 --key v1
Env: S3_ENDPOINT (default http://localhost:8333), AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
"""
import argparse
import os
import pathlib

import boto3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--key", required=True)
    a = ap.parse_args()
    s3 = boto3.client("s3", endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:8333"))
    try:
        s3.create_bucket(Bucket=a.bucket)
    except Exception:  # already exists
        pass
    src = pathlib.Path(a.src)
    files = [(src, a.key)] if src.is_file() else [(p, f"{a.key}/{p.relative_to(src).as_posix()}") for p in src.rglob("*") if p.is_file()]
    for p, key in files:
        s3.upload_file(str(p), a.bucket, key)
        print("uploaded", f"s3://{a.bucket}/{key}")


if __name__ == "__main__":
    main()
