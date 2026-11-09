"""Tests for the reported-figures check and the SeaweedFS / CI configuration described in the reflection."""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts")]  # slo.py, cost.py, check_reported_cost.py

import check_reported_cost as crc  # noqa: E402


def test_reported_cost_discrepancy_is_detected():
    r = crc.check(7.90, 2052.0, 3.95)
    assert abs(r["calculated_cost_per_1000"] - 3.8499) < 1e-3
    assert not r["agrees_within_0.5pct"]
    assert abs(r["requests_per_hour_implied_by_reported_cost"] - 2000.0) < 1e-6


def test_consistent_figures_pass():
    assert crc.check(7.90, 2000.0, 3.95)["agrees_within_0.5pct"]


def test_seaweedfs_manifest_matches_described_config():
    docs = [d for d in yaml.safe_load_all((ROOT / "cluster" / "seaweedfs.yaml").read_text()) if d]
    pvc = next(d for d in docs if d["kind"] == "PersistentVolumeClaim")
    dep = next(d for d in docs if d["kind"] == "Deployment")
    c = dep["spec"]["template"]["spec"]["containers"][0]
    assert pvc["spec"]["resources"]["requests"]["storage"] == "2Gi"
    assert c["resources"]["limits"]["memory"] == "1536Mi"  # 1.5 GiB
    assert any(m["mountPath"] == "/data" for m in c["volumeMounts"])


def test_ci_stage_order_and_quality_gate():
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    jobs = wf["jobs"]
    assert {"lint", "unit-tests", "evaluate", "quality-gate", "secret-scan"} <= set(jobs)
    assert jobs["unit-tests"]["needs"] == "lint"
    assert jobs["evaluate"]["needs"] == "unit-tests" and jobs["quality-gate"]["needs"] == "evaluate"
    gate = " ".join(str(s.get("run", "")) for s in jobs["quality-gate"]["steps"])
    assert "--min-validity 95" in gate
    assert "--min-validity" not in " ".join(str(s.get("run", "")) for s in jobs["evaluate"]["steps"])


def test_slo_error_budget():
    import slo

    r = slo.error_budget(1000, 7, 99.0)
    assert abs(r["budget_requests"] - 10.0) < 1e-9 and abs(r["budget_used_pct"] - 70.0) < 1e-9 and r["slo_met"]
    assert not slo.error_budget(100, 2, 99.0)["slo_met"]  # budget 1.0 request


def test_cost_formula_matches_worked_example():
    import cost

    hourly, per_hour, per_1000 = cost.cost_per_1000(2, 1.0, 1.0, 3.50, 0.45, 0.5)
    assert abs(hourly - 7.90) < 1e-9 and per_hour == 1800.0
    assert abs(per_1000 - 7.90 / 1800 * 1000) < 1e-9  # 4.3889 INR


def test_rate_card_example_is_labelled_hypothetical():
    import json

    card = json.loads((ROOT / "data" / "rate_card.example.json").read_text())
    assert "HYPOTHETICAL" in card["_comment"] and card["cpu_per_hour"] == 3.50 and card["memory_gib_per_hour"] == 0.45


def test_reliability_objects_in_app_manifest():
    docs = {d["kind"]: d for d in yaml.safe_load_all((ROOT / "k8s" / "app.yaml").read_text()) if d}
    pdb = docs["PodDisruptionBudget"]["spec"]
    assert pdb["minAvailable"] == 1 and pdb["selector"]["matchLabels"] == {"app": "command-parser"}
    assert docs["HorizontalPodAutoscaler"]["spec"]["behavior"]["scaleDown"]["stabilizationWindowSeconds"] == 60
    strat = docs["Deployment"]["spec"]["strategy"]["rollingUpdate"]
    assert strat["maxUnavailable"] == 0 and strat["maxSurge"] == 1
    assert docs["Deployment"]["spec"]["template"]["spec"]["terminationGracePeriodSeconds"] == 30


def test_dockerfiles_run_as_non_root_without_weights():
    found = [p for p in list(ROOT.rglob("Dockerfile*")) if ".git" not in p.parts]
    assert len(found) == 2
    for p in found:
        text = p.read_text()
        assert "USER 10001" in text and "COPY" in text and ".safetensors" not in text and "models/" not in text
