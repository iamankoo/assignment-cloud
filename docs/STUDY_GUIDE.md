# Study guide: CS3081 Mini Project, task by task

Author: Aniket Raj (230103030). Written for understanding and for preparing the handwritten reflection.

**Accuracy rule used throughout.** Text marked **[IMPLEMENTED]** exists in this repository. **[TESTED]** means it was run and the
log is in `results/`. **[METHOD]** means the procedure is described but was *not* executed. **[NOT RUN]** means no measurement exists yet; the section then
gives the evaluation procedure and, where useful, a labelled example. Evidence classes used in the tables: **actual** (produced by executing project code, log in `results/`), **calculated** (reproducible mathematical calculation), **illustrative** (example used to explain a method), **reported** (recorded in the project reflection), **planned** (not yet executed). Expected outcomes are theory, never results. Nothing in the "Results" sections is a measurement of this project unless it cites a file in `results/`.

---

## 0. The big picture

A teacher model (Phi-3.5 Mini, 3.8B parameters) is too big for a laptop service. We use it once, offline, to label 3,000 commands.
A 70M-parameter student (Pythia-70M) is fine-tuned to copy those labels. Only the student is deployed.

```
 commands_pool.jsonl (3000 text commands)
        |  upload
        v
 [SeaweedFS: bucket datasets]
        |  read by 2 parallel Jobs (shard 0, shard 1)
        v
 Teacher Phi-3.5 via Ollama  --> shard-0.jsonl, shard-1.jsonl   (raw replies)
        |  clean.py: parse JSON, check schema, drop duplicates
        v
 train.jsonl (+ SHA-256)  --first 1500 records-->  train.py (Pythia-70M)
        |                                              |
        |                                      model v1 / v2 (+ SHA-256)
        |                                              |
        |                       GitHub Release  +  [SeaweedFS: bucket models]
        v                                              v
                   FastAPI pods (namespace app) download model at start-up
                                   |
                  Service --> Ingress (Traefik) --> POST /parse
                                   |
                       HPA (1..2 pods at 70% CPU), Locust load test, cost/SLO
```

Status of this repository: all seven tasks are implemented in code and unit-tested where possible (32 tests); Task 5 is verified end to end; labelling, training, Docker, cluster, CI and the real load test have **not been run**, so there are no measured results for them.

---

## Task 1: Object storage and parallel teacher labelling (12 marks)

**Objective.** Put the command pool in object storage, label all 3,000 commands with the teacher using several workers in parallel, clean the output, and record exact counts and a checksum.

**Architecture.** k3d cluster (k3s inside Docker). Namespace `data` runs SeaweedFS with its S3 gateway (port 8333) and a PersistentVolumeClaim. Buckets: `datasets`, `models`. Namespace `pipeline` runs a Kubernetes **Indexed Job** with `completions = parallelism = 2`; each pod gets `JOB_COMPLETION_INDEX` (0 or 1). Ollama runs on the host and is reached from pods through the host gateway address.

**Sharding algorithm.** Number the commands `0..N-1` in file order. Worker `i` of `K` handles every record with `index mod K = i`.
Properties to prove in the report: *complete* (every index has exactly one residue), *non-overlapping* (residues are disjoint), *balanced* (shard sizes differ by at most 1; for N=3000, K=2 each gets 1500).

```python
def shard(records, i, k):
    return [r for n, r in enumerate(records) if n % k == i]
```

**Teacher prompt design.** The prompt (kept in `prompts/teacher_prompt.txt`; written but never used with the teacher) must contain: the four keys, the eight intents with meanings, the three slot rules (copy exactly; shortest phrase; null if absent), two or three examples, and the instruction "reply with one JSON object and nothing else". Use temperature 0 so the run is repeatable.

**Cleaning algorithm.** For every teacher reply: (a) `json.loads` must succeed; (b) keys must be exactly `intent,date,time,place`; (c) `intent` must be one of eight; (d) each non-null slot string must appear in the command text (the "never invent a value" rule); (e) drop duplicate *commands* (same text after case/space normalisation; the smallest id is kept). Count how many records each rule rejects. Identity: `input = kept + sum(rejected)` must hold. Write `train.jsonl` and its SHA-256 (`sha256sum train.jsonl`).

