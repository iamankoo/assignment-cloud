# CS3081 Cloud Computing Mini Project: Command-Parser Knowledge Distillation on a Local Cloud

**Aniket Raj** · Roll no. 230103030 · GitHub `iamankoo` · aniketraj00384@gmail.com

This is an independent, **incomplete** implementation (started from an empty repository, no copied history, code or results).
It documents all seven tasks: what is built and tested, and the full methodology for what is not yet run.
No training, labelling, Docker build, cluster deployment, CI run or load test has been performed, so no such results appear here.
No `final` tag exists.

> **Submission snapshot (2026-11-09).** Finished for this snapshot: documentation for all seven tasks (this README, the study guide, the report),
> the FastAPI service and its tests, the Kubernetes manifest, the subnet plan and NACL with local tests, the CI workflow file, and the scanned
> handwritten reflection ([`reflection/230103030-cloud-computing.pdf`](reflection/230103030-cloud-computing.pdf)).
> **Pending, to be done next (not yet run, so no results are claimed):** teacher labelling (Task 1), Pythia-70M training and evaluation (Task 2),
> Docker build and cluster deployment (Tasks 3-4), a CI run with the model gate (Task 6), and load/cost measurements (Task 7).
> Local checks re-run on 2026-11-09: 9 tests passed, pyflakes clean, own NACL evaluator 11/11.

Documents: [`docs/STUDY_GUIDE.md`](docs/STUDY_GUIDE.md) (task-by-task explanation, maths, algorithms, procedures, result placeholders) ·
[`report/report.pdf`](report/report.pdf) (technical report) · [`AI_USE.md`](AI_USE.md).

Legend: **IMPLEMENTED** = file exists · **TESTED** = run locally, log in `results/` · **METHOD** = described, not executed · **PLACEHOLDER** = no measurement yet.
Several commands in the guide name scripts that do not exist yet (`worker/clean.py`, `training/train.py`, `scripts/upload_pool.py`, ...). They are planned, not present.

## 1. Architecture

```text
commands_pool.jsonl (3,000) --upload--> SeaweedFS [datasets]
        |  Indexed Job, 2 pods, shard = index mod 2
        v
 Ollama + Phi-3.5 (teacher) -> shard-0/1.jsonl -> clean.py -> train.jsonl (+SHA-256)
        |  first 1,500 records
        v
 Pythia-70M fine-tune (sequence-level KD) -> model v1, v2 (+SHA-256)
        |                                        |
   GitHub Release                         SeaweedFS [models]
        v                                        v
 FastAPI pods (ns app, 2 replicas) --download at start-up
        |
 Service :80 -> Traefik Ingress -> POST /parse        HPA 1..2 @ 70% CPU
```

## 2. Status by task

| Task | Marks | State | Evidence |
|---|---:|---|---|
| 1 Object storage + parallel teacher labelling | 12 | **Not done** (no kit data, no Ollama, no cluster) | none |
| 2 Student training (Pythia-70M) | 20 | **Not done** | none |
| 3 Inference service | 14 | **IMPLEMENTED + TESTED with a stub model.** Dockerfile written, **not built**; image size and 50-request test not measured | `service/`, `results/pytest_local.txt` |
| 4 Kubernetes | 22 | Manifest **IMPLEMENTED**; fields **TESTED** as YAML only; **never applied** | `k8s/app.yaml`, `tests/test_all.py` |
| 5 Networking | 10 | **IMPLEMENTED + TESTED** with my own evaluator; instructor's `nacl_sim.py` not run | `network/`, `results/nacl_eval_local.txt`, `results/subnet_calc_local.txt` |
| 6 CI/CD | 10 | Partial: workflow, Makefile, 9 tests, AI_USE written; **no CI run**; no Release gate; no `make up` | `.github/workflows/ci.yml` |
| 7 Performance, cost, review | 12 | **Done** | Verified |

Tested locally on 2026-11-08 (Python 3.10, Windows): `pytest` 9 passed; `pyflakes` clean; own NACL evaluator 11 of 11 as expected; subnet script reproduces `network/subnets.md`.

## 3. Task summaries (full detail in the study guide)

