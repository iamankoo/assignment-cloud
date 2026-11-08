# Cloud-Assignment: Command-Parser Knowledge Distillation on a Local Cloud

**Aniket Raj** · Roll No. 230103030 · GitHub: [iamankoo](https://github.com/iamankoo) · aniketraj00384@gmail.com · CS3081 Cloud Computing Mini Project

A lightweight English command parser: a small student model (EleutherAI/Pythia-70M) is fine-tuned on JSON labels produced by a larger teacher (Ollama Phi-3.5 Mini) and served by a containerised FastAPI service on a local Kubernetes (k3d) cluster with SeaweedFS object storage.

> **Branch note:** This is the `mock/nanoparse-style` branch, a presentation draft that follows a public reference project's README structure and directory organisation only. All code here is my own and not run unless a result is shown in the status table; no code, text or results were copied from the reference, and none of its results are reported. `main` is unchanged. No `final` tag exists.

## 1. Status (Honest)

| Task | State | Evidence in `results/` |
|---|---|---|
| 1. Object storage + parallel teacher labelling | Code written (`worker/`, `k8s/worker-job.yaml`, `cluster/seaweedfs.yaml`, `prompts/`); cleaning logic unit-tested on toy data; **labelling not run** | None |
| 2. Student training | Code written (`training/`, `tools/predict.py`); **not run**; config values are planned settings | None |
| 3. Inference service | Implemented; 5 API tests pass with a stub model; Docker image **not built** | `pytest_local.txt` |
| 4. Kubernetes | Manifests written; YAML fields tested; **never applied** | `pytest_local.txt` |
| 5. Networking | Implemented and tested with my own evaluator (11/11) | `nacl_eval_local.txt`, `subnet_calc_local.txt` |
| 6. CI/CD | Workflow file written, **never run**; Release gate not implemented; `make up` written, **not run** | None |
| 7. Performance, cost, review | Locust file and cost script written, **not run**; no measurements | None |

**Local verification:** Python 3.10 on Windows; 14 tests passed, pyflakes clean, own NACL evaluator 11/11.

## 2. Architecture

```text
Natural-language command
        |
        v
   FastAPI service  <-- model downloaded at start-up from SeaweedFS (s3://models/<version>)
        |
        v
 Fine-tuned Pythia-70M (prompt: "Command: <text>\nJSON:")
        |
        v
 JSON-schema validation --invalid--> HTTP 500 {"error":"invalid_model_output"}
        |
        v
 {"intent","date","time","place"} + X-Model-Version, X-Served-By

Offline pipeline:
 commands_pool.jsonl -> SeaweedFS[datasets] -> 2 parallel teacher Jobs (shard = n mod 2, Ollama Phi-3.5)
   -> worker/clean.py -> datasets/v1/train.jsonl (+SHA-256) -> training/train.py (first 1,500) -> model v1/v2
   -> GitHub Release + SeaweedFS[models]

Runtime:
 k3d (ns app): Deployment x2 -> Service :80 -> Traefik Ingress
 HPA: 1..2 replicas @ 70% CPU
```

## 3. Technology Stack

| Component | Technology |
|---|---|
| Teacher model | Ollama Phi-3.5 Mini |
| Student model | EleutherAI/Pythia-70M |
| ML framework | PyTorch, Transformers |
| API | FastAPI, Uvicorn |
| Object storage | SeaweedFS (S3-compatible) |
| Containerisation | Docker |
| Orchestration | Kubernetes using k3d |
| Ingress and scaling | Traefik, Horizontal Pod Autoscaler |
| Load testing | Locust |
| CI/CD | GitHub Actions, Gitleaks |
| Networking | Python `ipaddress` |

## 4. Repository Structure

| Directory | Purpose |
|---|---|
| `data/`, `datasets/` | Kit data (`commands_pool`, `validation`, `schema`, `rate_card`: not in repo yet) and cleaned training data |
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

## 5. Requirements

- Docker
- k3d
- kubectl
- Python 3.11
- GNU Make
- GitHub CLI
- Ollama with `phi3.5`
- Locust

The machine used so far had Python only.

## 6. Setup

Clone the repository:

```bash
git clone https://github.com/iamankoo/Cloud-Assignment.git
cd Cloud-Assignment
```

Create and activate a Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the service and tooling dependencies:

```bash
pip install fastapi httpx pydantic jsonschema pyyaml pytest pyflakes boto3 requests locust
```

Create the local environment file:

```bash
cp .env.example .env
```

Never commit `.env` or local credentials.

## 7. Teacher Labelling and Object Storage (Task 1) — Not Run

The planned workflow uses SeaweedFS as S3-compatible object storage and two parallel Kubernetes Jobs for teacher labelling.

```bash
make up

python scripts/upload.py \
  --bucket datasets \
  --src data/commands_pool.jsonl \
  --key commands_pool.jsonl

make label
make clean-data
```

The teacher prompt is stored under `prompts/`. The worker uses Ollama Phi-3.5 Mini and divides work using `shard = n mod 2`.

The cleaning process rejects:

- Invalid JSON
- Incorrect keys
- Intents outside the eight allowed intents
- Slot values not present in the command
- Duplicate records

The cleaning logic checks the identity:

`input = kept + rejected`

This logic was unit-tested on toy data. Actual teacher labelling and dataset cleaning have not been run.

## 8. Student Training (Task 2) — Not Run

The planned student model is EleutherAI/Pythia-70M.

Planned configuration in `training/config.yaml`:

| Parameter | Value |
|---|---:|
| Training samples | First 1,500 cleaned records |
| Epochs | 3 |
| Batch size | 8 |
| Learning rate | 0.00005 |
| Optimizer | AdamW |
| Weight decay | 0.01 |
| Maximum sequence length | 128 |
| Random seed | 42 |
| Execution device | CPU |

The training objective is cross-entropy on the JSON answer sequence, using teacher-generated labels.

Planned commands:

```bash
make train SUBSET=50
make train VERSION=v1
make train VERSION=v2
```

Training has not been executed, and these configuration values are planned settings rather than measured training results.

## 9. Evaluation (Task 2) — No Results Yet

The planned prediction and evaluation workflow is:

```bash
python tools/predict.py \
  --model training/output/v1 \
  --input data/validation.jsonl \
  --out results/pred_v1.jsonl
```

The assignment-provided scoring script is not included in the current repository.

Planned evaluation command:

```bash
python tools/score.py \
  results/pred_v1.jsonl \
  data/validation.jsonl \
  --out results/score_v1.json \
  --min-validity 95
```

Evaluation metrics:

| Model | JSON validity | Intent | Date | Time | Place | Full frame |
|---|---|---|---|---|---|---|
| Teacher | Not measured | — | — | — | — | — |
| Untrained Pythia-70M | Not measured | — | — | — | — | — |
| Student v1 | Not measured | — | — | — | — | — |

## 10. FastAPI and Docker (Task 3)

The inference service exposes:

| Endpoint | Method | Purpose |
|---|---|---|
| `/parse` | POST | Parse a natural-language command |
| `/healthz` | GET | Process health |
| `/readyz` | GET | Model readiness |

The readiness endpoint returns HTTP 503 until the model is loaded.

Configuration variables:

- `MODEL_URI`
- `MODEL_VERSION`
- `S3_ENDPOINT`
- `MAX_NEW_TOKENS`

Credentials are intended to be supplied through a Kubernetes Secret.

`FAULT_INJECT=1` forces invalid model output for testing.

Build command:

```bash
docker build -f service/Dockerfile -t command-parser:v1 .
```

**Docker build has not been run.** Image size has not been measured; the assignment target is at most 2 GB.

## 11. Kubernetes and Scaling (Task 4) — Manifests Only

The planned deployment configuration includes:

| Setting | Configuration |
|---|---|
| Namespace | `app` |
| Replicas | 2 |
| CPU request | 250m |
| Memory request | 512Mi |
| CPU limit | 1 CPU |
| Memory limit | 1Gi |
| Liveness probe | `/healthz` |
| Readiness probe | `/readyz` |
| Update strategy | RollingUpdate |
| Max unavailable | 0 |
| HPA range | 1–2 replicas |
| CPU scaling target | 70% |

Rollout and rollback commands:

```bash
kubectl -n app set env deploy/command-parser \
  MODEL_VERSION=v2 \
  MODEL_URI=s3://models/v2

kubectl -n app rollout undo deploy/command-parser
```

The manifests have been written and structurally checked as YAML. They have never been applied to a running cluster.

## 12. Networking and NACL (Task 5) — Done

The subnet allocation uses the private network `10.20.0.0/16`.

| Subnet | CIDR |
|---|---|
| App | `10.20.0.0/22` |
| Public | `10.20.4.0/24` |
| Data | `10.20.5.0/25` |
| Management | `10.20.5.128/27` |

Subnet calculations are documented in `network/subnets.md`.

Network ACL rules are defined in `network/nacl.json`.

Run the local evaluators:

```bash
make subnets
make nacl
```

The independent local NACL evaluator passed 11/11 packet checks. The instructor-provided `nacl_sim.py` was not run.

## 13. CI/CD and Testing (Task 6)

The GitHub Actions workflow is stored at:

`.github/workflows/ci.yml`

The written workflow includes:

- Python linting with pyflakes
- Unit tests
- Gitleaks secret scanning

The following features are not implemented or verified:

- Release-based model evaluation
- The 95% model quality gate
- A deliberately failing quality-gate run
- A completed GitHub Actions run

Run local checks:

```bash
make lint
make test
```

Local test results: 14 passed.

## 14. Performance, Cost and Reliability (Task 7) — No Measurements

The repository contains a Locust test file and a cost calculation script. Neither has been executed.

Planned load test:

```bash
make load
```

Planned cost calculation:

```bash
python scripts/cost.py \
  --rate-card data/rate_card.json \
  --replicas 2 \
  --cpu 1 \
  --mem-gib 1 \
  --rps <measured>
```

Cost per 1,000 requests is calculated as:

\[
\text{Cost per 1000 requests}
=
\frac{\text{Hourly cost}}{\text{Throughput}\times3600}
\times1000
\]

All performance and cost values are pending actual measurements.

## 15. Shutdown

Delete the local Kubernetes cluster and associated resources:

```bash
make down
```

## 16. Limitations and Future Work

Current limitations:

- Task 1 teacher labelling has not been executed.
- Task 2 student training and evaluation have not been executed.
- Task 3 Docker image has not been built.
- Task 4 Kubernetes manifests have not been applied.
- Task 5 was tested with an independent evaluator; the instructor's simulator was not run.
- Task 6 has no completed CI run or model quality gate.
- Task 7 has no actual load-test, resource or cost measurements.
- The assignment-provided `score.py`, `nacl_sim.py` and dataset are not included.

Future work:

1. Obtain the assignment student kit and run the teacher-labelling pipeline.
2. Train Pythia-70M and publish the model artifacts as GitHub Release assets.
3. Run model evaluation and collect actual validation metrics.
4. Build and measure the Docker image.
5. Apply and test the Kubernetes deployment.
6. Implement and verify the Release-based CI quality gate.
7. Run Locust tests and collect CPU, memory and cold-start measurements.
8. Complete the cost analysis and reliability review.

## 17. Additional Documentation

- [Study Guide](docs/STUDY_GUIDE.md)
- [Technical Report](report/report.pdf)
- [AI Use Disclosure](AI_USE.md)
- [GitHub Repository](https://github.com/iamankoo/Cloud-Assignment)
