# CS3081 Cloud Computing Mini Project

**Author:** Aniket Raj
**Roll No.:** 230103030
**GitHub:** iamankoo
**Email:** aniketraj00384@gmail.com

Command-Parser Distillation on a Local Cloud is a lightweight natural-language command parser that converts English instructions into structured JSON. It uses a teacher–student knowledge-distillation architecture and integrates object storage, FastAPI, Docker, Kubernetes and automated evaluation.

> **Project status.** The implementation covers all seven tasks and is unit-tested (32 tests). The expensive experiments (teacher labelling, training,
> Docker build, cluster deployment, CI runs, load test) have **not yet been executed**; no logs, scores, model archives or measurements were fabricated to fill that gap.
> Every number in the documents is tagged with its evidence class (below).

## Evidence classes

| Classification | Meaning |
|---|---|
| Actual | Produced by executing project code |
| Calculated | Reproducible mathematical calculation |
| Illustrative | Example used to explain a method |
| Reported | Value recorded in the project reflection |
| Planned | Implementation or experiment not yet executed |

## Status by task

| Task | Implementation | What was actually run here | Not run |
|---|---|---|---|
| 1 Storage + labelling | `worker/`, `k8s/worker-job.yaml`, `cluster/`, `prompts/` | shard completeness/disjointness on 3,000 ids; cleaning rules, count identity, CLI, SHA-256 on toy records | labelling with Ollama, SeaweedFS, Job |
| 2 Training | `training/`, `tools/predict.py` | config completeness; prompt consistency with the service | training, scoring (no data, no `transformers`) |
| 3 Service + Docker | `service/` | 32-test suite; real app with a **stub** model (`tools/demo_server.py`): endpoints, headers, `FAULT_INJECT` | Docker build, size, 50 requests at 1 CPU / 1 GiB |
| 4 Kubernetes | `k8s/app.yaml` (Deployment, Service, Ingress, HPA, PodDisruptionBudget) | manifest fields unit-tested | applying to a cluster, rollout, recovery, cold start |
| 5 Networking | `network/`, `scripts/subnet_calc.py`, `tools/nacl_eval.py` | subnet plan, own NACL evaluator 11/11 | the instructor's `nacl_sim.py` (not available) |
| 6 CI/CD | `.github/workflows/ci.yml`, `Makefile` | stage order and gate logic checked by tests | any GitHub Actions run; gitleaks; `make up` |
| 7 Performance | `tools/locustfile.py`, `scripts/cost.py`, `scripts/slo.py` | cost/SLO arithmetic; Locust **toolchain** smoke test against the stub | the real load test |

Local verification (Windows 11, Python 3.10.11): **32 tests passed, pyflakes clean** (`results/pytest_local.txt`); NACL evaluator 11/11 (`results/nacl_eval_local.txt`); subnet plan (`results/subnet_calc_local.txt`).
The stub-service demo (`results/demo_api_stub.txt`) and the 20 s Locust smoke test (`results/stub_smoke_*`, 209 requests, 0 failures) validate the toolchain only; **they are not performance results** for the real model.
The instructor's `student_kit` (`commands_pool.jsonl`, `validation.jsonl`, `score.py`, `nacl_sim.py`, `rate_card.json`) is not included.

See `report/report.pdf` for the full technical report (all seven tasks, diagrams, worked examples, evidence index) and `results/README.md` for the classification of every file in `results/`.

## Figures reported in my handwritten reflection (not verified)

These come from `reflection/230103030.pdf`. **No supporting logs exist here and none were created.**

| Item | Reported value | Status |
|---|---|---|
| Pod recovery after deleting a pod under load | 18.93 s | reported, unverified |
| Dropped connections during that recovery | Zero | reported, unverified |
| Traffic distribution across replicas | 53.4% / 46.6% | reported, unverified |
| Cold start | 18.0 s | reported, unverified |
| Deployment cost (2 replicas) | 7.90 INR/hour | reported; reproduced by calculation (2 x (3.50 + 0.45)) |
| Throughput | 2,052 requests/hour | reported, unverified |
| Cost per 1,000 requests | 3.95 INR | reported; **arithmetic discrepancy** |

