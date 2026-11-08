"""Teacher labelling worker (Task 1). NOT RUN in this repository yet.

Reads data/commands_pool.jsonl (local) or s3://datasets/commands_pool.jsonl, keeps the records whose
position n satisfies n mod SHARD_COUNT == SHARD_INDEX, asks the Ollama teacher for a JSON label, and
writes datasets/teacher/shard-<i>.jsonl as {"id","text","raw"}. Resumable: finished IDs are skipped.

Env: SHARD_INDEX (or JOB_COMPLETION_INDEX), SHARD_COUNT, OLLAMA_HOST, TEACHER_MODEL, S3_ENDPOINT,
DATASETS_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, POOL_PATH (optional local file).
"""
import json
import os
import pathlib
import sys
import time

PROMPT_FILE = pathlib.Path(__file__).resolve().parents[1] / "prompts" / "teacher_prompt.txt"


def shard_records(records, index, count):
    """Complete, disjoint, balanced: record n goes to shard n mod count."""
    return [r for n, r in enumerate(records) if n % count == index]


def shard_index():
    for var in ("SHARD_INDEX", "JOB_COMPLETION_INDEX"):
        if os.environ.get(var) is not None:
            return int(os.environ[var])
    raise SystemExit("SHARD_INDEX or JOB_COMPLETION_INDEX must be set")


def build_prompt(template, text):
    return template.replace("{text}", text)


def ask_teacher(host, model, prompt):
    import requests

    r = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0, "seed": 42}},
        timeout=600,
    )
    r.raise_for_status()
    return r.json()["response"].strip()


def load_pool():
    local = os.environ.get("POOL_PATH")
    if local:
        text = pathlib.Path(local).read_text(encoding="utf-8")
    else:
        import boto3

        s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"])
        text = s3.get_object(Bucket=os.environ.get("DATASETS_BUCKET", "datasets"), Key="commands_pool.jsonl")["Body"].read().decode()
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def main():
    i, k = shard_index(), int(os.environ.get("SHARD_COUNT", "2"))
    host = os.environ.get("OLLAMA_HOST", "http://host.k3d.internal:11434")
    model = os.environ.get("TEACHER_MODEL", "phi3.5")
    template = PROMPT_FILE.read_text(encoding="utf-8")
    mine = shard_records(load_pool(), i, k)
    out = pathlib.Path(f"datasets/teacher/shard-{i}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in out.read_text().splitlines() if l.strip()} if out.exists() else set()
    t0 = time.time()
    with out.open("a", encoding="utf-8") as f:
        for n, rec in enumerate(mine, 1):
            if rec["id"] in done:
                continue
            raw = ask_teacher(host, model, build_prompt(template, rec["text"]))
            f.write(json.dumps({"id": rec["id"], "text": rec["text"], "raw": raw}) + "\n")
            f.flush()
            if n % 25 == 0:
                print(f"[shard {i}] {n}/{len(mine)} after {time.time() - t0:.0f}s", flush=True)
    if os.environ.get("S3_ENDPOINT"):
        import boto3

        boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"]).upload_file(
            str(out), os.environ.get("DATASETS_BUCKET", "datasets"), f"teacher/shard-{i}.jsonl"
        )
    print(f"[shard {i}] done -> {out}")


if __name__ == "__main__":
    sys.exit(main())