**Configuration.** `cluster/k3d.yaml` (1 server + 1 agent, port mapping 8080->80 for the Ingress); SeaweedFS Deployment/Service/PVC; env `SHARD_COUNT`, `OLLAMA_HOST`, `S3_ENDPOINT`, credentials from a Secret.

**Commands [METHOD].**
```bash
k3d cluster create --config cluster/k3d.yaml
kubectl apply -f cluster/seaweedfs.yaml
python scripts/upload.py --bucket datasets --src data/commands_pool.jsonl --key commands_pool.jsonl
kubectl apply -f k8s/worker-job.yaml                        # 2 parallel shards
kubectl -n pipeline logs -f job/teacher-label
python worker/clean.py --shards datasets/teacher/shard-0.jsonl datasets/teacher/shard-1.jsonl --counts-out results/clean_counts.json   # add --s3 to read/write the bucket
sha256sum datasets/v1/train.jsonl
```

**Testing methodology.** Verify shard files together contain exactly 3000 distinct IDs, no ID twice, and each ID sits in the shard its index predicts. Unit-test `clean.py` with hand-made bad replies (invalid JSON, extra key, bad intent, invented slot, duplicate).

**Results [NOT RUN for the real data].** The shard property and the counting identity are tested on synthetic and toy data (`tests/test_pipeline.py`, 32 tests pass: `results/pytest_local.txt`).
A real run needs the instructor's `commands_pool.jsonl` and Ollama. For orientation, the table shows what a filled table looks like.

| Quantity | This project (real data) | Toy unit test (illustrative; actual run of the test) |
|---|---|---|
| Input records | planned | 6 |
| Rejected: invalid JSON (a) | planned | 1 |
| Rejected: wrong keys (b) | planned | 1 |
| Rejected: bad intent (c) | planned | 1 |
| Rejected: invented slot (d) | planned | 1 |
| Duplicates (e) | planned | 1 |
| Kept | planned | 1 |
| Identity input = sum of the rest | by construction, asserted in tests | 6 = 1+1+1+1+1+1 |
| Records per shard | 1,500 / 1,500 expected (calculated: n mod 2) | n/a |
| SHA-256 of `train.jsonl` | produced by `clean.py` (planned run) | tested: digest equals the SHA-256 of the output file |

**Interpretation to write once measured.** Which rule rejects most? A high "invented slot" count means the teacher paraphrases; a better prompt or examples would reduce it. Wall-clock should be close to half the single-worker time only if Ollama is not the shared bottleneck on one CPU.

**Limitations.** Both workers share one host CPU for Ollama, so speed-up from parallelism may be small; the teacher itself is imperfect, so the student's ceiling is the teacher's quality.

---

## Task 2: Student training by sequence-level knowledge distillation (20 marks)

**Objective.** Fine-tune Pythia-70M on the first 1,500 cleaned records and compare teacher, untrained student and trained student on `validation.jsonl`.

**Theory.** Classic (word-level) KD minimises `KL(p_teacher || p_student)` over output distributions. **Sequence-level KD** (Kim and Rush, 2016) replaces the teacher's distribution by its single best output sequence `y*`; the student is trained with ordinary cross-entropy on `y*`:

L(theta) = - sum_{t=1}^{T} log p_theta( y*_t | x, y*_{<t} )

Why this suits the task: we can only call the teacher through text (Ollama replies), and the output space is a tiny JSON format, so imitating `y*` is enough. Limitation: the student inherits teacher mistakes and learns no uncertainty.

**Data format.** Each example becomes one string: `Command: <text>\nJSON: <teacher JSON><eos>`. Loss is computed on the JSON part (mask the prompt tokens with label -100) so the model is rewarded only for the answer. The service must use the *identical* prompt at inference (`PROMPT` in `service/app.py`); a mismatch is a classic bug.

**Training loop (CPU).** AdamW, learning rate about 5e-5, batch 8, 3-4 epochs, max length 128, fixed seed, gradient clipping 1.0. With 1,500 examples and batch 8 there are 188 steps per epoch. A reproducible `training/config.yaml` holds every number; `make train` reads only that file; `make train SUBSET=50` is a quick smoke test.

```python
for epoch in range(cfg.epochs):
    for batch in loader:
        loss = model(**batch).loss      # labels masked on the prompt
        loss.backward(); clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad()
        log_csv(epoch, loss.item())
```

