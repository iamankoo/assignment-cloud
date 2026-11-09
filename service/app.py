"""Command-parser inference service (Task 3).

Env: MODEL_URI (s3://bucket/prefix), MODEL_VERSION, S3_ENDPOINT, MAX_NEW_TOKENS, FAULT_INJECT.
Credentials (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY) come from a Kubernetes Secret.
The model is downloaded from object storage at start-up; weights are not in the image.
"""
import json
import logging
import os
import pathlib
import threading

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from jsonschema import ValidationError, validate
from pydantic import BaseModel

SCHEMA = json.loads((pathlib.Path(__file__).parent / "schema.json").read_text())
PROMPT = "Command: {text}\nJSON:"

log = logging.getLogger("command-parser")
app = FastAPI()
_state = {"ready": False, "generate": None}


class ParseRequest(BaseModel):
    text: str


def _download(model_uri: str, dest: str) -> None:
    import boto3

    bucket, _, prefix = model_uri.removeprefix("s3://").partition("/")
    s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"])
    os.makedirs(dest, exist_ok=True)
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            name = obj["Key"][len(prefix):].lstrip("/")
            if name:
                s3.download_file(bucket, obj["Key"], os.path.join(dest, name))


def _load_model():
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dest = "/tmp/model"
    _download(os.environ["MODEL_URI"], dest)
    tok = AutoTokenizer.from_pretrained(dest)
    model = AutoModelForCausalLM.from_pretrained(dest).eval()
    max_new = int(os.environ.get("MAX_NEW_TOKENS", "64"))

    def generate(text: str) -> str:
        ids = tok(PROMPT.format(text=text), return_tensors="pt")
        out = model.generate(**ids, max_new_tokens=max_new, do_sample=False, pad_token_id=tok.eos_token_id)
        return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    _state["generate"] = generate
    _state["ready"] = True


def _load_guarded():
    """Load in a background thread; a failure keeps /readyz at 503 and is logged instead of silently killing the thread."""
    try:
        _load_model()
    except Exception:
        log.exception("model load failed; service stays not-ready")


@app.on_event("startup")
def _startup():
    if os.environ.get("MODEL_URI"):  # tests inject _state["generate"] directly
        threading.Thread(target=_load_guarded, daemon=True).start()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return JSONResponse({"ready": _state["ready"]}, status_code=200 if _state["ready"] else 503)


@app.post("/parse")
def parse(req: ParseRequest):
    if not _state["ready"]:
        return JSONResponse({"error": "model_not_ready"}, status_code=503)
    raw = "not json" if os.environ.get("FAULT_INJECT") == "1" else _state["generate"](req.text)
    try:
        obj = json.loads(raw)
        validate(obj, SCHEMA)
    except (ValueError, ValidationError):
        return JSONResponse({"error": "invalid_model_output"}, status_code=500)
    return Response(
        content=json.dumps(obj),
        media_type="application/json",
        headers={
            "X-Model-Version": os.environ.get("MODEL_VERSION", "unknown"),
            "X-Served-By": os.environ.get("POD_NAME", os.environ.get("HOSTNAME", "local")),
        },
    )
