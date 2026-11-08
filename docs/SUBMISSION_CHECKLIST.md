# Submission checklist (Aniket Raj, 230103030)

Status key: DONE = completed and checked; PARTIAL = written or tested only in part; OPEN = not done; YOU = needs the student's personal action.

## A. Completed and verified (see `results/` and `results/README.md`)
- DONE Repository organised; README, report (3 pages), study guide, setup guide, release metadata, AI-use declaration are consistent with each other.
- DONE 18 unit tests pass; pyflakes clean; own NACL evaluator 11/11; subnet plan matches an independent computation.
- DONE Task 5 deliverables (`network/subnets.md`, `nacl.json`, own evaluator and packets).
- DONE Handwritten reflection present as `reflection/230103030.pdf` (3 pages; name, roll number, repo link).
- DONE Figures from the reflection kept verbatim in `results/REPORTED_FIGURES.md`, labelled **reported, unverified**; cost arithmetic warning (7.9 / 2052 x 1000 = 3.85, not 3.95) in README, report, reflection draft and results.
- DONE Ollama settings and SeaweedFS 2 GiB PVC / 1.5 GiB limit documented/configured as described in the reflection.
- DONE Externally sourced archives removed from the Release (redistribution permission could not be established); provenance, author attribution and original checksums preserved in `RELEASE_METADATA.md`. The Release now has no model archives.
- DONE Security checks: no secrets, `.env`, weights or temp files in the repository or ZIP; Git history preserved.
- DONE Annotated `final` tag created on the student's explicit authorisation (2026-11-09) at the final submission commit (see `git show final`); `230103030.zip` built from that tagged state and verified from a clean extraction (tests re-run in the extracted copy).

## B. Outstanding assignment requirements (nothing below has been run; no evidence exists)
| Task | Still needed |
|---|---|
| 1 Labelling (12) | instructor's `student_kit`; run labelling (2 shards); shard files; cleaning counts and SHA-256; SeaweedFS bucket evidence |
| 2 Training (20) | run `make train SUBSET=50` and `make train`; loss CSV; own v1/v2 archives, checksums and Release; scores for teacher, untrained base and trained student with the kit's `score.py` |
| 3 Service (14) | build Docker image and record size (<= 2 GB); 50 sequential requests at 1 CPU / 1 GiB with peak memory |
| 4 Kubernetes (22) | apply manifests; HPA evidence; rolling update and rollback; pod-deletion recovery; three cold starts; load balancing |
| 5 Networking (10) | run the instructor's `nacl_sim.py` on its six packets (everything else is done) |
| 6 CI/CD (10) | first GitHub Actions run; run of the manual quality-gate job (passing and a deliberately failing run, with links); gitleaks result; `make up` and `make down` from a fresh clone |
| 7 Performance (12) | Locust standard run (p50, p95, throughput, error rate); CPU and memory samples; cold-start timings; cost per 1,000 requests; SLO and error budget; six-row review table with measured evidence |

## C. Personal actions (only you can do these)
1. YOU Decide how to handle the reflection: provide the real logs or files for its reported figures, or edit the reflection. Resolve the cost discrepancy (3.85 vs 3.95 per 1,000 requests; 3.95 corresponds to 2,000 requests/hour or to one replica's hourly cost).
2. YOU The reflection says "zero dropped connections", that network policies were updated, and that the system is "reliable, cost-efficient and scalable"; nothing in the repository supports these. Confirm or revise.
3. YOU If you want to use or redistribute the other author's model archives, obtain and keep written permission first (the source has no licence file) and confirm your instructor's policy. They are not your training output, and your own v1/v2 archives, checksums and evaluation outputs are still outstanding.
4. YOU Add the instructor's kit files if you want the quality-gate job and evaluation to run.
5. YOU Run the pipeline on a machine with Docker, k3d, kubectl and Ollama if you want real results for Tasks 1-4 and 7, then give the outputs to be added to `results/`.
6. YOU Upload the ZIP to the college portal (not done by the assistant). The ZIP filename and the PDF filename must be exact: `230103030.zip`, `230103030.pdf`.
7. YOU Only the commit tagged `final` is assessed. If anything is changed after the tag, the tag must be moved deliberately (never force-pushed by the assistant) and the ZIP rebuilt.