**Versions.** v1 and v2 differ in a recorded way (for example seed or epochs). Task 4's rolling update later switches v1 to v2. Each is saved as `config.json`, `model.safetensors`, tokenizer files and `model.sha256`, uploaded to bucket `models` and attached to a GitHub Release. Weights are never committed to Git.

**Evaluation.** Three models, same prompt style, greedy decoding: teacher, untrained Pythia-70M, trained student. `score.py` (instructor-supplied) reports percentages: JSON validity, intent accuracy, date, time and place accuracy, and full-frame (all four right).

**Commands [METHOD].**
```bash
make train SUBSET=50 && make train
python tools/predict.py --model training/output/v1 --input data/validation.jsonl --out results/pred_v1.jsonl
python tools/score.py results/pred_v1.jsonl data/validation.jsonl --out results/score_v1.json --min-validity 95
sha256sum training/output/v1/model.safetensors
```

**Results [NOT RUN].** No model was trained or scored here (no labelled data; `transformers` not installed on the machine used). `train.py` writes `training/loss.csv` (one value per epoch) and `run_info.json`;
`config.yaml` records seed, learning rate, batch size, epochs, max length and the library versions (tested: `test_training_config_records_required_items`).
| Model | JSON validity | Intent | Date | Time | Place | Full frame |
|---|---|---|---|---|---|---|
| Teacher Phi-3.5 | planned | planned | planned | planned | planned | planned |
| Untrained Pythia-70M | planned | planned | planned | planned | planned | planned |
| Student v1 | planned | planned | planned | planned | planned | planned |
| Student v2 | planned | planned | planned | planned | planned | planned |

The assignment's own scoring example (V001-V004) gives validity 75, intent 50, date 50, time 75, place 75, full-frame 25 (calculated by hand from the specification).

**Expected (theory, not measured).** The untrained model should score near 0% validity because it was never taught the JSON format. The trained student should be much higher on validity and below or near the teacher on slot accuracy. Report the real numbers and the real gap.

**Limitations.** 1,500 examples and 70M parameters limit accuracy; validation has only 100 items so each point is 1%; the student cannot beat its teacher.

---

## Task 3: Inference service (14 marks)

**Objective.** A container that serves the student over HTTP with strict output validation.

**Architecture.** One FastAPI process (uvicorn, one worker) per pod. At start-up a background thread downloads `MODEL_URI` from SeaweedFS with boto3, loads tokenizer and model, then flips `ready = True`. Credentials come from a Kubernetes Secret as env vars.

| Endpoint | Behaviour |
|---|---|
| `GET /healthz` | 200 while the process lives (liveness) |
| `GET /readyz` | 503 until the model is loaded, then 200 (readiness) |
| `POST /parse` | body `{"text": ...}`; success returns only the four-key JSON with headers `X-Model-Version` and `X-Served-By` |

**Validation algorithm.** `raw -> json.loads -> jsonschema.validate(schema.json)`. Any failure returns HTTP 500 `{"error":"invalid_model_output"}`; broken JSON is never returned with 200. `FAULT_INJECT=1` replaces the raw text with `not json` before this check, to prove the guard works.

```python
raw = "not json" if os.environ.get("FAULT_INJECT") == "1" else generate(text)
try: obj = json.loads(raw); validate(obj, SCHEMA)
except (ValueError, ValidationError): return JSONResponse({"error": "invalid_model_output"}, 500)
```

**Docker.** `python:3.11-slim`, CPU-only torch from the PyTorch CPU wheel index (the default wheel bundles CUDA and would break the 2 GB limit), every dependency pinned, no weights in the image. Image must be <= 2 GB.

**Commands [METHOD].**
```bash
docker build -f service/Dockerfile -t command-parser:v1 .
docker image inspect command-parser:v1 --format '{{.Size}}'
docker run --cpus=1 --memory=1g -p 8000:8000 -e MODEL_URI=... -e S3_ENDPOINT=... command-parser:v1
# 50 sequential requests; sample memory with: docker stats --no-stream
curl -s -X POST localhost:8000/parse -H 'content-type: application/json' -d '{"text":"what is the weather in london"}'
```

