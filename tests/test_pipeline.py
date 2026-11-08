"""Unit tests for the labelling/cleaning/training helpers. They use hand-written toy records only (no teacher data)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "worker"), str(ROOT / "service")]

import clean  # noqa: E402
import teacher_worker as tw  # noqa: E402


def rec(i, text, raw):
    return {"id": f"C{i}", "text": text, "raw": raw}


GOOD = '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'


def test_shards_complete_disjoint_balanced():
    records = [{"id": n} for n in range(3000)]
    a, b = tw.shard_records(records, 0, 2), tw.shard_records(records, 1, 2)
    assert len(a) == len(b) == 1500
    ids = [r["id"] for r in a + b]
    assert sorted(ids) == list(range(3000)) and len(set(ids)) == 3000


def test_clean_counts_identity_and_reasons():
    recs = [
        rec(1, "what is the weather in london", GOOD),
        rec(2, "what is the weather in london", GOOD),                      # duplicate
        rec(3, "hello", "not json"),                                         # invalid json
        rec(4, "hello", '{"intent": "alarm_set"}'),                          # wrong keys
        rec(5, "hello", '{"intent": "x", "date": null, "time": null, "place": null}'),  # bad intent
        rec(6, "hello", '{"intent": "weather_query", "date": null, "time": null, "place": "paris"}'),  # invented slot
    ]
    kept, c = clean.clean(recs)
    assert len(kept) == 1 and c["kept"] == 1
    assert (c["duplicates"], c["invalid_json"], c["wrong_keys"], c["bad_intent"], c["slot_not_in_text"]) == (1, 1, 1, 1, 1)
    assert c["input"] == c["kept"] + sum(v for k, v in c.items() if k not in ("input", "kept"))


def test_prompt_matches_service():
    import app

    assert app.PROMPT == "Command: {text}\nJSON:"
    src = (ROOT / "training" / "train.py").read_text() + (ROOT / "tools" / "predict.py").read_text()
    assert src.count('PROMPT = "Command: {text}\\nJSON:"') == 2


def test_training_config_planned_values():
    import yaml

    cfg = yaml.safe_load((ROOT / "training" / "config.yaml").read_text())
    assert cfg["model_name"] == "EleutherAI/pythia-70m" and cfg["train_limit"] == 1500


def test_job_manifest_is_two_way_indexed():
    import yaml

    job = yaml.safe_load((ROOT / "k8s" / "worker-job.yaml").read_text().split("---")[1])["spec"]
    assert job["completionMode"] == "Indexed" and job["completions"] == job["parallelism"] == 2
