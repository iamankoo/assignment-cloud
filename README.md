# Cloud-Assignment: Command-Parser Knowledge Distillation on a Local Cloud

**Aniket Raj** · Roll no. 230103030 · GitHub `iamankoo` · aniketraj00384@gmail.com · CS3081 Cloud Computing mini project

A lightweight English command parser: a small student model (EleutherAI/Pythia-70M) is fine-tuned on JSON labels produced by a larger
teacher (Ollama Phi-3.5 Mini) and served by a containerised FastAPI service on a local Kubernetes (k3d) cluster with SeaweedFS object storage.

> **Branch note.** This is the `mock/nanoparse-style` branch, a presentation draft that follows the layout of a public reference project
> (rahul-singh92/NanoParse) for README structure and directory organisation only. **All code here is my own and *not run* unless a result is
> shown in the status table; no code, text or results were copied from the reference, and none of its results are reported.** `main` is unchanged.
> No `final` tag exists.

## Status (honest)

| Task | State | Evidence in `results/` |
|---|---|---|
| 1 Object storage + parallel teacher labelling | Code written (`worker/`, `k8s/worker-job.yaml`, `cluster/seaweedfs.yaml`, `prompts/`); cleaning logic unit-tested on toy data; **labelling not run** | none |
| 2 Student training | Code written (`training/`, `tools/predict.py`); **not run**; config values are planned settings | none |
| 3 Inference service | Implemented; 5 API tests pass with a stub model; Docker image **not built** | `pytest_local.txt` |
| 4 Kubernetes | Manifests written; YAML fields tested; **never applied** | `pytest_local.txt` |
| 5 Networking | Implemented and tested with my own evaluator (11/11) | `nacl_eval_local.txt`, `subnet_calc_local.txt` |
| 6 CI/CD | Workflow file written, **never run**; Release gate not implemented; `make up` written, **not run** | none |
| 7 Performance, cost, review | Locust file and cost script written, **not run**; no measurements | none |

Tests run locally (Python 3.10, Windows): **14 passed**, pyflakes clean, own NACL evaluator 11/11.

## Architecture

```text
Natural-language command
        |
        v
   FastAPI service  <-- model downloaded at start-up from SeaweedFS (s3://models/<version>)
        |
        v
 Fine-tuned Pythia-70M  (prompt: "Command: <text>\nJSON:")
        |
        v
 JSON-schema validation  --invalid--> HTTP 500 {"error":"invalid_model_output"}
        |
        v
 {"intent","date","time","place"} + X-Model-Version, X-Served-By

Offline pipeline:
 commands_pool.jsonl -> SeaweedFS[datasets] -> 2 parallel teacher Jobs (shard = n mod 2, Ollama Phi-3.5)
   -> worker/clean.py -> datasets/v1/train.jsonl (+SHA-256) -> training/train.py (first 1,500) -> model v1/v2
   -> GitHub Release + SeaweedFS[models]
Runtime: k3d (ns app): Deployment x2 -> Service :80 -> Traefik Ingress ; HPA 1..2 @ 70% CPU
```

## Technology stack
Teacher Ollama Phi-3.5 Mini · Student EleutherAI/Pythia-70M · PyTorch + Transformers · FastAPI + Uvicorn · SeaweedFS (S3) · Docker ·
Kubernetes via k3d (Traefik Ingress, HPA) · Locust · GitHub Actions + Gitleaks · Python `ipaddress` for subnetting.

## Repository structure

