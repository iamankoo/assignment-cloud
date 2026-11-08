"""Tests for the reported-figures check and the SeaweedFS / CI configuration described in the reflection."""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts")]

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


def test_ci_has_manual_quality_gate_stage():
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    assert "evaluate" in wf["jobs"] and "secret-scan" in wf["jobs"]
    steps = " ".join(str(s.get("run", "")) for s in wf["jobs"]["evaluate"]["steps"])
    assert "--min-validity 95" in steps
