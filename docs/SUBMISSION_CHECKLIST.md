# Submission checklist (Aniket Raj, 230103030)

Status key: **DONE** completed and checked; **PARTIAL** written or tested only in part; **OPEN** not done; **YOU** needs the student's personal action.
It separates what is done from what still needs execution; it is not a claim that every assignment requirement is complete.

## A. Completed and verified (evidence in `results/`, see `results/README.md`)
- DONE Repository organised; README, report (`report/report.pdf`, 7 pages, no empty fields), study guide, setup guide, release metadata and AI-use declaration are consistent with each other and tag every number with an evidence class.
- DONE 32 unit tests pass; pyflakes clean (`results/pytest_local.txt`); own NACL evaluator 11/11; subnet plan matches an independent computation.
- DONE Task 5 deliverables (`network/subnets.md`, `nacl.json`, own evaluator and packets).
- DONE Technical review and fixes (incl. `scripts/package_model.py`, `tools/predict_teacher.py`, SeaweedFS probes): worker writes `teacher_raw` (as required) and cleaning dedupes by command text; `clean.py --s3`; loss written to `training/loss.csv`; library versions recorded; service logs model-load failures; non-root Dockerfiles with `.dockerignore`; PodDisruptionBudget, HPA scale-down window, ingress class; CI split into lint -> unit-tests -> evaluate -> quality-gate (+ secret-scan); `scripts/slo.py`, example rate card, `tools/demo_server.py`.
- DONE Stub-model API demonstration (`results/demo_api_stub.txt`) and Locust toolchain smoke test (`results/stub_smoke_*`), clearly labelled as not performance results.
- DONE Worked cost and SLO examples with hypothetical inputs (`results/cost_slo_worked_examples.txt`).
- DONE Handwritten reflection present as `reflection/230103030.pdf` (3 pages; name, roll number, repo link). Reflection figures kept as **reported, unverified** (`results/REPORTED_FIGURES.md`); cost arithmetic mismatch (3.85 vs 3.95) flagged.
- DONE Release: one Release only (latest) with the source ZIP and checksum; no model archives (`docs/RELEASE_METADATA.md`).
- DONE Security checks: no secrets, `.env`, weights or temp files in the repository or ZIP (build-script pattern scan; gitleaks itself not run).

- DONE Supplied data-preparation and evaluation results recorded exactly and labelled (`docs/EVALUATION_RESULTS.md`); reflection cost figure 3.95 kept with the 3.85 calculation note.
- OPEN Raw logs, score files and model archives behind the supplied results are not in the repository.

## B. Outstanding assignment requirements (nothing below has been run; no evidence exists)
| Task | Still needed |
|---|---|
| 1 Labelling (12) | instructor's `student_kit`; run labelling (2 shards); shard files; cleaning counts and SHA-256; SeaweedFS bucket evidence |
| 2 Training (20) | run `make train SUBSET=50` and `make train`; own v1/v2 archives, checksums and Release; scores for teacher, untrained base and trained student with the kit's `score.py` |
| 3 Service (14) | build Docker image and record size (<= 2 GB); 50 sequential requests at 1 CPU / 1 GiB with peak memory |
| 4 Kubernetes (22) | apply manifests; HPA evidence; rolling update and rollback; pod-deletion recovery; three cold starts; load balancing |
| 5 Networking (10) | run the instructor's `nacl_sim.py` on its six packets (everything else is done) |
| 6 CI/CD (10) | first GitHub Actions run; passing and deliberately failing quality-gate runs (links); gitleaks result; `make up` / `make down` from a fresh clone |
| 7 Performance (12) | Locust standard run; `kubectl top` samples; cold-start timings; cost from measured throughput; SLO and error budget from measured counts; review table with measured evidence |

## C. Personal actions (only you can do these)
1. YOU Decide how to handle the reflection: provide the real logs for its reported figures, or edit it. Resolve the cost discrepancy (3.85 vs 3.95 per 1,000 requests).
2. YOU The reflection says "zero dropped connections", that network policies were updated and that the system is "reliable, cost-efficient and scalable"; nothing in the repository supports these. Confirm or revise.
3. YOU Publish your own v1/v2 archives and checksums in the Release after training and evaluation (`make package`).
4. YOU Add the instructor's kit files so the evaluation and gate jobs can run.
5. YOU Run the pipeline on a machine with Docker, k3d, kubectl and Ollama for real results for Tasks 1–4 and 7, then add the outputs to `results/`.
6. YOU Upload the ZIP to the college portal. Exact names: `230103030.zip`, `230103030.pdf`.
7. YOU The earlier annotated tag `final` was **not** moved by this cleanup. Only the commit tagged `final` is assessed in the real submission: when you are ready, move it deliberately (never force-pushed by the assistant) and rebuild the ZIP with `python scripts/build_submission.py --out-dir <dir> --require-tag final`.
8. YOU Confirm your instructor's policy on reusing public reference material before the graded submission (see `docs/PROVENANCE.md`).
