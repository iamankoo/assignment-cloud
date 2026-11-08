import json
import pathlib
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "service"), str(ROOT / "tools"), str(ROOT / "scripts")]

from fastapi.testclient import TestClient  # noqa: E402

import app as svc  # noqa: E402
import nacl_eval  # noqa: E402
import subnet_calc  # noqa: E402

GOOD = '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("FAULT_INJECT", raising=False)
    monkeypatch.setitem(svc._state, "ready", True)
    monkeypatch.setitem(svc._state, "generate", lambda text: GOOD)
    monkeypatch.setenv("MODEL_VERSION", "vtest")
    return TestClient(svc.app)


def test_parse_ok_and_headers(client):
    r = client.post("/parse", json={"text": "what is the weather in london"})
    assert r.status_code == 200
    assert r.json() == json.loads(GOOD)
    assert r.headers["x-model-version"] == "vtest"
    assert "x-served-by" in r.headers


def test_invalid_output_is_500(client, monkeypatch):
    monkeypatch.setitem(svc._state, "generate", lambda t: '{"intent": "bogus", "date": null, "time": null, "place": null}')
    r = client.post("/parse", json={"text": "x"})
    assert r.status_code == 500 and r.json() == {"error": "invalid_model_output"}


def test_extra_key_rejected(client, monkeypatch):
    monkeypatch.setitem(svc._state, "generate", lambda t: '{"intent": "alarm_set", "date": null, "time": null, "place": null, "x": 1}')
    assert client.post("/parse", json={"text": "x"}).status_code == 500


def test_fault_inject(client, monkeypatch):
    monkeypatch.setenv("FAULT_INJECT", "1")
    r = client.post("/parse", json={"text": "x"})
    assert r.status_code == 500 and r.json() == {"error": "invalid_model_output"}


def test_health_and_ready(monkeypatch):
    c = TestClient(svc.app)
    monkeypatch.setitem(svc._state, "ready", False)
    assert c.get("/healthz").status_code == 200
    assert c.get("/readyz").status_code == 503
    monkeypatch.setitem(svc._state, "ready", True)
    assert c.get("/readyz").status_code == 200


def test_subnets():
    got = {n: str(net) for n, _, net in subnet_calc.allocate("10.20.0.0/16", [("app", 1000), ("public", 250), ("data", 100), ("management", 20)])}
    assert got == {"app": "10.20.0.0/22", "public": "10.20.4.0/24", "data": "10.20.5.0/25", "management": "10.20.5.128/27"}


def test_nacl_packets():
    rules = json.loads((ROOT / "network/nacl.json").read_text())
    for line in (ROOT / "network/packets_own.jsonl").read_text().splitlines():
        p = json.loads(line)
        assert nacl_eval.decide(rules[p["direction"]], p["protocol"], p["port"], p["address"])[0] == p["expected"], p["id"]


def test_nacl_deny_precedes_web_allows():
    rules = json.loads((ROOT / "network/nacl.json").read_text())["inbound"]
    deny = next(r for r in rules if r["cidr"] == "198.51.100.0/24")
    web = [r["rule"] for r in rules if r["action"] == "allow" and r["port_from"] in (80, 443)]
    assert deny["action"] == "deny" and all(deny["rule"] < w for w in web)


def test_k8s_manifest_fields():
    docs = {d["kind"]: d for d in yaml.safe_load_all((ROOT / "k8s/app.yaml").read_text()) if d}
    dep = docs["Deployment"]
    c = dep["spec"]["template"]["spec"]["containers"][0]
    assert dep["metadata"]["namespace"] == "app" and dep["spec"]["replicas"] == 2
    assert c["resources"]["limits"] and c["resources"]["requests"]
    assert c["livenessProbe"] and c["readinessProbe"]
    h = docs["HorizontalPodAutoscaler"]["spec"]
    assert (h["minReplicas"], h["maxReplicas"]) == (1, 2)
    assert h["metrics"][0]["resource"]["target"]["averageUtilization"] == 70