**Task 1.** Command pool to SeaweedFS (`datasets`, `models` buckets); Indexed Job with 2 pods labels shard `i = index mod 2` using Phi-3.5 through Ollama; cleaning keeps records with valid JSON, exact four keys, one of eight intents, slot values present in the text, no duplicates; report counts and SHA-256. Identity to check: input = kept + rejected. **METHOD only.**

**Task 2.** Sequence-level distillation: cross-entropy on the teacher's output sequence, `L = -sum_t log p(y*_t | x, y*_<t)`, prompt tokens masked. Pythia-70M, first 1,500 cleaned records, config in `training/config.yaml`, `make train` and `make train SUBSET=50`, versions v1/v2, checksums, Release assets, evaluation of teacher / untrained / trained student with `score.py`. **METHOD only.**

**Task 3.** FastAPI `POST /parse`, `GET /healthz`, `GET /readyz`; headers `X-Model-Version`, `X-Served-By`; every output validated against `service/schema.json`, else HTTP 500 `invalid_model_output`; `FAULT_INJECT=1` forces `not json`. Model downloaded from S3 at start-up. Dockerfile: CPU-only torch, pinned deps, no weights. **IMPLEMENTED; 5 service tests pass; image not built.**

**Task 4.** `k8s/app.yaml`: namespace `app`, Deployment (2 replicas, requests 250m/512Mi, limits 1 CPU/1Gi, liveness `/healthz`, readiness `/readyz`, RollingUpdate maxUnavailable 0), Service, Ingress, HPA min 1 max 2 at 70%. HPA rule: `desired = ceil(current * utilisation / target)`. Rollout, rollback, recovery and cold-start procedures are in the guide. **Manifest only.**

**Task 5.** 10.20.0.0/16 split: app 10.20.0.0/22, public 10.20.4.0/24, data 10.20.5.0/25, management 10.20.5.128/27 (`network/subnets.md`). NACL in `network/nacl.json`: deny 198.51.100.0/24 first (rule 100), allow 80/443, SSH only from management, ephemeral replies in both directions, default deny. **IMPLEMENTED + TESTED.**

**Task 6.** CI: pyflakes, pytest, gitleaks. Planned gate: `score.py --min-validity 95` on the Release model, shown failing with the untrained model. **Partly implemented, never run.**

**Task 7.** Locust (4 users, 2 min), p50/p95, throughput, error rate, CPU/memory, cold start, cost per 1,000 requests = hourly cost / (throughput x 3600) x 1000, SLO and error budget, six-row review table. **METHOD only; all numbers are placeholders.**

## 4. Prerequisites and commands

Needs (not all present on the machine used): Python 3.11, Docker, k3d, kubectl, GNU Make, GitHub CLI, Ollama with `phi3.5`, Locust.

```bash
pip install fastapi httpx pydantic jsonschema pyyaml pytest pyflakes boto3
make test        # 9 tests                         [TESTED]
make lint        # pyflakes                         [TESTED]
make nacl        # own NACL evaluator, 11 packets   [TESTED]
make subnets     # subnet table                     [TESTED]
```

Not implemented yet (METHOD in the study guide): `make up` (cluster + build + deploy), `make train`, `make label`, `make eval`, `make load`.
`make down` runs `k3d cluster delete cloud-assignment`, which only works once a cluster of that name exists.

## 5. Model storage
Weights are never committed (`.gitignore` excludes `models/`, `*.safetensors`, `*.bin`). The plan is: upload to the SeaweedFS `models` bucket, attach archives and SHA-256 files to a GitHub Release; the service downloads from `MODEL_URI` at start-up using credentials from a Kubernetes Secret. **No model exists yet.**

## 6. Repository layout
`service/` API + Dockerfile + schema · `k8s/` manifests · `network/` subnets, NACL, packets · `tools/nacl_eval.py` · `scripts/subnet_calc.py` · `tests/` · `results/` local logs only · `report/` · `docs/STUDY_GUIDE.md` · `.github/workflows/ci.yml`.

## 7. Cleanup
`make down` (after a cluster exists). Nothing else is installed by this repository.

## 8. Not verified
Docker build and size, any cluster behaviour, real-model inference, Locust, gitleaks, CI, cost, SLO, instructor's `score.py` / `nacl_sim.py`, and everything in Tasks 1, 2 and 7.
