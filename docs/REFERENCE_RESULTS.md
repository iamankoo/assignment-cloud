# Reference results (supplied reference material)

**Student:** Aniket Raj · Roll No. 230103030 · GitHub `iamankoo`

**Status of every value on this page: reference. These figures were supplied as reference material. They were NOT produced by running this repository, and no log, CSV, score file or checksum for them exists here.**
They are reproduced exactly as supplied, without correction, so that the expected shape of a complete run can be compared with this project's own results once those exist. The source of the reference material is recorded in `PROVENANCE.md`.

## 1. Data preparation (3,000 teacher-generated examples)
| Item | Reference value |
|---|---|
| Input examples | 3,000 |
| Invalid JSON | 1 |
| Wrong keys | 57 |
| Invalid slots | 610 |
| Duplicates | 40 |
| Retained (v1 training set) | 2,292 |

The supplied note says the exclusion categories may overlap; the retained count is the definitive output count.

## 2. Validation (100 examples)
| Metric | Teacher Phi-3.5 | Student v1 | Student v2 |
|---|---:|---:|---:|
| JSON validity | 94% | 90% | 89% |
| Intent accuracy | 85% | 75% | 76% |
| Date accuracy | 71% | 68% | 69% |
| Time accuracy | 79% | 76% | 79% |
| Place accuracy | 81% | 77% | 71% |
| Full-frame accuracy | 44% | 41% | 42% |

The supplied untrained-baseline file contains zero scores. Student v1 is the production candidate; at 90% JSON validity it does not meet the 95% quality gate.

## 3. Container and deployment
| Item | Reference value |
|---|---|
| Base image | Python 3.12 slim, CPU-only PyTorch |
| Image size (ARM64) | approximately 1.66 GB (limit 2 GB) |
| Peak cgroup memory under limits | approximately 737.4 MiB, no OOM kill |
| Replicas / HPA | 2 replicas; HPA min 1, max 2, 70% CPU |
| Rolling update | maxSurge 1, maxUnavailable 0; rollback v2 to v1 recorded |
| Readiness | 503 while loading, 200 when ready |
| Cold start (three runs) | 11 s, 11 s, 11 s |
| NACL simulator | 6 of 6 sample packets (100%) |
| CI | lint, five unit tests, evaluation, secret scan completed; a manual untrained-model run failed the quality gate as expected; no leaks reported |

## 4. Load test (4 users, 4 users/s, 2 minutes, `/parse`)
| Item | Reference value |
|---|---|
| Requests / successes / failures | 89 / 78 / 11 |
| Failure breakdown | 9 HTTP 500; 2 HTTP 0 (no response) |
| Error rate | 12.36% |
| Median / average / p95 | 3,700 ms / 5,297 ms / 16,000 ms |
| Minimum / maximum | 1,100 ms / 30,013 ms |
| Throughput | 0.748 requests/s |
| Served by each replica | 41 and 37 successes, all model version v1 |
| Peak sampled CPU per pod | about 993m and 989m (limit 1 CPU) |
| Peak sampled memory per pod | about 556 MiB and 555 MiB (limit 1 GiB) |

Both assignment targets (error rate at most 1%, p95 at most 5,000 ms) are missed in the reference run.

## 5. Cost and SLO (reference)
| Item | Reference value |
|---|---|
| Rates | 3.50 per vCPU-hour, 0.45 per GiB-hour (hypothetical) |
| Two replicas, 1 vCPU and 1 GiB each | 7.90 per hour |
| Cost at 0.748439 requests/s | approximately 2.93 per 1,000 attempted requests |
| SLO 99%, one run | error budget 0.89 failures; 11 failures consume approximately 1,236% |

## 6. Project reflection (reported) cost figure
The project reflection reports a deployment cost of ₹7.90/hour, 2,052 requests/hour and **₹3.95 per 1,000 requests**. The reported ₹3.95 is preserved as written.
**Transparent note:** ₹7.90 / 2,052 requests per hour × 1,000 ≈ **₹3.85** per 1,000 requests (calculated, `results/cost_arithmetic_check.txt`); ₹3.95 would correspond to 2,000 requests/hour. Neither value was changed.
