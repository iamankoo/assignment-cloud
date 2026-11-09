# results/ index

Everything here is classified so that measured evidence cannot be confused with calculated, illustrative, reported or planned values. Nothing in this folder is a result of teacher labelling, training, a Docker build, a cluster run, CI, or a load test of the real service: those have not been executed.

## Actual: produced by running code in this repository (2026-11-09, Python 3.10.11, Windows 11)
| File | What it is |
|---|---|
| `pytest_local.txt` | 32 unit tests and pyflakes (warning-detail lines omitted) |
| `nacl_eval_local.txt` | Own NACL evaluator on 11 hand-written packets (11/11) |
| `subnet_calc_local.txt` | Subnet plan from `scripts/subnet_calc.py` |
| `demo_api_stub.txt` | `curl` session against the real FastAPI app with a **stub** generator (`tools/demo_server.py`): endpoints, headers, `FAULT_INJECT` |
| `stub_smoke_stats.csv`, `stub_smoke_stats_history.csv`, `stub_smoke_failures.csv`, `stub_smoke_exceptions.csv`, `stub_smoke_headers.json` | 20 s Locust run (4 users) against the stub: 209 requests, 0 failures. **Toolchain check only, not a performance result** |
| `zip_layout_tests.txt` (ZIP only) | Tests/lint re-run inside the submission ZIP layout by `scripts/build_submission.py` |

## Calculated / illustrative
| File | What it is |
|---|---|
| `cost_slo_worked_examples.txt` | `scripts/cost.py` and `scripts/slo.py` outputs for hypothetical throughput values and request counts; prices from `data/rate_card.example.json` (hypothetical exercise rates) |
| `cost_arithmetic_check.txt` | Arithmetic consistency check of the reflection's reported cost (3.85 computed vs 3.95 reported) |

## Reported (project reflection, not verified)
`REPORTED_FIGURES.md` lists the figures and configuration taken from the handwritten reflection (recovery time, traffic split, cold start, cost, throughput, Ollama and SeaweedFS settings) and the cost discrepancy. No supporting logs exist.

## Supplied (not executed here)
The supplied data-preparation and evaluation results are in `../docs/EVALUATION_RESULTS.md`; no log or data file for them is stored in this folder.

## Planned (not executed; nothing was fabricated to fill these)
Teacher shard files, cleaning counts, `training/loss.csv`, `score.py` outputs, Locust CSVs of the real service, `kubectl` outputs, Docker build/size output, CI run links, gitleaks output, and any SHA-256 of a model trained by this project.
Model archives and checksums will be published in the project Release after training; see `../docs/RELEASE_METADATA.md`.
