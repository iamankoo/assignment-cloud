# CS3081 Cloud Computing Mini Project (partial, independent implementation)

**Aniket Raj** · Roll no. 230103030 · GitHub `iamankoo` · aniketraj00384@gmail.com

This repository was started from scratch on 2026-11-08 with no copied history. It is **incomplete**: the deadline allowed about 30 minutes.
Nothing here claims results that were not produced. No `final` tag exists.

## Status

| Task | State | Evidence |
|---|---|---|
| 1 Storage + teacher labelling | **Not done** (no kit data, no Ollama, no cluster) | none |
| 2 Student training | **Not done** | none |
| 3 FastAPI service | **Implemented, unit-tested with a stub model.** Dockerfile written, **not built**; image size and 50-request test **not measured**; no real model | `service/`, `results/pytest_local.txt` |
| 4 Kubernetes | **Manifest written** (`k8s/app.yaml`), fields checked by a unit test; **never applied** | test only |
| 5 Networking | **Done and tested locally** with my own evaluator; instructor's `nacl_sim.py` **not run** (not available) | `network/`, `results/nacl_eval_local.txt`, `results/subnet_calc_local.txt` |
| 6 CI/CD | Workflow, Makefile, 9 tests, `AI_USE.md` written; **no CI run yet**; quality gate and Release evaluation **not implemented**; `make up` **not implemented** | `.github/workflows/ci.yml` |
| 7 Performance/cost | **Not done** | none |

## Run what exists
```bash
pip install fastapi httpx pydantic jsonschema pyyaml pytest pyflakes boto3
make test      # 9 tests
make lint
make nacl
make subnets
```
Local result 2026-11-08: 9 passed; pyflakes clean; own NACL evaluator 11/11 as expected; subnet plan matches `network/subnets.md`.

## Not verified
Docker build/size, any cluster behaviour, a real model, `/parse` against a real model, Locust, gitleaks, CI, cost, SLO.
The student_kit (commands, validation set, `score.py`, `nacl_sim.py`) was not available to me when this was written.