| Path | Purpose |
|---|---|
| `data/`, `datasets/` | Kit data (`commands_pool`, `validation`, `schema`, `rate_card`: **not in repo yet**) and cleaned training data |
| `prompts/` | Teacher prompt |
| `worker/` | `teacher_worker.py` (sharded labelling), `clean.py`, Dockerfile |
| `training/` | `config.yaml`, `train.py` |
| `service/` | FastAPI app, `schema.json`, Dockerfile, pinned requirements |
| `cluster/` | k3d and SeaweedFS configuration |
| `k8s/` | App Deployment/Service/Ingress/HPA (`app.yaml`), labelling Job |
| `network/` | `subnets.md`, `nacl.json`, own sample packets |
| `tools/` | `nacl_eval.py`, `predict.py`, `locustfile.py` (the kit's `score.py` and `nacl_sim.py` are not included) |
| `scripts/` | `deploy.sh`, `destroy.sh`, `upload.py`, `cost.py`, `subnet_calc.py` |
| `tests/` | 14 unit tests |
| `docs/STUDY_GUIDE.md`, `report/` | Task-by-task explanation; technical report |
| `results/` | Local logs of what was actually run |
| `reflection/` | Scanned handwritten reflection |

## Requirements
Docker, k3d, kubectl, Python 3.11, GNU Make, GitHub CLI, Ollama with `phi3.5`, Locust. (The machine used so far had Python only.)

## Setup
```bash
git clone https://github.com/iamankoo/Cloud-Assignment.git && cd Cloud-Assignment
python -m venv .venv && source .venv/bin/activate
pip install fastapi httpx pydantic jsonschema pyyaml pytest pyflakes boto3 requests locust
cp .env.example .env        # local dev secret; never commit .env
```

## Teacher labelling and object storage (Task 1) — NOT RUN
```bash
make up                                                     # cluster + SeaweedFS + images + app
python scripts/upload.py --bucket datasets --src data/commands_pool.jsonl --key commands_pool.jsonl
make label                                                  # Indexed Job, 2 pods, shard = n mod 2
make clean-data                                             # counts + SHA-256
```
Cleaning rejects: invalid JSON, wrong keys, intent outside the eight, slot value not in the command, duplicates. Identity: input = kept + rejected (unit-tested).

## Student training (Task 2) — NOT RUN
Planned configuration (`training/config.yaml`): Pythia-70M, first 1,500 cleaned records, 3 epochs, batch 8, lr 5e-5, AdamW weight decay 0.01, max length 128, seed 42, CPU.
Loss is cross-entropy on the JSON answer only (sequence-level distillation).
```bash
make train SUBSET=50     # smoke test
make train VERSION=v1
make train VERSION=v2    # second version for the rollout
```

## Evaluation (Task 2) — no results yet
```bash
python tools/predict.py --model training/output/v1 --input data/validation.jsonl --out results/pred_v1.jsonl
python tools/score.py results/pred_v1.jsonl data/validation.jsonl --out results/score_v1.json --min-validity 95   # kit script
```
| Model | JSON validity | Intent | Date | Time | Place | Full frame |
|---|---|---|---|---|---|---|
| Teacher | not measured | | | | | |
| Untrained Pythia-70M | not measured | | | | | |
| Student v1 | not measured | | | | | |

## FastAPI and Docker (Task 3)
`POST /parse`, `GET /healthz`, `GET /readyz` (503 until loaded); `FAULT_INJECT=1` forces invalid output. Config via `MODEL_URI`, `MODEL_VERSION`, `S3_ENDPOINT`, `MAX_NEW_TOKENS`; credentials from a Secret.
```bash
docker build -f service/Dockerfile -t command-parser:v1 .     # NOT RUN: size must be <= 2 GB
```

## Kubernetes and scaling (Task 4) — manifests only
Namespace `app`, 2 replicas, requests 250m/512Mi, limits 1 CPU/1Gi, liveness `/healthz`, readiness `/readyz`, RollingUpdate (maxUnavailable 0), HPA 1..2 at 70% CPU.
Rollout/rollback: `kubectl -n app set env deploy/command-parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2` then `kubectl -n app rollout undo deploy/command-parser`. Not executed.

## Networking and NACL (Task 5) — done
10.20.0.0/16: app 10.20.0.0/22, public 10.20.4.0/24, data 10.20.5.0/25, management 10.20.5.128/27 (`network/subnets.md`). NACL in `network/nacl.json`.
```bash
make subnets && make nacl
```

## CI/CD and testing (Task 6)
`.github/workflows/ci.yml`: pyflakes, pytest, gitleaks. Not implemented: Release-based evaluation and the 95% gate with a deliberately failing run. No CI run exists yet.
```bash
make lint && make test     # 14 passed locally
```

## Performance, cost and reliability (Task 7) — no measurements
```bash
make load      # 4 users, 2 minutes
python scripts/cost.py --rate-card data/rate_card.json --replicas 2 --cpu 1 --mem-gib 1 --rps <measured>
```
Cost per 1,000 requests = hourly cost / (throughput × 3600) × 1000. All values pending.

## Shutdown
```bash
make down
```

## Limitations and future work
Tasks 1, 2 and 7 have no executed results; the Docker image, cluster, CI and gate are unverified; the kit's `score.py`, `nacl_sim.py` and data are not included.
Next: run the pipeline end to end, publish v1/v2 as Release assets, add the Release-based CI gate, collect Locust/CPU/memory/cold-start data, fill the review table.

More detail: [`docs/STUDY_GUIDE.md`](docs/STUDY_GUIDE.md), [`report/report.pdf`](report/report.pdf), [`AI_USE.md`](AI_USE.md).
