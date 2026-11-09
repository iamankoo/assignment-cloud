# Data preparation and model evaluation results (supplied)

**Student:** Aniket Raj · Roll No. 230103030 · GitHub `iamankoo`

**Status: supplied.** These values were supplied and confirmed by the student as this project's data-preparation and model-evaluation results. They are reproduced exactly.
The underlying logs, score files, training data and model archives are **not** stored in this repository, and the labelling, training and scoring runs were **not re-executed here**. No additional metrics were derived or invented.
Infrastructure experiments (Docker build, cluster deployment, CI runs, load test) are a separate matter and remain **planned** (see `SUBMISSION_CHECKLIST.md`).

## Technology stack (supplied)
| Layer | Technology |
|---|---|
| Teacher / data generation | Ollama Phi-3.5 |
| Student / ML | EleutherAI Pythia-70M, PyTorch, Transformers |
| API | FastAPI and Uvicorn |
| Storage | SeaweedFS S3-compatible object storage |
| Orchestration | Docker, Kubernetes, k3d, Helm |
| Testing / automation | unittest, Ruff, GitHub Actions, Gitleaks, Locust |

Note: the code in this repository is checked locally with pytest and pyflakes and is deployed with `kubectl` manifests; it does not use Helm, unittest or Ruff.

## Data preparation
- Teacher-generated command dataset: **3,000** examples.
- Cleaning checked JSON syntax, required keys, validation of slots, and duplicates.
- V1 cleaned training set: **2,292** examples (3,000 - 2,292 = 708 examples excluded, calculated).
- Recorded exclusions include invalid JSON output, invalid-slot examples and duplicates. The detailed per-category counts were only partially legible in the supplied material and are therefore **not stated**; none was invented.

## Model evaluation (validation set: 100 examples)
| Validation metric | Teacher Phi-3.5 | Student v1 | Student v2 |
|---|---:|---:|---:|
| JSON validity | 94% | 90% | 89% |
| Intent accuracy | 85% | 75% | 76% |
| Date accuracy | 71% | 68% | 69% |
| Time accuracy | 79% | 76% | 79% |
| Place accuracy | 81% | 77% | 71% |
| Full-frame accuracy | 44% | 41% | 42% |

With 100 validation examples, one example equals one percentage point (calculated). Student v1 (90% JSON validity) is below the 95% JSON-validity quality gate.

## Reported cost figure (project reflection)
The reflection reports ₹7.90/hour, 2,052 requests/hour and **₹3.95 per 1,000 requests**; the reported value is preserved as written.
**Transparent note:** ₹7.90 / 2,052 requests per hour × 1,000 ≈ **₹3.85** per 1,000 requests (calculated, `results/cost_arithmetic_check.txt`). Neither value was changed.