**Discrepancy for review:** 7.90 INR/hour at 2,052 requests/hour gives 7.90 / 2,052 x 1,000 = **3.85 INR per 1,000 requests**, not 3.95. 3.95 would correspond to 2,000 requests/hour, and it equals the hourly cost of one replica (7.90 / 2). See `results/REPORTED_FIGURES.md` and `results/cost_arithmetic_check.txt` (arithmetic only).
The reflection's proposed improvements (pre-hydrated persistent volumes, safetensors `mmap`, Cilium eBPF network policies) and its conclusion that the system is "reliable, cost-efficient and scalable" are proposals/conclusions drawn from those unverified figures. Configuration it describes: `OLLAMA_HOST=0.0.0.0:11434`, `OLLAMA_NUM_PARALLEL=2`, `OLLAMA_FLASH_ATTENTION=true` (`docs/SETUP.md`); SeaweedFS with a 2 GiB PVC and 1.5 GiB limit (`cluster/seaweedfs.yaml`, my own manifest). A typed transcription is in `docs/REFLECTION_DRAFT.md`.

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
Scaling: Horizontal Pod Autoscaler (1-2 replicas, 70% CPU), PodDisruptionBudget (minAvailable 1)
Monitoring: Locust and kubectl top
```

## Technology Stack

- **Student model:** EleutherAI/Pythia-70M (Apache-2.0) · **Teacher:** Ollama Phi-3.5 Mini Instruct (temperature 0, seed 42)
- **ML framework:** PyTorch and Transformers · **API:** FastAPI and Uvicorn
- **Object storage:** SeaweedFS (S3-compatible) · **Containers:** Docker (non-root, CPU-only torch)
- **Orchestration:** Kubernetes using k3d · **Load testing:** Locust · **CI/CD:** GitHub Actions (pyflakes, pytest, evaluate, quality gate, Gitleaks)

## Repository Structure

| Path | Purpose |
|---|---|
| `worker/` | Teacher labelling worker (`teacher_raw` output), cleaning script, worker Dockerfile |
| `prompts/` | Teacher prompt |
| `training/` | Student training configuration (with library versions) and script |
| `service/` | FastAPI application, JSON schema, Dockerfile, pinned requirements |
| `cluster/` | k3d and SeaweedFS configuration |
| `k8s/` | Application Deployment, Service, Ingress, HPA, PodDisruptionBudget; labelling Job |
| `network/` | Subnet plan, NACL rules, sample packets |
| `tools/` | NACL evaluator, prediction script, Locust file, stub-model demo server |
| `scripts/` | Deployment, teardown, upload, model packaging, subnet, cost and SLO scripts |
| `data/` | Hypothetical example rate card (the instructor's kit data is not included) |
| `tests/` | Unit tests (32) |
| `docs/` | Setup, study guide, release metadata, submission checklist, reflection transcription |
| `results/` | Logs of what was actually run, plus clearly labelled worked examples |
| `report/`, `reflection/` | Technical report and handwritten reflection |

## Requirements

- Python 3.11 (3.10 was used for the local tests); `pip install fastapi uvicorn httpx pydantic jsonschema pyyaml pytest pyflakes boto3 requests locust`
- For the full system: Docker, k3d, kubectl, GNU Make, Ollama with `phi3.5` (none of these were available on the machine used so far, except Python)

## Setup

```bash
git clone https://github.com/iamankoo/Cloud-Assignment.git
cd Cloud-Assignment
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn httpx pydantic jsonschema pyyaml pytest pyflakes boto3 requests locust
cp .env.example .env     # development-only values; never commit .env
```

## Quick demonstration without Docker, Kubernetes or a model

```bash
make check               # pyflakes + 32 tests + NACL evaluator + subnet plan
make demo                # terminal 1: real FastAPI app with a STUB generator on :8000
curl -i -X POST localhost:8000/parse -H 'Content-Type: application/json' -d '{"text":"what is the weather in london"}'
FAULT_INJECT=1 make demo # forces invalid output: HTTP 500 {"error":"invalid_model_output"}
make cost RPS=0.57       # cost per 1,000 requests with the example (hypothetical) rate card
make slo REQUESTS=1000 FAILED=7
```

The stub is a keyword rule set, not Pythia-70M: its answers and latency say nothing about model quality or service performance.

## Model Training (planned, not run)

Settings in `training/config.yaml`: first 1,500 cleaned records, 3 epochs, batch size 8, learning rate 5e-5, AdamW weight decay 0.01, gradient clipping 1.0, max length 128, CPU, seed 42, pinned library versions.

```bash
make train SUBSET=50     # smoke test on 50 records
make train VERSION=v1
make train VERSION=v2    # second version for the rolling update (use --seed or more epochs to differ)
```

Outputs go to `training/output/<version>/` (excluded from Git); the loss per epoch is written to `training/loss.csv`.

## Evaluation (planned, not run)

```bash
python tools/predict_teacher.py --out results/pred_teacher.jsonl          # teacher, same prompt/options as Task 1 (needs Ollama)
python tools/predict.py --model training/output/v1 --input data/validation.jsonl --out results/pred_v1.jsonl
python tools/score.py results/pred_v1.jsonl data/validation.jsonl --out results/score_v1.json --min-validity 95
```

`tools/score.py` and `data/validation.jsonl` come from the instructor's kit and are not included. Scores required: teacher, untrained Pythia-70M, trained student.

## Deployment (not run)

```bash
make up          # cluster, SeaweedFS, images, application  (needs Docker, k3d, kubectl)
```

`scripts/deploy.sh` creates the k3d cluster, applies SeaweedFS and the Secrets from `.env`, builds and imports the images and applies `k8s/app.yaml`. Models must already be in the `models` bucket
(`python scripts/upload.py --bucket models --src training/output/v1 --key v1`). API endpoint: `http://localhost:8080/parse`.

