# Cloud-Assignment

**Cloud-Assignment** is a lightweight natural-language command parser that converts user instructions into structured JSON. It uses sequence-level knowledge distillation to fine-tune a compact Pythia-70M student model on teacher-generated training data, then serves the model through a containerised FastAPI application deployed on Kubernetes.

**Aniket Raj** · Roll No. 230103030 · GitHub: [iamankoo](https://github.com/iamankoo) · Email: aniketraj00384@gmail.com · CS3081 Cloud Computing Mini Project

## Status and what has actually been run

| Task | State | Evidence |
|---|---|---|
| 1. Object storage + parallel teacher labelling | Code written (`worker/`, `k8s/worker-job.yaml`, `cluster/`, `prompts/`); cleaning logic unit-tested on toy data; **labelling not run** | none |
| 2. Student training (Pythia-70M) | Code written (`training/`, `tools/predict.py`); **not run**; settings in `training/config.yaml` are planned values | none |
| 3. FastAPI service + Docker | Service implemented; API tests pass with a stub model; **Docker image not built** | `results/pytest_local.txt` |
| 4. Kubernetes | Manifests written; YAML fields unit-tested; **never applied to a cluster** | `results/pytest_local.txt` |
| 5. Networking + NACL | Implemented; subnet plan and own NACL evaluator tested (11/11) | `results/subnet_calc_local.txt`, `results/nacl_eval_local.txt` |
| 6. CI/CD | Workflow written, **never run**; `make up`/`make down` written, **not run**; Release-based 95% gate **not implemented** | none |
| 7. Performance, cost, review | Locust file and cost script written, **not run**; **no measurements exist** | none |

Local verification (Python 3.10, Windows): 14 unit tests passed, pyflakes clean. Nothing else has been executed: no teacher labelling, training, Docker build, cluster deployment, CI run or load test. **This repository contains no experimental results.** The instructor's `student_kit` files (`commands_pool.jsonl`, `validation.jsonl`, `score.py`, `nacl_sim.py`, `rate_card.json`) are not included.

## Architecture

```text
Natural Language Input
        |
        v
   FastAPI Service   (model downloaded at start-up from SeaweedFS)
        |
        v
Fine-tuned Pythia-70M
        |
        v
JSON Validation  --invalid-->  HTTP 500 {"error":"invalid_model_output"}
        |
        v
Structured Response  (+ X-Model-Version, X-Served-By)

Offline pipeline:
 commands_pool.jsonl -> SeaweedFS [datasets] -> 2 parallel teacher Jobs (shard = n mod 2, Ollama Phi-3.5)
   -> worker/clean.py -> train.jsonl (+SHA-256) -> training/train.py (first 1,500 records) -> model v1 / v2

Model Storage: SeaweedFS (S3-compatible)
Orchestration: Kubernetes (k3d), Traefik Ingress
Scaling: Horizontal Pod Autoscaler (1-2 replicas, 70% CPU)
Monitoring: Locust and kubectl metrics
```

## Technology Stack

- **Student model:** EleutherAI/Pythia-70M
- **Teacher:** Ollama Phi-3.5 Mini Instruct
- **ML framework:** PyTorch and Transformers
- **API:** FastAPI and Uvicorn
- **Object storage:** SeaweedFS (S3-compatible)
- **Containerisation:** Docker
- **Orchestration:** Kubernetes using k3d
- **Load testing:** Locust
- **CI/CD:** GitHub Actions (pyflakes, pytest) and Gitleaks

## Repository Structure

| Path | Purpose |
|---|---|
| `worker/` | Teacher labelling worker, cleaning script, worker Dockerfile |
| `prompts/` | Teacher prompt |
| `training/` | Student training configuration and script |
| `service/` | FastAPI application, JSON schema, Dockerfile, pinned requirements |
| `cluster/` | k3d and SeaweedFS configuration |
| `k8s/` | Application Deployment, Service, Ingress, HPA; labelling Job |
| `network/` | Subnet plan, NACL rules, sample packets |
| `tools/` | NACL evaluator, prediction script, Locust file |
| `scripts/` | Deployment, teardown, upload, subnet and cost scripts |
| `tests/` | Unit tests |
| `docs/` | Study guide, setup instructions, release metadata |
| `results/` | Logs of what was actually run |
| `report/`, `reflection/` | Technical report and handwritten reflection |

## Requirements

- Docker, k3d, kubectl
- Python 3.11 (3.10 was used for the local tests)
- GNU Make
- Locust for load testing
- Ollama with `phi3.5` for teacher labelling

Not all of these were available on the machine used so far (only Python).

## Setup

```bash
git clone https://github.com/iamankoo/Cloud-Assignment.git
cd Cloud-Assignment
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi httpx pydantic jsonschema pyyaml pytest pyflakes boto3 requests locust
cp .env.example .env
```

## Model Training (planned, not run)

The student model is based on EleutherAI/Pythia-70M. Settings in `training/config.yaml`:

- Maximum training samples: 1,500 (first 1,500 cleaned records)
- Epochs: 3, batch size: 8, learning rate: 0.00005
- Maximum sequence length: 128
- AdamW weight decay 0.01, gradient clipping 1.0
- Execution device: CPU, random seed: 42

```bash
make train SUBSET=50     # smoke test
make train VERSION=v1
make train VERSION=v2    # second version for the rollout (use --seed to differ)
```

Training outputs go to `training/output/` and are excluded from Git.

## Evaluation (planned, not run)

```bash
python tools/predict.py --model training/output/v1 --input data/validation.jsonl --out results/pred_v1.jsonl
python tools/score.py results/pred_v1.jsonl data/validation.jsonl --out results/score_v1.json --min-validity 95
```

`tools/score.py` is the instructor's script and is not included here. It reports JSON validity, intent, date, time, place and full-frame accuracy. No scores have been produced.

## Deployment (not run)

```bash
make up          # cluster, SeaweedFS, images, application
```

`scripts/deploy.sh` creates the k3d cluster, applies SeaweedFS and the Secrets from `.env`, builds and imports the images and applies `k8s/app.yaml`. Models must already be in the `models` bucket (`python scripts/upload.py --bucket models --src training/output/v1 --key v1`). Downloading models from a GitHub Release is not implemented.

API endpoint: `http://localhost:8080/parse`

## API Usage

```bash
curl -X POST http://localhost:8080/parse \
  -H "Content-Type: application/json" \
  -d '{"text":"set an alarm for seven thirty am tomorrow"}'
```

Expected response shape (the content depends on the model):

```json
{"intent": "alarm_set", "date": "tomorrow", "time": "seven thirty am", "place": null}
```

- `GET /healthz`: process health
- `GET /readyz`: 503 until the model is loaded
- `POST /parse`: command parsing; invalid model output returns HTTP 500 `invalid_model_output`; `FAULT_INJECT=1` forces invalid output

## Kubernetes and Load Testing (not run)

`k8s/app.yaml`: namespace `app`, 2 replicas, requests 250m/512Mi, limits 1 CPU/1Gi, liveness `/healthz`, readiness `/readyz`, RollingUpdate (maxUnavailable 0), Service, Ingress, HPA 1-2 replicas at 70% CPU.

Standard Locust test:

```bash
make load      # 4 users, 2 minutes, http://localhost:8080
kubectl top pods -n app
kubectl get pods,svc,hpa -n app
```

Cost per 1,000 requests = hourly cost / (throughput x 3600) x 1000 (`scripts/cost.py`). No measurements exist yet.

## Network Configuration

`network/` holds the subnet plan (`subnets.md`), NACL rules (`nacl.json`), and 11 hand-written packets (`packets_own.jsonl`).

| Subnet | Hosts | Network |
|---|---:|---|
| app | 1,000 | 10.20.0.0/22 |
| public | 250 | 10.20.4.0/24 |
| data | 100 | 10.20.5.0/25 |
| management | 20 | 10.20.5.128/27 |

```bash
python tools/nacl_eval.py network/nacl.json network/packets_own.jsonl   # my own evaluator: 11/11 as expected
python scripts/subnet_calc.py
```

The instructor's `nacl_sim.py` and its six sample packets are not in this repository and were not run.

## Automated Testing and CI

`.github/workflows/ci.yml` defines: (1) pyflakes lint, (2) pytest unit tests, (3) Gitleaks secret scanning. It has never run. The model evaluation stage and the 95% JSON-validity gate are not implemented.

```bash
make lint && make test     # 14 passed locally
```

## Model Artifacts

Weights are never committed to Git. The GitHub Release [`reference-nanoparse-v1.0`](https://github.com/iamankoo/Cloud-Assignment/releases/tag/reference-nanoparse-v1.0) holds two Pythia-70M archives and their checksum files. **They are externally sourced reference artifacts** from `rahul-singh92/NanoParse` release `v1.0` (author Rahul Singh Jadoun), re-uploaded unmodified. They were **not trained or evaluated in this repository** and are not my training output. See `docs/RELEASE_METADATA.md`.

## Provenance and AI Use

All code in this repository was written for this project (with Claude Code assistance) and was not copied from another project. See [AI_USE.md](AI_USE.md) for AI-assisted development, human oversight and known limitations.

## Cleanup

```bash
make down      # deletes the k3d cluster (only works after `make up`)
```

## Limitations and Future Improvements

- Tasks 1, 2 and 7 have not been executed; no results exist.
- Docker image, cluster behaviour, CI and the quality gate are unverified.
- Run the pipeline end to end, publish own v1/v2 as Release assets, add the Release-based CI gate, and collect Locust/CPU/memory/cold-start data.
- Evaluate multi-node Kubernetes deployment and replicated storage; use production-grade secret management and TLS externally.

## Project Repository

[https://github.com/iamankoo/Cloud-Assignment](https://github.com/iamankoo/Cloud-Assignment)
