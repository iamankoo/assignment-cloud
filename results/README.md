# results/ index

Everything here is classified so that measured evidence cannot be confused with reported or planned values.

## Genuine logs produced by running code in this repository (2026-11-08/09, Python 3.10, Windows)
| File | What it is |
|---|---|
| `pytest_local.txt` | Unit tests run in the repository layout |
| `nacl_eval_local.txt` | Own NACL evaluator on 11 hand-written packets |
| `subnet_calc_local.txt` | Subnet plan from `scripts/subnet_calc.py` |
| `cost_arithmetic_check.txt` | Arithmetic consistency check of the reported cost figures (not a measurement) |
| `zip_layout_tests.txt` (ZIP only) | Tests/lint re-run inside the submission ZIP layout |

## Reported, not verified
`REPORTED_FIGURES.md` lists the figures and configuration taken from the handwritten reflection (recovery time, traffic split, cold start, cost, throughput, Ollama and SeaweedFS settings) and the cost-arithmetic discrepancy. No supporting logs exist.

## Not present (nothing was fabricated to fill these)
Teacher shard files, cleaning counts, training config run/loss logs, `score.py` outputs, Locust CSVs, `kubectl` outputs, SeaweedFS manifest used in the original run, Docker build/size output, CI run links, and any SHA-256 of models trained by the student.
The GitHub Release has no model archives: the externally sourced archives were removed (redistribution permission could not be established) and only their original checksum manifests remain; see `../docs/RELEASE_METADATA.md`.
