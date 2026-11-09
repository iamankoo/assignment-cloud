"""Clean the teacher shards into train.jsonl (Task 1). Unit-tested on toy records; NOT RUN on real teacher output.

Usage: python worker/clean.py --shards datasets/teacher/shard-0.jsonl datasets/teacher/shard-1.jsonl \
           --out datasets/v1/train.jsonl --counts-out results/clean_counts.json
Rejection reasons are counted in the order checked; input = kept + sum(rejected) always holds.
"""
import argparse
import hashlib
import json
import os
import pathlib

INTENTS = {"alarm_set", "alarm_query", "calendar_set", "calendar_query", "calendar_remove",
           "weather_query", "datetime_query", "recommendation_events"}
KEYS = {"intent", "date", "time", "place"}


def check(text, raw):
    """Return (label, None) if the teacher reply is usable, else (None, reason)."""
    try:
        obj = json.loads(raw)
    except ValueError:
        return None, "invalid_json"
    if not isinstance(obj, dict) or set(obj) != KEYS:
        return None, "wrong_keys"
    if obj["intent"] not in INTENTS:
        return None, "bad_intent"
    low = text.casefold()
    for slot in ("date", "time", "place"):
        v = obj[slot]
        if v is not None and (not isinstance(v, str) or v.casefold() not in low):
            return None, "slot_not_in_text"
    return obj, None


def clean(records):
    counts = {"input": 0, "invalid_json": 0, "wrong_keys": 0, "bad_intent": 0, "slot_not_in_text": 0, "duplicates": 0, "kept": 0}
    kept, seen = [], set()
    for rec in records:
        counts["input"] += 1
        obj, reason = check(rec["text"], rec.get("teacher_raw", rec.get("raw", "")))
        if reason:
            counts[reason] += 1
            continue
        key = " ".join(rec["text"].casefold().split())  # duplicate COMMAND; the smallest id is seen first (ids sorted)
        if key in seen:
            counts["duplicates"] += 1
            continue
        seen.add(key)
        kept.append({"id": rec["id"], "text": rec["text"], **obj})
        counts["kept"] += 1
    return kept, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", nargs="+", required=True)
    ap.add_argument("--out", default="datasets/v1/train.jsonl")
    ap.add_argument("--counts-out", default="results/clean_counts.json")
    ap.add_argument("--s3", action="store_true", help="read shards from / write results to the datasets bucket")
    a = ap.parse_args()
    if a.s3:
        import boto3

        s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"])
        texts = [s3.get_object(Bucket="datasets", Key=f"teacher/{pathlib.Path(p).name}")["Body"].read().decode("utf-8") for p in a.shards]
    else:
        texts = [pathlib.Path(p).read_text(encoding="utf-8") for p in a.shards]
    recs = [json.loads(l) for t in texts for l in t.splitlines() if l.strip()]
    recs.sort(key=lambda r: r["id"])
    kept, counts = clean(recs)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_suffix(".sha256").write_text(f"{digest}  {out.name}\n")
    pathlib.Path(a.counts_out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.counts_out).write_text(json.dumps(counts, indent=2))
    print(counts, digest)


if __name__ == "__main__":
    main()