**Testing.** [TESTED] 5 unit tests with an injected stub generator: success and headers, invalid intent, extra key, fault injection, health/readiness (`tests/test_all.py`; the whole suite, 32 tests, passes: `results/pytest_local.txt`). `tools/demo_server.py` additionally runs the *real* app with a stub generator: `/healthz` 200, `/readyz` 200, a valid `/parse` with both headers, and `FAULT_INJECT=1` giving HTTP 500 `{"error":"invalid_model_output"}` (`results/demo_api_stub.txt`). A 20 s Locust run against the stub (209 requests, 0 failures) proves only the toolchain, not service performance.

**Results [NOT RUN].** The Docker daemon was not available, so image size, the 50-request test and peak memory have not been measured. Procedure: the commands above plus `docker inspect -f '{{.State.OOMKilled}}'`.
Calculated: fp32 weights are about 70.4 M x 4 B = 0.28 GB, which is why they are fetched from object storage.

**Limitations.** Not built or run with a real model. The stub tests cannot detect a prompt/training mismatch or an out-of-memory failure.

---

## Task 4: Kubernetes deployment (22 marks)

**Objective.** Run the service reliably: replicas, probes, resource limits, autoscaling, rolling update, rollback, recovery.

**Architecture.** Namespace `app`: Deployment `command-parser` (2 replicas) -> Service (port 80 to 8000) -> Ingress (Traefik, bundled with k3s). HPA targets the Deployment.

**Key configuration [IMPLEMENTED in `k8s/app.yaml`, TESTED only as YAML fields].**
- `resources.requests` 250m CPU / 512Mi, `limits` 1 CPU / 1Gi. Requests drive scheduling and the HPA percentage; limits cap usage.
- `livenessProbe /healthz` restarts a hung process; `readinessProbe /readyz` keeps a pod out of the Service until the model is loaded. A large `failureThreshold` allows model download time.
- `strategy: RollingUpdate`, `maxUnavailable: 0`, `maxSurge: 1`: a new pod must be Ready before an old one is removed.
- HPA `minReplicas 1`, `maxReplicas 2`, CPU target 70%.

**HPA mathematics.** `desired = ceil( current_replicas * current_utilisation / target_utilisation )`, where utilisation is average CPU usage divided by the CPU *request*. Example: 2 pods at 140% of request: `ceil(2 * 140/70) = 4`, clipped to max 2. Note: the Deployment starts at 2 but the HPA minimum is 1, so the HPA may scale down to 1 when idle, after its stabilisation window (about 5 minutes).

**Procedures [METHOD].**
```bash
kubectl apply -f k8s/app.yaml
kubectl -n app get deploy,svc,ingress,hpa,pods -o wide
# load balancing: count X-Served-By values over many requests
# rolling update during load:
kubectl -n app set env deploy/command-parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2
kubectl -n app rollout status deploy/command-parser
kubectl -n app rollout undo deploy/command-parser
# recovery: kubectl -n app delete pod <name> while Locust runs
# cold start: time from `kubectl delete pod` until the replacement is Ready (3 runs)
```

**Testing.** [TESTED] `test_k8s_manifest_fields` asserts namespace, replicas, probes, limits and HPA fields. Nothing else was tested.

**Results [NOT RUN].** No cluster was available, so nothing was applied. Each experiment and its acceptance criterion:

| Experiment | Acceptance criterion | This project | Reported (reflection) |
|---|---|---|---|
| Load balancing, 2 Ready replicas | each replica at least 30% of successes | planned | 53.4% / 46.6% (unverified) |
| Rolling update v1 to v2 under load | at most 0.5% failed | planned | n/a |
| Rollback | `X-Model-Version` is v1 again | not run | n/a |
| Pod deletion under load | replica count restored; at most 2% failed | not run | my reflection reports 18.93 s, zero dropped (unverified) |
| Cold start, 3 runs, median | log shows model download | planned | 18.0 s (unverified) |
| HPA 1 to 2 and back | events show both directions | not run | calculated: 2 pods at 140% -> ceil(2*140/70)=4 -> clipped to 2; 20% -> 1 |

The manifest also contains a PodDisruptionBudget (`minAvailable: 1`), an HPA scale-down window of 60 s and a 30 s termination grace period (fields unit-tested).

**Limitations.** Manifest never applied. Single laptop means no node-failure tolerance; max 2 replicas limits scale-out; metrics-server may take minutes to report.

---

## Task 5: Subnetting and NACL (10 marks) [IMPLEMENTED and TESTED]