## API Usage

```bash
curl -X POST http://localhost:8080/parse -H "Content-Type: application/json" -d '{"text":"set an alarm for seven thirty am tomorrow"}'
```

Expected response shape (the content depends on the model): `{"intent": "alarm_set", "date": "tomorrow", "time": "seven thirty am", "place": null}`

- `GET /healthz`: process health · `GET /readyz`: 503 until the model is loaded · `POST /parse`: invalid model output returns HTTP 500 `invalid_model_output`; `FAULT_INJECT=1` forces invalid output

## Kubernetes and Load Testing (not run)

`k8s/app.yaml`: namespace `app`, 2 replicas, requests 250m/512Mi, limits 1 CPU/1Gi, liveness `/healthz`, readiness `/readyz`, RollingUpdate (maxUnavailable 0, maxSurge 1), Service, Ingress (Traefik), HPA 1-2 replicas at 70% CPU (scale-down window 60 s), PodDisruptionBudget (minAvailable 1).
The cluster is one laptop: it demonstrates Kubernetes self-healing, not fault tolerance across machines.

```bash
make load                                   # 4 users, 2 minutes, http://localhost:8080
kubectl top pods -n app && kubectl get pods,svc,hpa -n app
make cost RPS=<measured> && make slo REQUESTS=<n> FAILED=<f>
```

Cost per 1,000 requests = hourly cost / (throughput x 3600) x 1000 (`scripts/cost.py`); each replica is billed at its CPU and memory limits (an assumption).

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

`.github/workflows/ci.yml` stages, in order: `lint` (pyflakes) -> `unit-tests` (pytest) -> `evaluate` (download a Release model, run `score.py`) -> `quality-gate` (`score.py --min-validity 95`); `secret-scan` (Gitleaks) runs in parallel.
`evaluate` and `quality-gate` are manual (`workflow_dispatch`) and need this project's own model Release and the kit's `score.py`, neither of which exists yet. No workflow has ever run.

```bash
make lint && make test     # 32 passed locally
```

## Model Artifacts

Model weights are maintained separately from the Git repository. Model archives and their corresponding checksums will be published in the project Release after training and evaluation.
The [latest Release](https://github.com/iamankoo/Cloud-Assignment/releases/latest) currently contains the source ZIP and its checksum. `make package VERSION=v1` builds a model archive with its checksum once a model has been trained.

## Provenance and AI Use

Academic provenance is documented in [`docs/PROVENANCE.md`](docs/PROVENANCE.md); AI-assisted development and its checking are documented in [`AI_USE.md`](AI_USE.md).

## Cleanup

```bash
make down      # deletes the k3d cluster (only after `make up`)
```

## Limitations and Future Improvements

- Not executed: labelling, training, Docker build, cluster deployment, CI runs, load test; the instructor's kit is missing.
- Next: obtain the kit; run the pipeline end to end; publish my own v1/v2 with checksums; add the failing and passing quality-gate runs; collect Locust, `kubectl top` and cold-start data; fill `results/`.
- Beyond the assignment: multi-node cluster, replicated storage, grammar-constrained decoding, per-service credentials, TLS.

## Project Repository

[https://github.com/iamankoo/Cloud-Assignment](https://github.com/iamankoo/Cloud-Assignment)
