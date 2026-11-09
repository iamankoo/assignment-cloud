"""Run the REAL FastAPI app (service/app.py) with a deterministic STUB generator instead of Pythia-70M.

Purpose: let a reviewer exercise /healthz, /readyz, /parse, the response headers, schema validation, FAULT_INJECT and the
Locust file on a laptop without Docker, a model or object storage. The stub is a tiny keyword rule set. Its output says
NOTHING about model quality, and any latency or throughput measured against it is NOT a performance result for the real service.

Usage: python tools/demo_server.py [--port 8000]
MODEL_VERSION / POD_NAME / FAULT_INJECT behave exactly as in the service.
"""
import argparse
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(p) for p in (_ROOT / "service", _ROOT / "src" / "service") if p.is_dir()]  # repository layout or ZIP layout
import app as svc  # noqa: E402

RULES = [("weather", "weather_query"), ("alarm", "alarm_set"), ("calendar", "calendar_set"),
         ("what time", "datetime_query"), ("events", "recommendation_events")]


def stub_generate(text: str) -> str:
    low = text.lower()
    intent = next((i for k, i in RULES if k in low), "datetime_query")
    place = low.rsplit(" in ", 1)[1] if " in " in low else None
    return json.dumps({"intent": intent, "date": None, "time": None, "place": place})


def install_stub():
    svc._state["generate"] = stub_generate
    svc._state["ready"] = True
    return svc.app


if __name__ == "__main__":
    import uvicorn

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    uvicorn.run(install_stub(), host="127.0.0.1", port=ap.parse_args().port, log_level="warning")