**Subnetting method.** Sort requirements largest first. For hosts `h`, choose the smallest prefix `p` with `2^(32-p) - 2 >= h`, i.e. `p = 32 - ceil(log2(h+2))`. Place blocks back to back starting at 10.20.0.0; each block's size is `2^(32-p)`.

| Subnet | h | p | Block | Network | Usable | Broadcast | Usable count |
|---|---:|---:|---:|---|---|---|---:|
| app | 1000 | /22 | 1024 | 10.20.0.0 | .0.1 - .3.254 | 10.20.3.255 | 1022 |
| public | 250 | /24 | 256 | 10.20.4.0 | .4.1 - .4.254 | 10.20.4.255 | 254 |
| data | 100 | /25 | 128 | 10.20.5.0 | .5.1 - .5.126 | 10.20.5.127 | 126 |
| management | 20 | /27 | 32 | 10.20.5.128 | .5.129 - .5.158 | 10.20.5.159 | 30 |

Worked check for `app`: log2(1002) = 9.97, ceil = 10, p = 22, block = 1024, usable = 1022 >= 1000. A /23 would give 510 (too few).

**NACL evaluation algorithm.** For a packet and direction: sort that direction's rules by number ascending; the first rule whose CIDR contains the address *and* (protocol is `all` or protocol matches and the port lies in `[port_from, port_to]`) decides; if none matches, deny. Inbound rules match the *source* address, outbound rules match the *destination*.

**Rule set** (`network/nacl.json`): inbound 100 deny all 198.51.100.0/24; 110 allow tcp 80; 120 allow tcp 443; 130 allow tcp 22 from 10.20.5.128/27; 140 allow tcp 1024-65535 from 10.20.0.0/22. Outbound 100 allow tcp 8000 to 10.20.0.0/22; 110 allow tcp 1024-65535 to 0.0.0.0/0.

**Why replies need rules (stateless).** A security group remembers a connection and lets the reply through automatically. A NACL does not: the reply is a brand-new packet checked against the rules. A client connecting to port 443 replies from port 443 to the client's ephemeral port, so the outbound side needs an allow for 1024-65535 (rule 110), and replies from the app subnet arrive inbound on the load balancer's ephemeral ports (rule 140).

**Why order matters.** Rule 100 must be lower than 110/120. If the allows came first, a packet from 198.51.100.7 to port 443 would match 120 and be allowed, defeating the block.

**Side effect found while testing.** Rule 110 also allows outbound TCP 8000 to *any* address, because 8000 is inside 1024-65535. The specification forces this ("replies going back to clients anywhere"); it could be narrowed only with a stateful firewall.

**Commands and results.** `make subnets`, `make nacl`, `make test`. [TESTED] `results/subnet_calc_local.txt` (table above reproduced), `results/nacl_eval_local.txt` (11 of 11 hand-written packets as expected), 9 of 9 unit tests. The instructor's `nacl_sim.py` with its six packets was **not** run (not available).

---

## Task 6: Reproducibility, CI/CD, security (10 marks)

**Objective.** Make the whole thing rebuildable and automatically checked.

**Pipeline design.** `.github/workflows/ci.yml` [IMPLEMENTED, never run]: jobs `lint` -> `unit-tests` -> `evaluate` -> `quality-gate` (the last two are manual `workflow_dispatch` jobs: they download a model from a Release and run `score.py`, then `score.py --min-validity 95`) plus `secret-scan` (gitleaks, full history). The stage order is unit-tested. **Not done:** any run on GitHub, and the deliberately failing run with the untrained model.

**Quality gate logic.** `score.py` exits non-zero if JSON validity < 95; the workflow fails at that step. Demonstration: run once with the untrained Pythia-70M (expected validity near 0%, so the run fails; the link to that run belongs in the report once it exists, **[NOT RUN]**), and once with the trained model (expected to pass only if validity >= 95).

**Reproducibility.** Pinned dependency versions, fixed seeds, a single config file for training, checksums for datasets and models, `make up` (cluster + build + deploy) and `make down` (delete cluster). `make up` is implemented (`scripts/deploy.sh`) but **not run** (no Docker/k3d on the machine used).

**Security.** Secrets only in Kubernetes Secrets or CI secrets; `.env` ignored by Git; weights excluded by `.gitignore`; gitleaks on every push; least privilege (**limitation:** one shared S3 identity is simplest but not minimal).

