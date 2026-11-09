"""Unit tests for the labelling/cleaning/training helpers. They use hand-written toy records only (no teacher data)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "worker"), str(ROOT / "service")]

import clean  # noqa: E402
import teacher_worker as tw  # noqa: E402


def rec(i, text, raw):
    return {"id": f"C{i}", "text": text, "teacher_raw": raw}


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


def test_clean_dedupes_by_command_text_and_keeps_smallest_id():
    a = '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'
    recs = [rec(1, "what is the weather in london", a), rec(2, "What is  the weather in London", a.replace("weather_query", "datetime_query"))]
    kept, c = clean.clean(recs)
    assert [k["id"] for k in kept] == ["C1"] and c["duplicates"] == 1  # same command, different label -> still a duplicate


def test_clean_reads_teacher_raw_and_legacy_raw_field():
    assert clean.clean([{"id": "C1", "text": "weather in london", "teacher_raw": GOOD}])[1]["kept"] == 1
    assert clean.clean([{"id": "C1", "text": "weather in london", "raw": GOOD}])[1]["kept"] == 1


def test_worker_output_field_name_is_teacher_raw():
    src = (ROOT / "worker" / "teacher_worker.py").read_text()
    assert '"teacher_raw": raw' in src and "temperature" in src and '"seed": 42' in src


def test_clean_cli_writes_sorted_output_and_checksum(tmp_path):
    import hashlib
    import json
    import subprocess

    shard0 = tmp_path / "shard-0.jsonl"
    shard1 = tmp_path / "shard-1.jsonl"
    shard0.write_text(json.dumps({"id": "C0002", "text": "weather in london", "teacher_raw": GOOD}) + chr(10))
    shard1.write_text(json.dumps({"id": "C0001", "text": "weather in london today", "teacher_raw": GOOD}) + chr(10))
    out, counts = tmp_path / "v1" / "train.jsonl", tmp_path / "counts.json"
    script = next(pathlib.Path(clean.__file__).resolve().parent.glob("clean.py"))
    subprocess.run([sys.executable, str(script), "--shards", str(shard0), str(shard1), "--out", str(out), "--counts-out", str(counts)], check=True, capture_output=True)
    ids = [json.loads(line)["id"] for line in out.read_text().splitlines()]
    assert ids == ["C0001", "C0002"]
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    assert (tmp_path / "v1" / "train.sha256").read_text().split()[0] == digest
    assert json.loads(counts.read_text())["kept"] == 2


def test_training_config_records_required_items():
    import yaml

    cfg = yaml.safe_load((ROOT / "training" / "config.yaml").read_text())
    for key in ("seed", "learning_rate", "batch_size", "epochs", "max_seq_len", "libraries"):
        assert key in cfg
    assert {"torch", "transformers"} <= set(cfg["libraries"])
    src = (ROOT / "training" / "train.py").read_text()
    assert "torch.manual_seed(seed)" in src and '"loss.csv"' in src


def test_demo_server_serves_real_app_with_stub_model():
    import importlib.util

    from fastapi.testclient import TestClient

    path = next(ROOT.glob("*/demo_server.py"))
    spec = importlib.util.spec_from_file_location("demo_server", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    c = TestClient(mod.install_stub())
    r = c.post("/parse", json={"text": "what is the weather in london"})
    assert r.status_code == 200 and r.json()["intent"] == "weather_query" and r.json()["place"] == "london"
    assert set(r.json()) == {"intent", "date", "time", "place"} and "x-served-by" in r.headers


def test_package_model_refuses_empty_and_is_deterministic(tmp_path):
    import hashlib
    import importlib.util
    import json
    import tarfile

    path = next(ROOT.rglob("package_model.py"))
    spec = importlib.util.spec_from_file_location("package_model", path)
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    empty = tmp_path / "empty"
    empty.mkdir()
    try:
        pm.package(empty, "v1", tmp_path / "dist")
        raise AssertionError("must refuse an empty model dir")
    except SystemExit:
        pass
    assert not (tmp_path / "dist" / "v1.tar.gz").exists()
    m = tmp_path / "m"
    m.mkdir()
    (m / "model.safetensors").write_bytes(b"toy-bytes-not-a-model")  # synthetic test fixture, not a model
    (m / "config.json").write_text("{}")
    a = pm.package(m, "v1", tmp_path / "d1")
    b = pm.package(m, "v1", tmp_path / "d2")
    assert a["sha256"] == b["sha256"] == hashlib.sha256((tmp_path / "d1" / "v1.tar.gz").read_bytes()).hexdigest()
    assert (tmp_path / "d1" / "v1.tar.gz.sha256").read_text().split()[0] == a["sha256"]
    assert "v1" in json.loads((tmp_path / "d1" / "release_manifest.json").read_text())
    with tarfile.open(tmp_path / "d1" / "v1.tar.gz") as t:
        assert sorted(t.getnames()) == ["v1/config.json", "v1/model.safetensors"]


def test_predict_teacher_uses_worker_prompt_and_exact_reply():
    import importlib.util

    path = next(ROOT.rglob("predict_teacher.py"))
    spec = importlib.util.spec_from_file_location("predict_teacher", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    seen = []

    def fake_ask(host, model, prompt):
        seen.append((host, model, prompt))
        return " raw reply "

    out = mod.predict_all([{"id": "V001", "text": "hello"}], "Q: {text}", "h", "phi3.5", ask=fake_ask)
    assert out == [{"id": "V001", "prediction": " raw reply "}] and seen[0][2] == "Q: hello"


def test_seaweedfs_has_probes_and_limit():
    import yaml

    docs = [d for d in yaml.safe_load_all((ROOT / "cluster" / "seaweedfs.yaml").read_text()) if d]
    c = next(d for d in docs if d["kind"] == "Deployment")["spec"]["template"]["spec"]["containers"][0]
    assert c["readinessProbe"] and c["livenessProbe"] and c["resources"]["limits"]["memory"] == "1536Mi"
