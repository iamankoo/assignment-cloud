# Figures reported in the original handwritten reflection (NOT verified)

Source: the student's handwritten reflection (`reflection/230103030.pdf`, page 3 and page 2). No log, CSV, command output or
screenshot supporting these figures exists in this repository, and none has been fabricated. They are preserved here as the
student reported them and must not be read as measurements verified by this repository.

**As written in the reflection (verbatim, unchanged):** `18.93 s`; `53.4 %`, `46.6 %`; `18.0 s`; `7.9 INR/hr`; `2052 requests/hr`; `3.95 INR per 1000 requests`;
`OLLAMA_HOST = 0.0.0.0:11434`; `OLLAMA_FLASH_ATTENTION = true`; `OLLAMA_NUM_PARALLEL = 2`; 2 GiB persistentVolumeClaim; 1.5 GiB memory limit.
Other documents only reformat the same values (7.9 shown as 7.90, 2052 as 2,052); no value has been changed. The unit-cost arithmetic warning below applies wherever these figures appear.

| Item | Reported value | Supporting file in repo | Status |
|---|---|---|---|
| Pod recovery after deleting an active pod under load | 18.93 s, "zero dropped connections" | none | **reported, unverified** |
| Dropped connections during that recovery | Zero ("zero dropped connections") | none | **reported, unverified** |
| Traffic distribution across replicas | 53.4% / 46.6% | none | **reported, unverified** (the two shares sum to 100%) |
| Cold start | 18.0 s | none | **reported, unverified** |
| Deployment cost (2 replicas) | 7.90 INR/hour | none | **reported, unverified** |
| Throughput | 2,052 requests/hour | none | **reported, unverified** |
| Cost per 1,000 requests | 3.95 INR | none | **reported; arithmetic does not match, see below** |

## Configuration described in the reflection
| Item | Reported | In this repository |
|---|---|---|
| Ollama server host | `OLLAMA_HOST=0.0.0.0:11434` | documented in `docs/SETUP.md` |
| Ollama parallelism | `OLLAMA_NUM_PARALLEL=2` | documented in `docs/SETUP.md` |
| Flash Attention | enabled (`OLLAMA_FLASH_ATTENTION=true`) | documented in `docs/SETUP.md` |
| SeaweedFS storage | 2 GiB PersistentVolumeClaim mounted at `/data` | present in `cluster/seaweedfs.yaml` (my manifest) |
| SeaweedFS memory | 1.5 GiB limit | present in `cluster/seaweedfs.yaml` (my manifest, added to match the description) |
| File path named in the reflection | `k8s/data/seaweedfs.yaml` | this repo uses `cluster/seaweedfs.yaml`; the student's original file was not provided |

Whether the Ollama connection failure and the SeaweedFS out-of-memory event described in the reflection occurred is **unverified**: no error output or pod description was provided.

## Cost arithmetic check (`scripts/check_reported_cost.py`, output in `cost_arithmetic_check.txt`)
This is an arithmetic check of the reported numbers against each other, not a measurement.

- cost per 1,000 requests = hourly cost / requests per hour x 1,000 = 7.90 / 2,052 x 1,000 = **3.850 INR**
- Reported: **3.95 INR**. Difference 0.10 INR (+2.6%).
- 3.95 INR per 1,000 requests would correspond to **2,000 requests/hour** (7.90 / 2,000 x 1,000), not 2,052.
- 3.95 also equals 7.90 / 2, the hourly cost of **one** replica; the two quantities may have been confused.
- 2,052 requests/hour is about 0.57 requests/second.

**Flag for review:** one of the reported throughput (2,052/h), the reported unit cost (3.95) or the reported hourly cost (7.90) is inconsistent. Correct the reflection or provide the Locust statistics and rate card before relying on any of them.
7.90 INR/hour is consistent with 2 replicas x (1 vCPU x 3.50 + 1 GiB x 0.45) only if the instructor's rate card uses those prices; `rate_card.json` is not in this repository, so that is also unverified.

## What would verify them
Locust `*_stats.csv` and the `X-Served-By` counts (distribution, throughput), `kubectl get pods -w` output with timestamps around the pod deletion (recovery), the three cold-start timings, and the rate card.