**Testing.** [TESTED] 32 tests, pyflakes clean, locally only (`results/pytest_local.txt`). The manual evaluate and quality-gate jobs are written but never run.

**AI use.** AI-assisted development and how its output was checked are disclosed in `AI_USE.md`.

---

## Task 7: Performance, cost and review (12 marks)

**Load test method [METHOD].** Locust, 4 users, 2 minutes, against the Ingress:
`locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/load`.
A request fails if it is not HTTP 200 within 30 s.

**Metrics.**
- Latency percentiles: p50 and p95 = the value below which 50% / 95% of sorted latencies fall.
- Throughput = completed requests / seconds. Error rate = failures / requests x 100.
- CPU and memory: `kubectl top pods` sampled every 10 s during the run; report the peak.
- Cold start: seconds from pod creation to Ready, three runs, median.

**Cost model.** Choose a rate card (the supplied `rate_card.json` has the hypothetical prices). Hourly cost = replicas x (cpu_limit x price_cpu + mem_GiB x price_mem). Requests per hour = throughput x 3600. Cost per 1,000 requests = hourly cost / requests per hour x 1000. State the assumption "billed at limits" explicitly; it is an assumption, not a measurement.

**SLO and error budget.** Example SLO: 99% of requests succeed and p95 latency below a stated bound. Error budget = (1 - SLO) x requests; with 254 requests the budget would be 2.54 failures. Compare measured failures against it.

**Results [NOT RUN for the service].** No load test of a real deployment exists. What does exist:

- *Calculated:* with the exercise prices (3.50 INR per vCPU-hour, 0.45 per GiB-hour, hypothetical) two 1 vCPU / 1 GiB replicas cost 7.90 INR/hour. Cost per 1,000 requests at a *hypothetical* throughput: 0.25 rps 8.78; 0.50 rps 4.39; 0.57 rps 3.85; 0.75 rps 2.93; 1.00 rps 2.19 (`results/cost_slo_worked_examples.txt`, via `make cost RPS=...`).
- *Illustrative SLO:* 99% target, N = 1000 gives a budget of 10 requests (7 failures = 70% used, 25 = 250%); N = 254 gives 2.54 (3 failures = 118%) (`make slo REQUESTS=... FAILED=...`).
- *Actual, but only the toolchain:* a 20 s Locust run against the stub service (209 requests, 0 failures, 11.0 req/s) in `results/stub_smoke_*`. Latency of the stub says nothing about the real service.
- *Reported, unverified:* 2,052 req/h and 3.95 INR per 1,000 in my reflection; 7.90 / 2052 x 1000 = 3.85, so 3.95 does not follow (`results/cost_arithmetic_check.txt`).

**Review table (6 rows).** One row per area (data, model, service, Kubernetes, performance, security/cost) with *measured evidence*, *limitation*, *improvement*. Every evidence cell needs a number with its evidence class; the filled table is in `report/report.pdf` (Task 7).

---

## What to say in the handwritten reflection (truthfully)
- Learned: sequence-level distillation, why replies need NACL rules, probes vs. limits, HPA formula, why weights live in object storage.
- Challenges: time, missing student_kit, no Docker/k3d/Ollama in the working environment, a wrong test expectation (A8) found by running tests.
- Honest status: all seven tasks are implemented in code and unit-tested where possible; Task 5 is also checked end to end; the labelling, training, Docker, cluster, CI and load-test runs have not been executed, so no measured results for them exist.
- Improvements: run the pipeline end to end, add the Release-based gate, constrained decoding, multi-node cluster.

---

## Reference results
Figures supplied as reference material (data cleaning, validation scores, container size, load test, cost) are kept exactly as supplied in [`REFERENCE_RESULTS.md`](REFERENCE_RESULTS.md).
They were not produced by this repository and are not independently verified: use them only to see what a complete run looks like. Source: [`PROVENANCE.md`](PROVENANCE.md).
Key points: cleaning kept 2,292 of 3,000; validation JSON validity 94% / 90% / 89% (teacher / v1 / v2), so v1 misses the 95% gate; load test 12.36% errors and p95 16,000 ms, missing both targets; cost about 2.93 per 1,000 attempted requests.
The reflection's reported cost of 3.95 per 1,000 requests is kept as written; 7.90 / 2,052 x 1,000 is approximately 3.85.
