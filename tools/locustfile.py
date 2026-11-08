"""Locust load test for POST /parse (Task 7). NOT RUN yet.

The assignment's student_kit supplies the official locustfile; replace this file with it before the graded run.
This version samples data/validation.jsonl and counts a request as failed unless it returns HTTP 200 (30 s timeout).
Standard command:
  locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
"""
import json
import pathlib
import random
from collections import Counter

from locust import HttpUser, between, events, task

PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "validation.jsonl"
TEXTS = [json.loads(l)["text"] for l in PATH.read_text(encoding="utf-8").splitlines() if l.strip()] if PATH.exists() else ["what is the weather in london"]
SERVED_BY, VERSIONS = Counter(), Counter()


class ParserUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def parse(self):
        with self.client.post("/parse", json={"text": random.choice(TEXTS)}, timeout=30, catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                return
            SERVED_BY[r.headers.get("X-Served-By", "?")] += 1
            VERSIONS[r.headers.get("X-Model-Version", "?")] += 1


@events.quitting.add_listener
def _dump(environment, **kw):
    pathlib.Path("results").mkdir(exist_ok=True)
    pathlib.Path("results/loadtest_headers.json").write_text(json.dumps({"per_replica": SERVED_BY, "per_model_version": VERSIONS}, indent=2))
